import json
import sqlite3
import pytest
from margen.commands import parse
from margen.domain import Event, UserError
from margen.storage import Store
from margen.application import Application


@pytest.mark.parametrize('command', ['/nota','/libro Solo','/libro a|b|c','/resumen otro libro','/buscar','/ver inexistente','/confirmar extra','/inexistente'])
def test_invalid_commands_never_capture(h, command):
    h.activate()
    result = h.send(command)
    assert 'Uso:' in result.text or 'desconocido' in result.text
    assert h.store.db.execute('SELECT COUNT(*) FROM notes').fetchone()[0] == 0


def test_register_does_not_activate_and_normalizes_duplicates(h):
    h.send('/libro   ÁRBOL  | AUTOR')
    h.send('/libro árbol | autor')
    assert h.store.db.execute('SELECT COUNT(*) FROM books').fetchone()[0] == 1
    assert 'Sin libro activo' in h.send('/libros').text


def test_capture_receipts_are_idempotent_across_active_change(h):
    h.activate()
    first = h.send('  texto original\ncon matices ',message='100')
    h.activate('Libro B')
    duplicate = h.send('  texto original\ncon matices ',message='100')
    assert first.text == duplicate.text and first.refs == duplicate.refs
    assert 'Libro A' in duplicate.text
    h.send('  texto original\ncon matices ')
    rows = h.store.db.execute('SELECT * FROM notes ORDER BY seq').fetchall()
    assert len(rows) == 2 and rows[0]['book'] != rows[1]['book']
    assert rows[0]['text'] == '  texto original\ncon matices '


def test_one_pending_assignment_activates_book(h):
    ref = h.send('primera idea').refs[0]
    assert 'pendiente' in h.send('/ver '+ref).text.lower() or 'Sin libro' in h.send('/ver '+ref).text
    h.send('/libro Nuevo | Autora')
    result = h.send('Nuevo')
    assert ref in result.text and 'activo' in result.text
    assert 'Nuevo' in h.send('/libros').text


def test_batch_assignment_frozen_while_new_note_uses_active(h):
    a = h.send('a').refs[0]
    b = h.send('/nota b').refs[0]
    h.send('/libro Destino | Autor')
    result = h.send('Destino')
    assert a in result.text and b in result.text
    c = h.send('/nota posterior').refs[0]
    payload = json.loads(h.store.db.execute('SELECT payload FROM pending_interactions').fetchone()[0])
    assert {t[0] for t in payload['targets']} == {a,b}
    assert c not in h.send('/confirmar').refs
    assert h.store.db.execute('SELECT COUNT(*) FROM notes WHERE book IS NULL').fetchone()[0] == 0


def test_pending_answer_is_not_note_and_cancel_keeps_data(h):
    h.send('pendiente')
    h.send('selección no válida')
    assert h.store.db.execute('SELECT COUNT(*) FROM notes').fetchone()[0] == 1
    h.send('/nota otra')
    h.send('/cancelar')
    assert h.store.db.execute('SELECT COUNT(*) FROM notes WHERE book IS NULL').fetchone()[0] == 2


def test_ambiguous_title_preserves_active_and_bad_number_is_not_note(h):
    h.activate()
    h.send('/libro Igual | Uno')
    h.send('/libro Igual | Dos')
    active = h.store.db.execute('SELECT book FROM reading_state').fetchone()[0]
    assert '1.' in h.send('/activar Igual').text
    h.send('42')
    assert h.store.db.execute('SELECT book FROM reading_state').fetchone()[0] == active
    h.send('2')
    assert 'Dos [activo]' in h.send('/libros').text
    assert not h.store.db.execute('SELECT * FROM notes').fetchall()


