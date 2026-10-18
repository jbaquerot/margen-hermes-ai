from .domain import UserError, normalized, now, reference


def register(db, owner, title, author):
    key = (owner, normalized(title), normalized(author))
    old = db.execute("SELECT * FROM books WHERE owner=? AND title_key=? AND author_key=?", key).fetchone()
    if old:
        return old, False
    ident = reference("B")
    db.execute("INSERT INTO books VALUES(?,?,?,?,?,?,?)", (ident, owner, title, author, key[1], key[2], now()))
    return get(db, owner, ident), True


def get(db, owner, ident):
    row = db.execute("SELECT * FROM books WHERE id=? AND owner=?", (ident, owner)).fetchone()
    if not row:
        raise UserError("El libro no está registrado. Usa /libro Título | Autor.")
    return row


def all_books(db, owner):
    return db.execute("SELECT * FROM books WHERE owner=? ORDER BY created_at,id", (owner,)).fetchall()


def matching(db, owner, title):
    return db.execute("SELECT * FROM books WHERE owner=? AND title_key=? ORDER BY created_at,id", (owner, normalized(title))).fetchall()


def active(db, owner):
    row = db.execute("SELECT book FROM reading_state WHERE owner=?", (owner,)).fetchone()
    return get(db, owner, row[0]) if row and row[0] else None


def activate(db, owner, book):
    get(db, owner, book)
    db.execute("INSERT INTO reading_state VALUES(?,?) ON CONFLICT(owner) DO UPDATE SET book=excluded.book", (owner, book))


def label(book):
    return f"{book['title']} — {book['author']}"
