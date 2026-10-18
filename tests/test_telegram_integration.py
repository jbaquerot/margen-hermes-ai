import asyncio
import sys
import types
from types import SimpleNamespace
import pytest
from telegram import Update
from telegram.ext import ApplicationHandlerStop
from margen.ingress import telegram_factory
from margen.delivery import Delivery,split_text
from margen.jobs import Jobs


class Bot:
    id=2
    username='margen_test_bot'
    def __init__(self):
        self.messages=[]
        self.documents=[]
        self.fail=False
    async def send_message(self,**kwargs):
        if self.fail:
            raise OSError('network')
        self.messages.append(kwargs['text'])
    async def send_document(self,**kwargs):
        self.documents.append(kwargs['document'].read())


class Native:
    def __init__(self):
        self.handlers=[]
        self.tasks=[]
    def add_handler(self,handler,group):
        self.handlers.append((group,handler))
    def create_task(self,coro,**kwargs):
        task=asyncio.create_task(coro)
        self.tasks.append(task)
        return task


def update(text,user=1,chat=1,message=100):
    return Update.de_json({'update_id':message,'message':{'message_id':message,'date':1,
        'chat':{'id':chat,'type':'private'},'from':{'id':user,'is_bot':False,'first_name':'Test'},'text':text}},None)


def wire(monkeypatch,h,bot):
    commands=types.ModuleType('hermes_cli.commands')
    commands.resolve_command=lambda name:object() if name=='help' else None
    monkeypatch.setitem(sys.modules,'hermes_cli',types.ModuleType('hermes_cli'))
    monkeypatch.setitem(sys.modules,'hermes_cli.commands',commands)
    native=Native()
    telegram_factory(None,lambda ident:h.app,
        lambda app,bot:Delivery(app.store,Jobs(app.store),bot,'1'),owner='1',chat='1')(native,None)
    return native


def test_real_ptb_update_interception_and_original_identity(h,monkeypatch):
    async def run():
        bot=Bot()
        native=wire(monkeypatch,h,bot)
        group,handler=native.handlers[0]
        assert group<0
        u=update('Pendiente original')
        assert handler.check_update(u)
        with pytest.raises(ApplicationHandlerStop):
            await handler.callback(u,SimpleNamespace(bot=bot))
        await asyncio.gather(*native.tasks)
        assert h.store.db.execute('SELECT count(*) FROM notes').fetchone()[0]==1
        assert h.store.db.execute('SELECT key FROM processed_events WHERE key LIKE ?',('%100%',)).fetchone()
        with pytest.raises(ApplicationHandlerStop):
            await handler.callback(u,SimpleNamespace(bot=bot))
        await asyncio.gather(*native.tasks)
        assert h.store.db.execute('SELECT count(*) FROM notes').fetchone()[0]==1
    asyncio.run(run())


def test_unauthorized_text_does_not_reach_domain_and_native_command_falls_through(h,monkeypatch):
    async def run():
        bot=Bot()
        native=wire(monkeypatch,h,bot)
        handler=native.handlers[0][1]
        for u in (update('secret',user=3),update('/nota secret',chat=3)):
            with pytest.raises(ApplicationHandlerStop):
                await handler.callback(u,SimpleNamespace(bot=bot))
        assert await handler.callback(update('/help'),SimpleNamespace(bot=bot)) is None
        assert not native.tasks
        assert h.store.db.execute('SELECT count(*) FROM processed_events').fetchone()[0]==0
    asyncio.run(run())


def test_delivery_failure_retry_and_simultaneous_delivery(h):
    h.activate()
    result=h.send('Una nota')
    async def run():
        bot=Bot()
        delivery=Delivery(h.store,Jobs(h.store),bot,'1')
        bot.fail=True
        with pytest.raises(OSError):
            await delivery.send(result,'1')
        assert h.store.db.execute('SELECT delivered FROM outbox WHERE event_key=?',(result.receipt,)).fetchone()[0]==0
        bot.fail=False
        await asyncio.gather(delivery.send(result,'1'),delivery.send(result,'1'))
        assert len(bot.messages)==1
        assert h.store.db.execute('SELECT payload FROM outbox WHERE event_key=?',(result.receipt,)).fetchone()[0] is None
        assert h.store.db.execute('SELECT count(*) FROM notes').fetchone()[0]==1
    asyncio.run(run())


def test_long_output_fits_utf16_and_export_delivered(h):
    assert all(len(x.encode('utf-16-le'))//2<=4096 for x in split_text('😀'*10000))
    h.activate()
    h.send('Texto íntegro de exportación')
    response=h.send('/exportar')
    async def run():
        bot=Bot()
        await Delivery(h.store,Jobs(h.store),bot,'1').send(response,'1')
        assert 'Texto íntegro'.encode() in bot.documents[0]
        assert h.store.db.execute('SELECT result FROM jobs WHERE id=?',(response.job,)).fetchone()[0] is None
    asyncio.run(run())
