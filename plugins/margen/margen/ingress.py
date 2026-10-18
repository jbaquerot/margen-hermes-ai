from .domain import Event


def telegram_factory(ctx, make_app, make_delivery, *, owner, chat):
    """Public factory; SDK imports deferred until Telegram connects."""
    def wire(native, adapter):
        from telegram.ext import MessageHandler, filters, ApplicationHandlerStop
        from hermes_cli.commands import resolve_command
        state = {}

        async def receive(update, context):
            message, user = update.effective_message, update.effective_user
            if not message or not user:
                raise ApplicationHandlerStop
            if message.chat.type != 'private' or str(user.id) != owner or str(message.chat_id) != chat:
                raise ApplicationHandlerStop
            text = message.text or ''
            if text.lstrip().startswith('/'):
                command = text.lstrip()[1:].split(maxsplit=1)[0].split('@')[0]
                if resolve_command(command) is not None:
                    return  # Native administration and callbacks remain Hermes-owned.
            try:
                if not state:
                    app = make_app(str(context.bot.id))
                    delivery = make_delivery(app,context.bot)
                    state.update(app=app,delivery=delivery)
                    native.create_task(delivery.retry_pending(owner),update=update)
                app, delivery = state['app'], state['delivery']
                result = app.handle(Event(str(context.bot.id),str(user.id),str(message.chat_id),str(message.message_id),text),bot_username=context.bot.username)
                async def finish():
                    try:
                        await delivery.send(result,owner)
                    except Exception:
                        # No traceback with user content or provider responses.
                        import logging
                        logging.getLogger('margen').warning('delivery_failed; pending receipt retained')
                native.create_task(finish(),update=update)
            except Exception:
                try:
                    await context.bot.send_message(chat_id=chat,text="No se pudo completar la operación. No se confirma el guardado; si se interrumpió una entrega, un reintento del mismo mensaje no duplica la captura.",parse_mode=None)
                except Exception:
                    pass
            raise ApplicationHandlerStop

        # A single scoped handler consumes Margen traffic before core handlers.
        # Non-text media from the authorized chat are rejected, never passed to an LLM.
        async def unsupported(update,context):
            if update.effective_user and str(update.effective_user.id) == owner and str(update.effective_chat.id) == chat:
                try:
                    await context.bot.send_message(chat_id=chat,text="Margen admite únicamente notas de texto.",parse_mode=None)
                except Exception:
                    pass
            raise ApplicationHandlerStop
        native.add_handler(MessageHandler(filters.TEXT,receive,block=True),group=-100)
        native.add_handler(MessageHandler(filters.ATTACHMENT,unsupported,block=True),group=-100)
    return wire