def test_history_edit_move_keeps_reference_date_and_active(h):
    h.activate()
    ref = h.send('original').refs[0]
    before = dict(h.store.db.execute('SELECT * FROM notes').fetchone())
    h.send('/editar '+ref+' corregido')
    h.send('/libro Destino | Autor')
    h.send('/mover '+ref+' | Destino')
    after = dict(h.store.db.execute('SELECT * FROM notes').fetchone())
    assert before['created_at'] == after['created_at'] and before['seq'] == after['seq']
    assert 'original' in h.send('/historial '+ref).text
    assert 'corregido' in h.send('/ver '+ref).text
    assert 'Libro A' in h.send('/libros').text.split('[activo]')[0]


def test_delete_revalidates_version_and_cancel_does_not_delete(h):
    h.activate()
    ref = h.send('original privado').refs[0]
    assert 'todas sus versiones' in h.send('/eliminar '+ref).text
    h.send('/editar '+ref+' cambiado')
    assert 'cambiado' in h.send('/confirmar').text
    assert h.store.db.execute('SELECT COUNT(*) FROM notes').fetchone()[0] == 1
    h.send('/eliminar '+ref)
    h.send('/cancelar')
    assert 'cambiado' in h.send('/ver '+ref).text
    h.send('/eliminar '+ref)
    h.send('/confirmar')
    assert not h.store.db.execute('SELECT * FROM notes').fetchall()
    assert not h.store.db.execute('SELECT * FROM note_versions').fetchall()
    assert not h.store.db.execute('SELECT * FROM notes_fts').fetchall()
    assert 'cambiado' not in h.send('/ver '+ref).text
    assert not h.store.db.execute("SELECT 1 FROM outbox WHERE payload LIKE '%original privado%'").fetchall()


def test_pending_confirmation_not_replaced(h):
    h.activate()
    ref = h.send('idea').refs[0]
    h.send('/eliminar '+ref)
    before = h.store.db.execute('SELECT payload FROM pending_interactions').fetchone()[0]
    h.send('/eliminar '+ref)
    h.send('sí')
    h.send('/nota nueva')
    assert h.store.db.execute('SELECT payload FROM pending_interactions').fetchone()[0] == before
    assert h.store.db.execute('SELECT COUNT(*) FROM notes').fetchone()[0] == 2


def test_reopen_preserves_active_and_confirmation(h):
    h.activate()
    ref = h.send('idea').refs[0]
    h.send('/eliminar '+ref)
    path = h.store.path
    h.store.close()
    h.store = Store(path)
    h.app = Application(h.store,owner='1',chat='1',bot='2')
    assert 'Libro A' in h.send('/libros').text
    assert ref in h.send('/confirmar').refs


def test_failed_write_does_not_leave_receipt_or_confirmation(h):
    h.activate()
    h.store.db.execute("CREATE TRIGGER fail_note BEFORE INSERT ON notes BEGIN SELECT RAISE(ABORT,'disk failure'); END")
    h.store.db.commit()
    with pytest.raises(sqlite3.DatabaseError):
        h.send('must not be confirmed', message='9999')
    assert h.store.db.execute('SELECT COUNT(*) FROM notes').fetchone()[0] == 0
    assert not h.store.db.execute("SELECT 1 FROM processed_events WHERE key LIKE '%9999%'").fetchall()


@pytest.mark.parametrize('field,value',[('user','other'),('chat','group'),('bot','otherbot')])
def test_authorization_at_application_boundary(h,field,value):
    data = dict(bot='2',user='1',chat='1',message='42',text='private')
    data[field] = value
    with pytest.raises(PermissionError):
        h.app.handle(Event(**data))
    assert not h.store.db.execute('SELECT * FROM processed_events').fetchall()


def test_parser_preserves_note_content_and_checks_bot_target():
    assert parse('/nota  línea\nsegunda ').args == (' línea\nsegunda ',)
    with pytest.raises(UserError):
        parse('/nota@other texto',bot_username='margenbot')
    assert parse('/nota@margenbot texto',bot_username='margenbot').command == 'nota'


def test_same_text_from_two_new_messages_is_two_notes(h):
    h.activate()
    assert h.send('repetido').refs!=h.send('repetido').refs
    assert h.store.db.execute('SELECT count(*) FROM notes').fetchone()[0]==2
