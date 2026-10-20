import asyncio
from dataclasses import asdict
import json
import logging
import sqlite3
from .domain import Response, SummaryFailure, SUMMARY_FAILURE_CODES
from . import summaries, exports, search


class Jobs:
    def __init__(self, store, *, model=None, embedder_factory=None):
        self.store, self.model, self.embedder_factory = store, model, embedder_factory
        self._embedder = None
        self.index_lock = asyncio.Lock()

    async def run(self, ident, owner):
        with self.store.transaction() as db:
            row = db.execute("SELECT * FROM jobs WHERE id=? AND owner=?", (ident,owner)).fetchone()
            if not row:
                raise ValueError("Trabajo no encontrado")
            if row['status'] == 'completed':
                return Response(**json.loads(row['result'])) if row['result'] else Response("Operación completada anteriormente. Consulta la referencia entregada o solicita de nuevo la operación.")
            if row['status'] != 'pending':
                return Response("Trabajo en curso, interrumpido o fallido. Consulta sus notas y solicita de nuevo la operación.")
            db.execute("UPDATE jobs SET status='running' WHERE id=?", (ident,))
            payload, kind = json.loads(row['payload']), row['kind']
        stage = 'generate'
        try:
            if kind == 'resumen':
                if self.model is None:
                    raise RuntimeError("Modelo no configurado")
                text = await summaries.generate(self.model, payload)
            elif kind == 'buscar':
                async with self.index_lock:
                    if self._embedder is None:
                        if self.embedder_factory is None:
                            raise RuntimeError("Modelo de búsqueda local no preparado")
                        self._embedder = await asyncio.to_thread(self.embedder_factory)
                    result = await asyncio.to_thread(search.search,self.store,self._embedder,owner,payload['query'])
            else:
                result = exports.render(payload)
            stage = 'save'
            with self.store.transaction() as db:
                status = db.execute("SELECT status FROM jobs WHERE id=?", (ident,)).fetchone()[0]
                if status != 'running':
                    return Response("Operación cancelada porque sus notas cambiaron o se eliminaron. Solicítala de nuevo.")
                if kind == 'resumen':
                    result = summaries.save(db,owner,payload,text)
                # Clear transient snapshots once done. Summary sources live separately.
                db.execute("UPDATE jobs SET status='completed',payload='{}',result=? WHERE id=?", (json.dumps(asdict(result)),ident))
            return result
        except Exception as exc:
            code = 'operation_failed'
            if isinstance(exc, SummaryFailure) and exc.code in SUMMARY_FAILURE_CODES:
                code = exc.code
            elif isinstance(exc, TimeoutError):
                code = 'operation_timeout'
            elif isinstance(exc, sqlite3.Error):
                code = 'operation_storage'
            # Do not log exception messages, tracebacks, IDs, payloads or provider output.
            safe_kind = kind if kind in ('resumen', 'buscar', 'exportar') else 'other'
            logging.getLogger('margen').warning(
                'operation_failed kind=%s stage=%s code=%s', safe_kind, stage, code)
            with self.store.transaction() as db:
                db.execute("UPDATE jobs SET status='failed',payload='{}',error=?,result=NULL WHERE id=?", (code,ident))
            return Response("La operación no se ha completado. Las notas guardadas se conservan. Revisa la configuración local o solicita de nuevo la operación; no se considera ausencia de coincidencias.")
