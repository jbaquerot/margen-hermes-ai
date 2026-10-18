from __future__ import annotations

import json
from . import books, conversations as conv, events, notes
from .commands import parse
from .domain import Event, Response, UserError, now, reference, display_date


class Application:
    def __init__(self, store, *, owner: str, chat: str, bot: str):
        self.store, self.owner, self.chat, self.bot = store, str(owner), str(chat), str(bot)

    def handle(self, event: Event, *, bot_username=None) -> Response:
        if (event.user, event.chat, event.bot) != (self.owner, self.chat, self.bot):
            raise PermissionError("Origen no autorizado")
        with self.store.transaction() as db:
            old = events.previous(db, event)
            if old:
                return old
            db.execute("SAVEPOINT command")
            try:
                result = self._route(db, parse(event.text, bot_username=bot_username))
                db.execute("RELEASE command")
            except UserError as exc:
                db.execute("ROLLBACK TO command")
                db.execute("RELEASE command")
                result = Response(str(exc))
            events.record(db, event, result)
        return result

    def _choose(self, db, action, args=(), choices=None):
        if conv.pending(db, self.owner):
            raise UserError("Resuelve la interacción pendiente o usa /cancelar antes de iniciar otra.")
        options = books.all_books(db, self.owner) if choices is None else choices
        conv.set_pending(db, self.owner, 'select', {'action': action, 'args': list(args), 'options': [b['id'] for b in options]})
        listing = '\n'.join(f"{i}. {books.label(b)}" for i,b in enumerate(options, 1))
        return Response("Selecciona el libro (número o título). /cancelar para abandonar.\n" + (listing or "Registra primero uno con /libro Título | Autor y luego indica su título."))

    def _resolve(self, db, text, pending):
        opts = pending['options']
        if text.strip().isdigit():
            index = int(text.strip()) - 1
            if index < 0 or index >= len(opts):
                return Response("Número fuera de las opciones. Selecciona uno válido o usa /cancelar.")
            book = books.get(db, self.owner, opts[index])
        else:
            matches = books.matching(db, self.owner, text)
            if not matches:
                return Response("Libro no encontrado. Usa /libro Título | Autor para registrarlo; después indica su título.")
            if len(matches) > 1:
                pending['options'] = [b['id'] for b in matches]
                conv.set_pending(db, self.owner, 'select', pending)
                return Response("Selecciona por número:\n" + '\n'.join(f"{i}. {books.label(b)}" for i,b in enumerate(matches,1)))
            book = matches[0]
        conv.clear(db, self.owner)
        return self._selected(db, book, pending['action'], pending['args'])

    def _selected(self, db, book, action, args):
        if action == 'move':
            ref = args[0]
            notes.move(db, self.owner, ref, book['id'])
            return Response(f"Nota {ref} asignada a {books.label(book)}. Libro activo sin cambios.", [ref])
        books.activate(db, self.owner, book['id'])
        if action in ('resumen', 'exportar', 'resumenes'):
            return self._book_operation(db, action, args, book)
        pending = notes.for_book(db, self.owner, None)
        if len(pending) == 1:
            ref = pending[0]['ref']
            notes.move(db, self.owner, ref, book['id'])
            return Response(f"Nota {ref} guardada en {books.label(book)}. Libro activo: {books.label(book)}.", [ref])
        if len(pending) > 1:
            targets = [[r['ref'], r['version'], r['book']] for r in pending]
            conv.set_pending(db, self.owner, 'assign', {'book': book['id'], 'targets': targets})
            return Response(f"Libro activo: {books.label(book)}.\nAsignar estas notas pendientes a ese libro:\n" + '\n'.join(r['ref'] for r in pending) + "\n/confirmar o /cancelar.", [r['ref'] for r in pending])
        return Response("Libro activo: " + books.label(book))

    def _book_operation(self, db, cmd, args, book):
        if cmd == 'resumenes':
            from .summaries import listing
            return listing(db, self.owner, book)
        snapshot = [dict(r) for r in notes.for_book(db, self.owner, book['id'])]
        if not snapshot:
            return Response("El libro no tiene notas guardadas.")
        payload = {'book': dict(book), 'notes': snapshot, 'mode': args[0] if args else None}
        ident = reference('J')
        db.execute("INSERT INTO jobs(id,owner,kind,payload,created_at) VALUES(?,?,?,?,?)", (ident, self.owner, cmd, json.dumps(payload), now()))
        return Response("Petición registrada.", job=ident)

    def _confirm(self, db, pending):
        kind, payload = pending
        if kind not in ('delete','assign'):
            return Response("No hay una acción pendiente de confirmación. Selecciona una opción o usa /cancelar.")
        targets = payload['targets']
        current = []
        for ref, version, book in targets:
            try:
                row = notes.get(db, self.owner, ref)
            except UserError:
                conv.clear(db, self.owner)
                return Response("Una nota ya no existe. La acción se ha cancelado; revisa y solicita de nuevo.")
            current.append([ref, row['version'], row['book']])
        if current != targets:
            conv.clear(db, self.owner)
            return Response("Las notas han cambiado. Acción cancelada: revisa su versión actual y solicita de nuevo.")
        conv.clear(db, self.owner)
        if kind == 'delete':
            notes.delete(db, self.owner, targets[0][0])
            return Response("Nota y todo su historial eliminados: " + targets[0][0], [targets[0][0]])
        for ref, *_ in targets:
            notes.move(db, self.owner, ref, payload['book'])
        return Response("Notas asignadas a " + books.label(books.get(db, self.owner, payload['book'])) + ': ' + ', '.join(t[0] for t in targets), [t[0] for t in targets])

    def _route(self, db, intent):
        cmd, args = intent.command, intent.args
        pending = conv.pending(db, self.owner)
        if cmd == 'cancelar':
            conv.clear(db, self.owner)
            return Response("Interacción cancelada. Las notas conservadas se mantienen." if pending else "No hay interacción pendiente.")
        if cmd == 'confirmar':
            return self._confirm(db, pending) if pending else Response("No hay acción que confirmar.")
        if pending and cmd == 'text':
            if pending[0] == 'select':
                return self._resolve(db, args[0], pending[1])
            return Response("Usa /confirmar o /cancelar. Para añadir una nota nueva usa /nota texto.")
        if cmd == 'libro':
            book, created = books.register(db, self.owner, *args)
            return Response(("Libro registrado: " if created else "El libro ya está registrado: ") + books.label(book) + '. El libro activo no cambia.')
        if cmd == 'activar':
            if pending:
                if pending[0] == 'select':
                    return self._resolve(db, args[0], pending[1])
                raise UserError("Resuelve o cancela la confirmación pendiente antes de cambiar el libro activo.")
            matches = books.matching(db, self.owner, args[0])
            if not matches:
                raise UserError("Libro no registrado. Usa /libro Título | Autor. El activo no cambia.")
            if len(matches) > 1:
                return self._choose(db, 'activate', choices=matches)
            return self._selected(db, matches[0], 'activate', ())
        if cmd == 'libros':
            active = books.active(db, self.owner)
            rows = books.all_books(db, self.owner)
            return Response(('\n'.join(books.label(b) + (' [activo]' if active and active['id'] == b['id'] else '') for b in rows) or 'No hay libros registrados.') + ('' if active else '\nSin libro activo.'))
        if cmd in ('text','nota'):
            row = notes.create(db, self.owner, args[0])
            if row['book']:
                return Response(f"Nota guardada en {books.label(books.get(db, self.owner, row['book']))}. Referencia: {row['ref']}", [row['ref']])
            response = f"Nota conservada pendiente de asignación. Referencia: {row['ref']}\n"
            if not pending:
                selected = self._choose(db, 'assign')
                response += selected.text
            else:
                response += "Sin libro asignado. La interacción previa sigue pendiente."
            return Response(response, [row['ref']])
        if cmd in ('ver','historial','editar','mover','eliminar'):
            row = notes.get(db, self.owner, args[0])
            if cmd == 'ver':
                return Response(notes.describe(db, self.owner, row), [row['ref']])
            if cmd == 'historial':
                versions = db.execute("SELECT * FROM note_versions WHERE ref=? ORDER BY version", (row['ref'],)).fetchall()
                return Response(row['ref'] + '\n' + '\n\n'.join(f"Versión {v['version']} ({display_date(v['created_at'])})" + (' [vigente]' if v['version'] == row['version'] else '') + '\n' + v['text'] for v in versions), [row['ref']])
            if cmd == 'editar':
                notes.edit(db, self.owner, *args)
                return Response("Nota corregida; original conservado. Resúmenes afectados desactualizados. " + row['ref'], [row['ref']])
            if cmd == 'mover':
                matches = books.matching(db, self.owner, args[1])
                if not matches:
                    raise UserError("Libro de destino no registrado; la nota no cambia.")
                if len(matches) > 1:
                    return self._choose(db, 'move', (args[0],), matches)
                old = books.label(books.get(db, self.owner, row['book'])) if row['book'] else 'Sin libro asignado'
                notes.move(db, self.owner, row['ref'], matches[0]['id'])
                return Response(f"{row['ref']}: {old} → {books.label(matches[0])}. Libro activo sin cambios.", [row['ref']])
            if pending:
                raise UserError("Resuelve o cancela la interacción pendiente antes de eliminar.")
            conv.set_pending(db, self.owner, 'delete', {'targets': [[row['ref'], row['version'], row['book']]]})
            return Response(notes.describe(db, self.owner, row) + '\nSe borrarán el original y todas sus versiones. Los resúmenes previos y copias ya enviados pueden conservar información.\n/confirmar para eliminar o /cancelar.', [row['ref']])
        if cmd in ('resumen','exportar','resumenes'):
            book = books.active(db, self.owner)
            return self._book_operation(db, cmd, args, book) if book else self._choose(db, cmd, args)
        if cmd == 'ver_resumen':
            from .summaries import show
            return show(db, self.owner, args[0])
        if cmd == 'buscar':
            ident = reference('J')
            db.execute("INSERT INTO jobs(id,owner,kind,payload,created_at) VALUES(?,?,?,?,?)", (ident, self.owner, 'buscar', json.dumps({'query': args[0]}), now()))
            return Response('Búsqueda registrada.', job=ident)
        if cmd == 'mas':
            from .search import page
            return page(db, self.owner)
        raise UserError("Comando no disponible.")
