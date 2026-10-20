import asyncio
import json
import pytest
from margen.jobs import Jobs
from margen.summaries import checked_output


class Model:
    def __init__(self, before=None):
        self.before = before
    async def complete(self,messages,*,max_tokens):
        if self.before:
            self.before()
            self.before = None
        data = json.loads(messages[1]['content'].split('DATOS JSON:\n')[1])
        refs = list(dict.fromkeys(r for item in data for r in item['sources']))
        return json.dumps({'sections':[{'sources':refs,'text':'Síntesis de prueba respaldada por los datos sintéticos.'}]})


def run_job(h,response,model=None):
    return asyncio.run(Jobs(h.store,model=model or Model()).run(response.job,'1'))


def test_summary_created_only_on_request_and_stale_on_changes(h):
    h.activate()
    ref = h.send('idea').refs[0]
    assert not h.store.db.execute('SELECT * FROM summaries').fetchall()
    result = run_job(h,h.send('/resumen'))
    assert 'Resumen de las notas' in result.text
    saved = h.store.db.execute('SELECT * FROM summaries').fetchone()
    assert saved['mode'] == 'brief' and saved['stale'] == 0
    h.send('/editar '+ref+' matiz añadido')
    assert 'DESACTUALIZADO' in h.send('/ver_resumen '+saved['ref']).text
    assert h.store.db.execute('SELECT COUNT(*) FROM summaries').fetchone()[0] == 1


def test_change_during_generation_marks_new_summary_stale(h):
    h.activate()
    h.send('primera')
    result = run_job(h,h.send('/resumen detallado'),Model(before=lambda:h.send('segunda')))
    assert 'DESACTUALIZADO' in result.text
    assert h.store.db.execute('SELECT mode FROM summaries').fetchone()[0] == 'detailed'


def test_job_keeps_original_book_after_active_switch(h):
    h.activate()
    h.send('primera')
    request = h.send('/resumen')
    h.activate('Otro')
    assert 'Libro A' in run_job(h,request).text


def test_summary_survives_original_deletion_without_history(h):
    h.activate()
    ref = h.send('original').refs[0]
    run_job(h,h.send('/resumen'))
    h.send('/eliminar '+ref)
    h.send('/confirmar')
    saved = h.store.db.execute('SELECT * FROM summaries').fetchone()
    assert saved['stale'] and h.store.db.execute('SELECT COUNT(*) FROM summary_sources').fetchone()[0] == 1
    assert 'DESACTUALIZADO' in h.send('/ver_resumen '+saved['ref']).text


def test_selection_resumes_original_summary_mode(h):
    h.send('/libro Uno | Autor')
    response = h.send('/resumen detallado')
    assert 'Selecciona' in response.text
    result = h.send('1')
    assert 'no tiene notas' in result.text
    h.send('nota')
    assert 'Uno' in run_job(h,h.send('/resumen detallado')).text


@pytest.mark.parametrize('data',[
    {'sections':[{'sources':['invented'],'text':'falso'}]},
    {'sections':[{'sources':['b'],'text':'segundo'},{'sources':['a'],'text':'primero'}]},
    {'sections':[{'sources':['a'],'text':'omite b'}]},
])
def test_invalid_source_coverage_and_order_rejected(data):
    with pytest.raises(RuntimeError):
        checked_output(json.dumps(data),['a','b'])


def test_export_is_complete_and_uses_current_order(h):
    h.activate()
    a = h.send('# original\ntexto *literal*').refs[0]
    b = h.send('segunda').refs[0]
    h.send('/editar '+a+' actualizado')
    request = h.send('/exportar')
    h.activate('Otro')
    output = run_job(h,request)
    assert output.filename.endswith('.md') and output.document.index(a) < output.document.index(b)
    assert 'actualizado' in output.document and 'original' not in output.document
    assert 'Libro A' in output.document


def test_failed_model_does_not_claim_a_summary(h):
    h.activate()
    h.send('nota')
    class Broken:
        async def complete(self,*args,**kwargs):
            raise TimeoutError()
    output = run_job(h,h.send('/resumen'),Broken())
    assert 'no se ha completado' in output.text
    assert h.store.db.execute('SELECT COUNT(*) FROM notes').fetchone()[0] == 1
    assert h.store.db.execute('SELECT COUNT(*) FROM summaries').fetchone()[0] == 0


def test_long_notes_all_fragments_reach_model_without_truncation(h):
    h.activate()
    original='Inicio '+('datos de lectura '*5000)+' FINAL_INDISPENSABLE'
    h.send(original)
    class Tracking(Model):
        def __init__(self):
            super().__init__()
            self.contents=[]
        async def complete(self,messages,**kwargs):
            data=json.loads(messages[1]['content'].split('DATOS JSON:\n')[1])
            self.contents.extend(item['text'] for item in data)
            return await super().complete(messages,**kwargs)
    model=Tracking()
    result=run_job(h,h.send('/resumen'),model)
    assert 'Resumen de las notas' in result.text
    assert any('FINAL_INDISPENSABLE' in item for item in model.contents)
    assert any(item.startswith('Inicio ') for item in model.contents)


