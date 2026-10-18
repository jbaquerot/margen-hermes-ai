import asyncio
import pytest
from margen.delivery import Delivery
from margen.domain import Response
from margen.ingress import telegram_factory
from test_telegram_integration import Bot,Native,update,wire
from types import SimpleNamespace
from telegram.ext import ApplicationHandlerStop


def test_storage_startup_error_consumes_text_even_if_error_delivery_fails(h,monkeypatch):
    async def run():
        bot=Bot()
        bot.fail=True
        native=wire(monkeypatch,h,bot)  # provides hermes command resolver
        native=Native()
        def fail(_):
            raise OSError('cannot open database')
        telegram_factory(None,fail,None,owner='1',chat='1')(native,None)
        with pytest.raises(ApplicationHandlerStop):
            await native.handlers[0][1].callback(update('never forward to core'),SimpleNamespace(bot=bot))
        assert not native.tasks
    asyncio.run(run())


def test_long_operation_reports_progress_without_blocking_capture(h):
    h.activate()
    class SlowJob:
        async def run(self,*args):
            await asyncio.sleep(5.1)
            return Response('Resultado terminado')
    async def run():
        bot=Bot()
        task=asyncio.create_task(Delivery(h.store,SlowJob(),bot,'1').send(Response('inicio',job='test'),'1'))
        await asyncio.sleep(.01)
        assert h.send('Nota durante el trabajo').refs
        await task
        assert bot.messages==['Sigo trabajando. Las notas guardadas se conservan.','Resultado terminado']
    asyncio.run(run())


def test_deletion_cancels_already_queued_sensitive_delivery(h):
    h.activate()
    ref=h.send('Contenido sensible').refs[0]
    view=h.send('/ver '+ref)
    from margen.jobs import Jobs
    async def run():
        bot=Bot()
        delivery=Delivery(h.store,Jobs(h.store),bot,'1')
        await delivery.lock.acquire()
        task=asyncio.create_task(delivery.send(view,'1'))
        await asyncio.sleep(.01)
        h.send('/eliminar '+ref)
        h.send('/confirmar')
        delivery.lock.release()
        await task
        assert bot.messages==[]
    asyncio.run(run())


def test_partial_delivery_resumes_after_last_acknowledged_part(h):
    h.activate()
    ref=h.send('Texto largo '*600).refs[0]
    response=h.send('/ver '+ref)
    from margen.delivery import split_text
    from margen.jobs import Jobs
    class Interrupted(Bot):
        calls=0
        async def send_message(self,**kwargs):
            self.calls+=1
            if self.calls==2:
                raise OSError('interrupted after first acknowledgement')
            return await super().send_message(**kwargs)
    async def run():
        bot=Interrupted()
        delivery=Delivery(h.store,Jobs(h.store),bot,'1')
        with pytest.raises(OSError):
            await delivery.send(response,'1')
        assert len(bot.messages)==1
        assert h.store.db.execute('SELECT sent_parts FROM outbox WHERE event_key=?',(response.receipt,)).fetchone()[0]==1
        await delivery.send(response,'1')
        assert bot.messages==split_text(response.text)
    asyncio.run(run())
