#!/usr/bin/env python3
"""Preview/apply cleanup of the three exact synthetic books used in acceptance tests."""
if __name__ == '__main__':
    import hermes_bootstrap  # Activate the container's admitted dependency generation first.

import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
from margen.backup import check, snapshot
from margen import notes

FIXTURES = (
    ('Libro de prueba', 'Autor de prueba'),
    ('Segundo libro de prueba', 'Otra autora'),
    ('Prueba de matices', 'Autor ficticio'),
)
DEFAULT_DATABASE = '/opt/data/profiles/margen/plugin-data/margen/data.db'


def rows(db, sql, values=()):
    return [dict(row) for row in db.execute(sql, values)]


def plan(db):
    selected = [row for title, author in FIXTURES for row in rows(
        db, 'SELECT * FROM books WHERE title=? AND author=? ORDER BY id', (title, author))]
    if len({row['owner'] for row in selected}) > 1:
        raise RuntimeError('Los libros coinciden con varios propietarios; limpieza cancelada.')
    details = []
    for book in selected:
        content = rows(db, 'SELECT * FROM notes WHERE book=? ORDER BY seq', (book['id'],))
        summaries = rows(db, 'SELECT * FROM summaries WHERE book=? ORDER BY ref', (book['id'],))
        if any(row['owner'] != book['owner'] for row in content + summaries):
            raise RuntimeError('Propietarios inconsistentes; limpieza cancelada.')
        versions = [v for note in content for v in rows(
            db, 'SELECT * FROM note_versions WHERE ref=? ORDER BY version', (note['ref'],))]
        details.append({'book': book, 'notes': content, 'versions': versions, 'summaries': summaries})
    active = [r for owner in {b['owner'] for b in selected} for r in rows(
        db, 'SELECT * FROM reading_state WHERE owner=?', (owner,))]
    fingerprint = hashlib.sha256(json.dumps([details, active], sort_keys=True,
                                          ensure_ascii=False).encode()).hexdigest()[:32]
    return details, fingerprint


def public_plan(details, fingerprint):
    return {'modo': 'solo vista previa', 'confirmacion': fingerprint,
            'libros': [{'titulo': item['book']['title'], 'autor': item['book']['author'],
                        'notas': len(item['notes']), 'versiones': len(item['versions']),
                        'resumenes': len(item['summaries'])} for item in details],
            'alcance': 'Libros indicados, sus notas/versiones y sus resúmenes. Otros libros se conservan.'}


def references_target(value, targets):
    if isinstance(value, dict):
        return any(references_target(v, targets) for v in value.values())
    if isinstance(value, list):
        return any(references_target(v, targets) for v in value)
    return isinstance(value, str) and value in targets


def cleanup(db, database, archive, expected):
    db.execute('BEGIN IMMEDIATE')
    try:
        details, fingerprint = plan(db)
        if not details or expected != fingerprint:
            raise RuntimeError('La vista previa ya no coincide. Volver a comprobar antes de borrar.')
        owner = details[0]['book']['owner']
        if db.execute('SELECT 1 FROM pending_interactions WHERE owner=?', (owner,)).fetchone():
            raise RuntimeError('Resolver o cancelar la interacción pendiente antes de limpiar.')
        if db.execute("SELECT 1 FROM jobs WHERE owner=? AND status IN ('pending','running')", (owner,)).fetchone():
            raise RuntimeError('Hay trabajos sin terminar; no se borra nada.')
        if db.execute('SELECT 1 FROM outbox WHERE owner=? AND delivered=0', (owner,)).fetchone():
            raise RuntimeError('Hay entregas pendientes; no se borra nada.')
        # No writes precede this backup. BEGIN IMMEDIATE prevents another writer from
        # changing the reviewed data while the read-only backup connection copies it.
        snapshot(database, archive)
        targets = {item['book']['id'] for item in details}
        targets.update(n['ref'] for item in details for n in item['notes'])
        targets.update(s['ref'] for item in details for s in item['summaries'])
        for job in rows(db, 'SELECT * FROM jobs WHERE owner=?', (owner,)):
            if any(references_target(json.loads(job[field]), targets)
                   for field in ('payload', 'result') if job[field]):
                db.execute('DELETE FROM jobs WHERE id=?', (job['id'],))
        for item in details:
            book = item['book']
            for note in item['notes']:
                notes.delete(db, owner, note['ref'])
            db.execute('DELETE FROM summaries WHERE owner=? AND book=?', (owner, book['id']))
            db.execute('UPDATE reading_state SET book=NULL WHERE owner=? AND book=?', (owner, book['id']))
            db.execute('DELETE FROM books WHERE owner=? AND id=?', (owner, book['id']))
        # Search pagination is transient; remove the old page rather than retain deleted refs.
        db.execute('DELETE FROM search_sessions WHERE owner=?', (owner,))
        check(db)
        db.commit()
        return len(details)
    except BaseException:
        db.rollback()
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', default=DEFAULT_DATABASE)
    parser.add_argument('--apply', metavar='CONFIRMACION', help='Token de la vista previa revisada')
    args = parser.parse_args()
    database = Path(args.database).resolve(strict=True)
    if args.apply:
        result = subprocess.run(['/command/s6-svstat', '-o', 'up', '/run/service/gateway-default'],
                                check=True, capture_output=True, text=True)
        if result.stdout.strip() != 'false':
            parser.exit(1, 'Detener primero el gateway compartido; el contenedor permanece abierto.\n')
    mode = 'rw' if args.apply else 'ro'
    db = sqlite3.connect(database.as_uri() + '?mode=' + mode, uri=True, timeout=3)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    try:
        check(db)
        if args.apply:
            count = cleanup(db, database, database.parent/'current.tar', args.apply)
            print(f'Libros ficticios eliminados: {count}. Copia SQLite previa verificada.')
            print('Los demás libros se conservan. Las copias y mensajes anteriores no se borran.')
        else:
            db.execute('BEGIN')
            details, fingerprint = plan(db)
            print(json.dumps(public_plan(details, fingerprint), ensure_ascii=False, indent=2))
            db.rollback()
    finally:
        db.close()


if __name__ == '__main__':
    main()