def test_hermes_model_contract_and_wrong_provider_rejection():
    from margen.model import HermesModel
    from margen.domain import SUMMARY_MODEL
    from types import SimpleNamespace
    class Llm:
        provider='openrouter'
        async def acomplete(self,**kwargs):
            assert kwargs['temperature']==0.1 and kwargs['timeout']==180
            assert 'provider' not in kwargs and 'model' not in kwargs
            return SimpleNamespace(provider=self.provider,model=SUMMARY_MODEL,text='JSON sintético')
    llm=Llm()
    model=HermesModel(SimpleNamespace(llm=llm))
    assert asyncio.run(model.complete([{'role':'user','content':'datos'}],max_tokens=3000))=='JSON sintético'
    llm.provider='other'
    with pytest.raises(RuntimeError):
        asyncio.run(model.complete([],max_tokens=3000))


@pytest.mark.parametrize('raw,code', [
    ('respuesta sin JSON', 'summary_json'),
    ('[]', 'summary_structure'),
    (json.dumps({'sections':[{'sources':['invented'],'text':'idea'}]}), 'summary_sources'),
    (json.dumps({'sections':[{'sources':['b'],'text':'dos'},{'sources':['a'],'text':'uno'}]}), 'summary_order'),
    (json.dumps({'sections':[{'sources':['a'],'text':'incompleto'}]}), 'summary_coverage'),
])
def test_summary_diagnostics_distinguish_rejection_without_relaxing_checks(raw, code):
    from margen.domain import SummaryFailure
    with pytest.raises(SummaryFailure) as caught:
        checked_output(raw, ['a', 'b'])
    assert caught.value.code == code


@pytest.mark.parametrize('failure,code', [
    (TimeoutError('PRIVATE_EXCEPTION'), 'operation_timeout'),
    (RuntimeError('PRIVATE_EXCEPTION'), 'operation_failed'),
])
def test_job_diagnostic_never_logs_private_payload_or_exception(h, caplog, failure, code):
    h.activate()
    h.send('PRIVATE_NOTE')
    class Broken:
        async def complete(self, *args, **kwargs):
            raise failure
    output = run_job(h, h.send('/resumen'), Broken())
    assert 'no se ha completado' in output.text
    row = h.store.db.execute('SELECT * FROM jobs').fetchone()
    assert row['error'] == code and row['payload'] == '{}' and row['result'] is None
    assert 'kind=resumen stage=generate code=' + code in caplog.text
    assert 'PRIVATE_NOTE' not in caplog.text and 'PRIVATE_EXCEPTION' not in caplog.text
    assert not any(record.exc_info for record in caplog.records)
    assert h.store.db.execute('SELECT COUNT(*) FROM summaries').fetchone()[0] == 0
    assert h.store.db.execute('SELECT COUNT(*) FROM notes').fetchone()[0] == 1


def test_provider_failure_is_classified_without_exposing_response(h, caplog):
    from margen.model import HermesModel
    from types import SimpleNamespace
    class Llm:
        async def acomplete(self, **kwargs):
            raise ValueError('PRIVATE_PROVIDER_RESPONSE')
    h.activate()
    h.send('PRIVATE_NOTE')
    output = run_job(h, h.send('/resumen'), HermesModel(SimpleNamespace(llm=Llm())))
    assert 'no se ha completado' in output.text
    assert h.store.db.execute('SELECT error FROM jobs').fetchone()[0] == 'summary_provider'
    assert 'code=summary_provider' in caplog.text
    assert 'PRIVATE_PROVIDER_RESPONSE' not in caplog.text and 'PRIVATE_NOTE' not in caplog.text


def test_job_records_specific_summary_rejection(h, caplog):
    h.activate()
    h.send('PRIVATE_NOTE')
    class Invalid:
        async def complete(self, *args, **kwargs):
            return json.dumps({'sections':[{'sources':['PRIVATE_FAKE_SOURCE'],'text':'PRIVATE_OUTPUT'}]})
    output = run_job(h, h.send('/resumen'), Invalid())
    assert 'no se ha completado' in output.text
    assert h.store.db.execute('SELECT error FROM jobs').fetchone()[0] == 'summary_sources'
    assert 'code=summary_sources' in caplog.text
    assert not any(secret in caplog.text for secret in ('PRIVATE_NOTE', 'PRIVATE_FAKE_SOURCE', 'PRIVATE_OUTPUT'))
