import json
import math


def ensure_index(store, embedder, owner):
    with store.lock:
        # Rebuild entries when the configured model revision changes.
        rows = store.db.execute("SELECT n.* FROM notes n WHERE owner=? AND (EXISTS(SELECT 1 FROM index_jobs j WHERE j.ref=n.ref) OR NOT EXISTS(SELECT 1 FROM note_chunks c JOIN note_embeddings e ON e.chunk=c.id WHERE c.ref=n.ref AND c.version=n.version AND e.revision=?)) ORDER BY n.seq", (owner, embedder.revision)).fetchall()
    for row in rows:
        pieces = embedder.chunks(row['text'])
        vectors = embedder.encode(pieces)
        if len(vectors) != len(pieces) or not pieces:
            raise RuntimeError("Índice incompleto")
        for v in vectors:
            if len(v) != 384 or not all(math.isfinite(x) for x in v):
                raise RuntimeError("Embedding inválido")
        with store.transaction() as db:
            current = db.execute("SELECT version FROM notes WHERE ref=? AND owner=?", (row['ref'],owner)).fetchone()
            if not current or current[0] != row['version']:
                continue
            db.execute("DELETE FROM note_chunks WHERE ref=?", (row['ref'],))
            for i, vector in enumerate(vectors):
                cur = db.execute("INSERT INTO note_chunks(ref,version,position) VALUES(?,?,?)", (row['ref'],row['version'],i))
                db.execute("INSERT INTO note_embeddings VALUES(?,?,?)", (cur.lastrowid, embedder.revision,json.dumps(vector)))
            db.execute("DELETE FROM index_jobs WHERE ref=? AND version=?", (row['ref'],row['version']))
