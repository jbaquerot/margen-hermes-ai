import pytest
from margen.search import search,page
from margen.indexing import ensure_index


class Encoder:
    revision='synthetic-test-only'
    def chunks(self,text):
        return [text]
    def encode(self,texts,**kwargs):
        # Deliberately simple deterministic test double; no quality claim for E5.
        return [[float('azul' in text),float('azul' not in text)]+[0.0]*382 for text in texts]


def test_all_books_pending_pagination_and_current_version(h):
    pending=h.send('azul pendiente').refs[0]
    h.activate()
    refs=[h.send('azul idea '+str(i)).refs[0] for i in range(7)]
    h.activate('Otro','Autor')
    other=h.send('azul otro libro').refs[0]
    h.send('rojo irrelevante')
    first=search(h.store,Encoder(),'1','azul')
    with h.store.transaction() as db:
        second=page(db,'1')
        third=page(db,'1')
    assert len(first.refs)==5
    assert set(first.refs).isdisjoint(second.refs)
    assert set(first.refs+second.refs)==set([pending,other]+refs)
    assert not third.refs
    h.send('/editar '+refs[0]+' rojo cambiado')
    updated=search(h.store,Encoder(),'1','azul')
    with h.store.transaction() as db:
        updated.refs.extend(page(db,'1').refs)
    assert refs[0] not in updated.refs
    h.send('/eliminar '+other)
    h.send('/confirmar')
    assert h.store.db.execute('SELECT count(*) FROM note_chunks WHERE ref=?',(other,)).fetchone()[0]==0


def test_encoder_failure_leaves_index_pending_and_no_false_result(h):
    h.send('Texto')
    class Failed(Encoder):
        def encode(self,*a,**k):
            raise OSError('missing local model')
    with pytest.raises(OSError):
        search(h.store,Failed(),'1','texto')
    assert h.store.db.execute('SELECT count(*) FROM index_jobs').fetchone()[0]==1
    assert h.store.db.execute('SELECT count(*) FROM search_sessions').fetchone()[0]==0


def test_stale_vectors_never_published(h):
    ref=h.send('azul inicial').refs[0]
    class Changed(Encoder):
        def encode(self,*a,**k):
            h.send('/editar '+ref+' rojo cambiado')
            return super().encode(*a,**k)
    ensure_index(h.store,Changed(),'1')
    assert h.store.db.execute('SELECT count(*) FROM note_chunks').fetchone()[0]==0
    assert h.store.db.execute('SELECT count(*) FROM index_jobs').fetchone()[0]==1
