from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import sqlite3
import threading


class Store:
    """Own database; transactions serialized in-process and with SQLite locks."""

    def __init__(self, path: str | Path, *, connection=None):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.lock = threading.RLock()
        self.db = connection or sqlite3.connect(self.path, timeout=3, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys=ON")
        if connection is None:
            self.db.execute("PRAGMA journal_mode=WAL")
            self.db.execute("PRAGMA synchronous=FULL")
        self.db.execute("PRAGMA busy_timeout=3000")
        exists = self.db.execute("SELECT 1 FROM sqlite_master WHERE name='schema_version'").fetchone()
        if not exists:
            sql = (Path(__file__).parent / "migrations/001_initial.sql").read_text()
            try:
                self.db.executescript("BEGIN IMMEDIATE;\n" + sql + "\nCOMMIT;")
            except Exception:
                self.db.rollback()
                raise
        if [r[0] for r in self.db.execute("SELECT version FROM schema_version")] != [1]:
            raise RuntimeError("Versión de esquema no compatible")
        self.path.chmod(0o600)

    @contextmanager
    def transaction(self):
        with self.lock:
            self.db.execute("BEGIN IMMEDIATE")
            try:
                yield self.db
                self.db.commit()
            except BaseException:
                self.db.rollback()
                raise

    def recover_interrupted_jobs(self):
        """Called once at gateway startup; never re-execute old inference."""
        with self.transaction() as db:
            db.execute("UPDATE jobs SET status='failed',payload='{}',result=NULL,error='process_restarted' WHERE status IN ('pending','running')")

    def close(self):
        with self.lock:
            self.db.close()


def invalidate(db, owner, books):
    for book in set(books) - {None}:
        db.execute("UPDATE summaries SET stale=1 WHERE owner=? AND book=?", (owner, book))


def reindex(db, ref, version):
    db.execute("DELETE FROM note_chunks WHERE ref=?", (ref,))
    db.execute("INSERT INTO index_jobs(ref,version) VALUES(?,?) ON CONFLICT(ref) DO UPDATE SET version=excluded.version", (ref, version))
