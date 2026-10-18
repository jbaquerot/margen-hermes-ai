"""Consistent snapshots and quarantine restore; never starts a gateway."""
from pathlib import Path
import hashlib
import io
import json
import os
import sqlite3
import subprocess
import tarfile
import tempfile
from .domain import now


def digest(path):
    h = hashlib.sha256()
    with open(path, 'rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def check(db):
    if db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
        raise ValueError('Integridad SQLite inválida')
    if db.execute('PRAGMA foreign_key_check').fetchone():
        raise ValueError('Relaciones SQLite inválidas')
    if [r[0] for r in db.execute('SELECT version FROM schema_version')] != [1]:
        raise ValueError('Esquema no compatible')


def snapshot(source, destination):
    source, destination = Path(source).resolve(strict=True), Path(destination)
    if destination.resolve() == source:
        raise ValueError('La copia no puede reemplazar la base')
    destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with tempfile.TemporaryDirectory(dir=destination.parent, prefix='.margen-snapshot-') as temp:
        root = Path(temp)
        dbpath = root/'data.db'
        live = sqlite3.connect(source.as_uri()+'?mode=ro',uri=True)
        copy = sqlite3.connect(dbpath)
        try:
            live.backup(copy)
            check(copy)
        finally:
            live.close()
            copy.close()
        manifest = {'schema':1,'created_utc':now(),'sha256':digest(dbpath),
                    'restore':'quarantine-only; review later deletions before activation'}
        archive = root/'current.tar'
        with tarfile.open(archive,'w') as tar:
            tar.add(dbpath,arcname='data.db')
            payload = json.dumps(manifest,ensure_ascii=False).encode()
            info = tarfile.TarInfo('manifest.json')
            info.size, info.mode = len(payload), 0o600
            tar.addfile(info,io.BytesIO(payload))
        archive.chmod(0o600)
        with archive.open('rb') as stream:
            os.fsync(stream.fileno())
        os.replace(archive,destination)
    return manifest


def open_verified_mount(mount, expected_source):
    actual = subprocess.run(['findmnt','-n','-M',str(mount),'-o','SOURCE'],
                            check=True,capture_output=True,text=True).stdout.strip()
    if os.path.realpath(actual) != os.path.realpath(expected_source):
        raise ValueError('El volumen montado no coincide con el esperado')
    fd = os.open(mount,os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        if os.fstat(fd).st_dev != os.stat(os.path.realpath(expected_source)).st_rdev:
            raise ValueError('El volumen cambió durante la comprobación')
        if os.fstat(fd).st_dev == mount.parent.stat().st_dev:
            raise ValueError('El destino no es un volumen independiente')
        return fd
    except BaseException:
        os.close(fd)
        raise


def transfer(archive, mount, expected_source, *, subdirectory='backups', name='margen-current.tar'):
    """Hold directory descriptors so an unplug cannot redirect writes to rootfs."""
    if any('/' in value or value in ('','.','..') for value in (subdirectory,name)):
        raise ValueError('Nombre de destino no válido')
    mount = Path(mount).resolve(strict=True)
    fd = open_verified_mount(mount, expected_source)
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    directory = None
    tmpname = '.margen-transfer-'+os.urandom(8).hex()
    try:
        try:
            os.mkdir(subdirectory,mode=0o700,dir_fd=fd)
        except FileExistsError:
            pass
        directory = os.open(subdirectory,flags,dir_fd=fd)
        if os.fstat(directory).st_dev != os.fstat(fd).st_dev:
            raise ValueError('Subdirectorio en otro volumen')
        target = os.open(tmpname,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=directory)
        expected = digest(archive)
        h = hashlib.sha256()
        with os.fdopen(target,'wb') as out, open(archive,'rb') as stream:
            for block in iter(lambda:stream.read(1024*1024),b''):
                out.write(block)
                h.update(block)
            out.flush()
            os.fsync(out.fileno())
        if h.hexdigest() != expected:
            raise ValueError('La instantánea cambió durante la transferencia')
        # Read the written bytes back before replacing the last verified archive.
        readback = os.open(tmpname,os.O_RDONLY|os.O_NOFOLLOW,dir_fd=directory)
        h = hashlib.sha256()
        with os.fdopen(readback,'rb') as stream:
            for block in iter(lambda:stream.read(1024*1024),b''):
                h.update(block)
        if h.hexdigest() != expected:
            raise ValueError('Verificación del SSD fallida')
        os.replace(tmpname,name,src_dir_fd=directory,dst_dir_fd=directory)
    finally:
        if directory is not None:
            try:
                os.unlink(tmpname,dir_fd=directory)
            except FileNotFoundError:
                pass
            os.close(directory)
        os.close(fd)


def restore(archive, quarantine, *, current_database=None):
    root = Path(quarantine)
    root.mkdir(mode=0o700)  # Exclusive new directory; never overwrite an active database.
    path = root/'data.db'
    try:
        with tarfile.open(archive,'r') as tar:
            members = tar.getmembers()
            if sorted(m.name for m in members) != ['data.db','manifest.json'] or not all(m.isfile() for m in members):
                raise ValueError('Archivo de backup no compatible')
            manifest = json.loads(tar.extractfile('manifest.json').read(65537))
            if manifest['schema'] != 1:
                raise ValueError('Manifiesto no compatible')
            with path.open('xb') as out:
                stream = tar.extractfile('data.db')
                for block in iter(lambda:stream.read(1024*1024),b''):
                    out.write(block)
        if digest(path) != manifest['sha256']:
            raise ValueError('Hash de backup incorrecto')
        db = sqlite3.connect(path)
        try:
            db.execute('PRAGMA foreign_keys=ON')
            check(db)
            # A newer live deletion ledger can remove resurrected notes by stable ref.
            if current_database:
                livepath = Path(current_database).resolve(strict=True)
                live = sqlite3.connect(livepath.as_uri()+'?mode=ro',uri=True)
                try:
                    deleted = live.execute('SELECT ref FROM deletion_ledger').fetchall()
                finally:
                    live.close()
                db.executemany('DELETE FROM notes WHERE ref=?',deleted)
            for table in ('pending_interactions','outbox','jobs','search_sessions'):
                db.execute('DELETE FROM '+table)
            db.execute('UPDATE summaries SET stale=1')
            db.commit()
            check(db)
        finally:
            db.close()
        path.chmod(0o600)
        (root/'REVIEW_REQUIRED.txt').write_text(
            'CUARENTENA: no activar automáticamente. Revisar eliminaciones posteriores, '
            'credenciales y autorización. No se restauran acciones ni entregas pendientes.\n')
        return path
    except BaseException:
        path.unlink(missing_ok=True)
        raise
