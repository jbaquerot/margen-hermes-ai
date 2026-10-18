import sqlite3
import subprocess
import pytest
from margen.backup import snapshot,restore,transfer


def test_snapshot_restore_clears_actions_and_honors_later_deletion(h,tmp_path):
    h.activate()
    ref=h.send('Original conservado').refs[0]
    archive=tmp_path/'current.tar'
    snapshot(h.store.path,archive)
    h.send('/eliminar '+ref)
    h.send('/confirmar')
    path=restore(archive,tmp_path/'quarantine',current_database=h.store.path)
    db=sqlite3.connect(path)
    assert db.execute('SELECT count(*) FROM notes').fetchone()[0]==0
    for table in ('jobs','outbox','pending_interactions'):
        assert db.execute('SELECT count(*) FROM '+table).fetchone()[0]==0
    db.close()
    assert (tmp_path/'quarantine/REVIEW_REQUIRED.txt').exists()
    with pytest.raises(FileExistsError):
        restore(archive,tmp_path/'quarantine')


def test_failed_snapshot_retains_previous(h,tmp_path):
    target=tmp_path/'current.tar'
    snapshot(h.store.path,target)
    previous=target.read_bytes()
    with pytest.raises(FileNotFoundError):
        snapshot(tmp_path/'missing.db',target)
    assert target.read_bytes()==previous


def test_unmounted_destination_never_creates_backup(h,tmp_path,monkeypatch):
    def absent(*args,**kwargs):
        raise subprocess.CalledProcessError(1,args[0])
    monkeypatch.setattr(subprocess,'run',absent)
    archive=tmp_path/'current.tar'
    snapshot(h.store.path,archive)
    mount=tmp_path/'mount'
    mount.mkdir()
    with pytest.raises(subprocess.CalledProcessError):
        transfer(archive,mount,'/dev/expected')
    assert list(mount.iterdir())==[]


def test_changed_archive_rejected(h,tmp_path):
    archive=tmp_path/'current.tar'
    snapshot(h.store.path,archive)
    import tarfile
    import io
    with tarfile.open(archive,'a') as tar:
        item=tarfile.TarInfo('../escape')
        item.size=1
        tar.addfile(item,io.BytesIO(b'x'))
    with pytest.raises(ValueError):
        restore(archive,tmp_path/'bad')
    assert not (tmp_path/'escape').exists()


def test_simulated_mounted_transfer_replaces_only_after_verification(h,tmp_path,monkeypatch):
    from margen import backup
    import os
    archive=tmp_path/'current.tar'
    snapshot(h.store.path,archive)
    mount=tmp_path/'mounted'
    mount.mkdir()
    # Only the OS mount probe is simulated; real file I/O, hashing and replace run.
    monkeypatch.setattr(backup,'open_verified_mount',lambda *args:os.open(mount,os.O_RDONLY|os.O_DIRECTORY))
    transfer(archive,mount,'synthetic-device')
    previous=(mount/'backups/margen-current.tar').read_bytes()
    assert previous==archive.read_bytes()
    monkeypatch.setattr(backup,'digest',lambda *args:'invalid-sha256')
    with pytest.raises(ValueError):
        transfer(archive,mount,'synthetic-device')
    assert (mount/'backups/margen-current.tar').read_bytes()==previous
    assert [p.name for p in (mount/'backups').iterdir()]==['margen-current.tar']
