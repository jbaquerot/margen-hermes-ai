from . import books
from .domain import UserError, now, reference
from .storage import invalidate, reindex


def get(db, owner, ref):
    row = db.execute("SELECT * FROM notes WHERE owner=? AND ref=?", (owner, ref)).fetchone()
    if not row:
        raise UserError("La nota no existe o ha sido eliminada.")
    return row


def for_book(db, owner, book):
    return db.execute("SELECT * FROM notes WHERE owner=? AND book IS ? ORDER BY created_at,seq", (owner, book)).fetchall()


def describe(db, owner, row):
    book = books.label(books.get(db, owner, row['book'])) if row['book'] else "Sin libro asignado"
    return f"{row['ref']} · {book}\n{row['text']}"


def create(db, owner, text):
    if not text.strip():
        raise UserError("La nota no puede estar vacía.")
    book = books.active(db, owner)
    ref, date = reference("N"), now()
    db.execute("INSERT INTO notes(ref,owner,book,text,created_at) VALUES(?,?,?,?,?)", (ref, owner, book['id'] if book else None, text, date))
    db.execute("INSERT INTO note_versions VALUES(?,?,?,?)", (ref, 1, text, date))
    reindex(db, ref, 1)
    invalidate(db, owner, [book['id'] if book else None])
    return get(db, owner, ref)


def edit(db, owner, ref, text):
    row = get(db, owner, ref)
    if not text.strip():
        raise UserError("El texto de reemplazo no puede estar vacío.")
    version = row['version'] + 1
    db.execute("INSERT INTO note_versions VALUES(?,?,?,?)", (ref, version, text, now()))
    db.execute("UPDATE notes SET text=?,version=? WHERE ref=?", (text, version, ref))
    reindex(db, ref, version)
    invalidate(db, owner, [row['book']])
    return get(db, owner, ref)


def move(db, owner, ref, book):
    row = get(db, owner, ref)
    books.get(db, owner, book)
    db.execute("UPDATE notes SET book=? WHERE ref=?", (book, ref))
    invalidate(db, owner, [row['book'], book])
    return get(db, owner, ref)


def delete(db, owner, ref):
    row = get(db, owner, ref)
    invalidate(db, owner, [row['book']])
    db.execute("INSERT INTO deletion_ledger VALUES(?,?)", (ref, now()))
    db.execute("DELETE FROM notes WHERE ref=?", (ref,))
    # Purge potentially sensitive pending output from this owner, including views.
    # Preserved summaries are explicitly exempted by the approved specification.
    db.execute("UPDATE outbox SET payload=NULL,delivered=1 WHERE owner=?", (owner,))
    import json
    for job in db.execute("SELECT * FROM jobs WHERE owner=?", (owner,)).fetchall():
        payload = json.loads(job['payload'])
        result = json.loads(job['result']) if job['result'] else {}
        affected = ref in [n['ref'] for n in payload.get('notes', [])] or ref in result.get('refs', [])
        if affected or job['kind'] == 'buscar':
            db.execute("UPDATE jobs SET status='failed',payload='{}',result=NULL,error='source_deleted' WHERE id=?", (job['id'],))
