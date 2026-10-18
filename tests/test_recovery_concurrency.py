from concurrent.futures import ThreadPoolExecutor
from margen.domain import Event
from margen.storage import Store


def test_concurrent_original_delivery_commits_once(h):
    h.activate()
    e=Event('2','1','1','same-original','Nota concurrente')
    with ThreadPoolExecutor(max_workers=8) as pool:
        results=list(pool.map(lambda _:h.app.handle(e),range(20)))
    assert len({tuple(r.refs) for r in results})==1
    assert h.store.db.execute('SELECT count(*) FROM notes').fetchone()[0]==1
    assert h.store.db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'


def test_recovery_never_reexecutes_inference_and_keeps_pending_interaction(h):
    h.activate()
    h.send('Original')
    job=h.send('/resumen').job
    h.send('/eliminar '+h.store.db.execute('SELECT ref FROM notes').fetchone()[0])
    path=h.store.path
    h.store.close()
    h.store=Store(path)
    h.store.recover_interrupted_jobs()
    row=h.store.db.execute('SELECT status,payload FROM jobs WHERE id=?',(job,)).fetchone()
    assert row['status']=='failed' and row['payload']=='{}'
    assert h.store.db.execute('SELECT count(*) FROM pending_interactions').fetchone()[0]==1
    assert h.store.db.execute('SELECT count(*) FROM notes').fetchone()[0]==1
