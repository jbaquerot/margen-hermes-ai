"""Receipt helpers: do not retain copies of note content after delivery."""
from dataclasses import asdict
import json
from .domain import Response, now


def previous(db, event):
    row = db.execute("SELECT p.refs,o.payload FROM processed_events p JOIN outbox o ON o.event_key=p.key WHERE p.key=? AND p.owner=?", (event.key, event.user)).fetchone()
    if row:
        if row['payload']:
            result = Response(**json.loads(row['payload']))
            result.receipt = event.key
            return result
        return Response("Mensaje procesado previamente. " + " ".join(json.loads(row['refs'])), receipt=event.key)
    return None


def record(db, event, result):
    result.receipt = event.key
    db.execute("INSERT INTO processed_events VALUES(?,?,?,?)", (event.key, event.user, json.dumps(result.refs), now()))
    db.execute("INSERT INTO outbox(event_key,owner,payload) VALUES(?,?,?)", (event.key, event.user, json.dumps(asdict(result))))
