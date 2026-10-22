import importlib.util
import json
from pathlib import Path
import pytest
from margen import books, notes, summaries

spec = importlib.util.spec_from_file_location('cleanup_test_books', Path('scripts/cleanup-test-books.py'))
cleanup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cleanup)


def populate(h):
    refs = []
    for title, author in cleanup.FIXTURES:
        h.activate(title, author)
        refs.append(h.send('PRIVATE_TEST_NOTE').refs[0])
        with h.store.transaction() as db:
            book = books.active(db, '1')
            summaries.save(db, '1', {'book':book, 'notes':notes.for_book(db,'1',book['id']),
                                    'mode':'brief'}, 'PRIVATE_TEST_SUMMARY')
    return refs


def delivered(h):
    # The domain harness has no Telegram transport. Model acknowledged replies explicitly.
    with h.store.transaction() as db:
        db.execute('UPDATE outbox SET delivered=1,payload=NULL')


def test_preview_lists_only_exact_fixtures_without_note_text(h):
    populate(h)
    h.activate('Mi libro real', 'Autora real')
    h.send('PRIVATE_REAL_NOTE')
    details, token = cleanup.plan(h.store.db)
    output = json.dumps(cleanup.public_plan(details, token))
    assert len(details) == 3
    assert all(len(item['notes']) == 1 and len(item['summaries']) == 1 for item in details)
    assert 'PRIVATE_' not in output and 'Mi libro real' not in output
    assert h.store.db.execute('SELECT COUNT(*) FROM books').fetchone()[0] == 4


def test_cleanup_preserves_real_book_active_and_data_and_records_deleted_refs(h, tmp_path):
    refs = populate(h)
    h.activate('Mi libro real', 'Autora real')
    real_ref = h.send('PRIVATE_REAL_NOTE').refs[0]
    delivered(h)
    _, token = cleanup.plan(h.store.db)
    archive = tmp_path/'current.tar'
    assert cleanup.cleanup(h.store.db, h.store.path, archive, token) == 3
    assert archive.exists()
    assert h.store.db.execute('SELECT COUNT(*) FROM books').fetchone()[0] == 1
    assert books.active(h.store.db, '1')['title'] == 'Mi libro real'
    assert notes.get(h.store.db, '1', real_ref)['text'] == 'PRIVATE_REAL_NOTE'
    assert h.store.db.execute('SELECT COUNT(*) FROM summaries').fetchone()[0] == 0
    assert h.store.db.execute('SELECT COUNT(*) FROM note_versions').fetchone()[0] == 1
    assert h.store.db.execute('SELECT COUNT(*) FROM notes_fts').fetchone()[0] == 1
    assert {r[0] for r in h.store.db.execute('SELECT ref FROM deletion_ledger')} == set(refs)


def test_changed_data_invalidates_reviewed_confirmation(h, tmp_path):
    refs = populate(h)
    _, token = cleanup.plan(h.store.db)
    h.send('/editar ' + refs[0] + ' nota cambiada después de revisar')
    archive = tmp_path/'current.tar'
    with pytest.raises(RuntimeError, match='vista previa'):
        cleanup.cleanup(h.store.db, h.store.path, archive, token)
    assert not archive.exists()
    assert h.store.db.execute('SELECT COUNT(*) FROM books').fetchone()[0] == 3


def test_failed_backup_keeps_books_and_notes(h, tmp_path, monkeypatch):
    populate(h)
    delivered(h)
    _, token = cleanup.plan(h.store.db)
    def fail(*args):
        raise OSError('Disco no escribible')
    monkeypatch.setattr(cleanup, 'snapshot', fail)
    with pytest.raises(OSError):
        cleanup.cleanup(h.store.db, h.store.path, tmp_path/'current.tar', token)
    assert h.store.db.execute('SELECT COUNT(*) FROM books').fetchone()[0] == 3
    assert h.store.db.execute('SELECT COUNT(*) FROM notes').fetchone()[0] == 3


def test_pending_work_prevents_cleanup(h, tmp_path):
    populate(h)
    h.send('/resumen')
    _, token = cleanup.plan(h.store.db)
    with pytest.raises(RuntimeError, match='trabajos sin terminar'):
        cleanup.cleanup(h.store.db, h.store.path, tmp_path/'current.tar', token)
    assert h.store.db.execute('SELECT COUNT(*) FROM books').fetchone()[0] == 3


def test_removing_active_test_book_leaves_no_active_book(h, tmp_path):
    populate(h)
    delivered(h)
    _, token = cleanup.plan(h.store.db)
    cleanup.cleanup(h.store.db, h.store.path, tmp_path/'current.tar', token)
    assert books.active(h.store.db, '1') is None
    assert h.store.db.execute('SELECT COUNT(*) FROM books').fetchone()[0] == 0


def test_unacknowledged_response_prevents_cleanup(h, tmp_path):
    populate(h)
    _, token = cleanup.plan(h.store.db)
    with pytest.raises(RuntimeError, match='entregas pendientes'):
        cleanup.cleanup(h.store.db, h.store.path, tmp_path/'current.tar', token)
    assert h.store.db.execute('SELECT COUNT(*) FROM notes').fetchone()[0] == 3
