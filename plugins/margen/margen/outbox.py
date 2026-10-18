def acknowledge(store, receipt):
    if receipt:
        with store.transaction() as db:
            db.execute("UPDATE outbox SET delivered=1,payload=NULL WHERE event_key=?", (receipt,))


def progress(store, receipt, count):
    if receipt:
        with store.transaction() as db:
            db.execute("UPDATE outbox SET sent_parts=? WHERE event_key=?", (count, receipt))


def sent_parts(store, receipt):
    with store.lock:
        row = store.db.execute("SELECT sent_parts FROM outbox WHERE event_key=?", (receipt,)).fetchone()
        return row[0] if row else 0
