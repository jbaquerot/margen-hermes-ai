import asyncio
from io import BytesIO
from dataclasses import asdict
import json
from .domain import Response
from .outbox import acknowledge, progress, sent_parts


def split_text(text, limit=1800):
    # 1800 code points also fit Telegram's UTF-16 limit for astral characters.
    pieces = [text[i:i+limit] for i in range(0,len(text),limit)] or [' ']
    if len(pieces) > 1:
        return [f"({i}/{len(pieces)})\n{part}" for i,part in enumerate(pieces,1)]
    return pieces


class Delivery:
    def __init__(self, store, jobs, bot, chat):
        self.store, self.jobs, self.bot, self.chat = store, jobs, bot, chat
        self.lock = asyncio.Lock()
        self.inflight = {}

    async def send(self, response, owner):
        key = response.receipt or str(id(response))
        existing = self.inflight.get(key)
        if existing:
            return await asyncio.shield(existing)
        task = asyncio.create_task(self._send(response,owner))
        self.inflight[key] = task
        try:
            return await asyncio.shield(task)
        finally:
            if task.done():
                self.inflight.pop(key,None)

    def _invalidated(self, receipt):
        if not receipt:
            return False
        with self.store.lock:
            row = self.store.db.execute("SELECT delivered FROM outbox WHERE event_key=?", (receipt,)).fetchone()
        return bool(row and row[0])

    async def _send(self, response, owner):
        if response.receipt:
            with self.store.lock:
                row = self.store.db.execute("SELECT delivered FROM outbox WHERE event_key=?", (response.receipt,)).fetchone()
            if row and row[0]:
                return
        if response.job:
            task = asyncio.create_task(self.jobs.run(response.job, owner))
            done, _ = await asyncio.wait({task},timeout=5)
            if not done:
                try:
                    await self.bot.send_message(chat_id=self.chat,text="Sigo trabajando. Las notas guardadas se conservan.", parse_mode=None)
                except Exception:
                    pass
            final = await task
            final.receipt = response.receipt
            with self.store.transaction() as db:
                # A deletion can invalidate the original receipt while the job runs.
                row = db.execute("SELECT delivered FROM outbox WHERE event_key=?", (response.receipt,)).fetchone()
                if row and row[0]:
                    return
                db.execute("UPDATE outbox SET payload=?,sent_parts=0 WHERE event_key=?", (json.dumps(asdict(final)),response.receipt))
                db.execute("UPDATE jobs SET result=NULL WHERE id=?", (response.job,))
            response = final
        async with self.lock:
            parts = split_text(response.text)
            start = sent_parts(self.store,response.receipt)
            for index, part in enumerate(parts):
                if index < start:
                    continue
                if self._invalidated(response.receipt):
                    return
                await self._attempt(self.bot.send_message, chat_id=self.chat,text=part,parse_mode=None)
                progress(self.store,response.receipt,index+1)
            if response.document is not None and start <= len(parts):
                if self._invalidated(response.receipt):
                    return
                data = BytesIO(response.document.encode('utf-8'))
                data.name = response.filename or 'margen.md'
                await self._attempt(self.bot.send_document, chat_id=self.chat,document=data,filename=data.name)
                progress(self.store,response.receipt,len(parts)+1)
            acknowledge(self.store,response.receipt)

    async def _attempt(self, method, **kwargs):
        # Retry only explicit rate-limit refusal, not uncertain network outcomes.
        for attempt in range(3):
            try:
                return await method(**kwargs)
            except Exception as exc:
                delay = getattr(exc,'retry_after',None)
                if hasattr(delay,'total_seconds'):
                    delay = delay.total_seconds()
                if delay is None or delay > 30 or attempt == 2:
                    raise
                await asyncio.sleep(float(delay)+0.1)

    async def retry_pending(self, owner):
        with self.store.lock:
            rows = self.store.db.execute("SELECT payload FROM outbox WHERE owner=? AND delivered=0 AND payload IS NOT NULL ORDER BY rowid", (owner,)).fetchall()
        for row in rows:
            await self.send(Response(**json.loads(row[0])),owner)
