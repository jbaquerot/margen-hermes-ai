import json


def pending(db, owner):
    row = db.execute("SELECT kind,payload FROM pending_interactions WHERE owner=?", (owner,)).fetchone()
    return (row[0], json.loads(row[1])) if row else None


def set_pending(db, owner, kind, payload):
    db.execute("INSERT INTO pending_interactions VALUES(?,?,?) ON CONFLICT(owner) DO UPDATE SET kind=excluded.kind,payload=excluded.payload", (owner, kind, json.dumps(payload)))


def clear(db, owner):
    db.execute("DELETE FROM pending_interactions WHERE owner=?", (owner,))
