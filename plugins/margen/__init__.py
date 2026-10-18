"""Hermes loads this package under its own plugin namespace."""


def register(ctx):
    if ctx.profile_name != 'margen':
        return
    from .margen.commands import FORMATS
    from .margen.application import Application
    from .margen.storage import Store
    from .margen.jobs import Jobs
    from .margen.model import HermesModel
    from .margen.embeddings import LocalE5
    from .margen.delivery import Delivery
    from .margen.ingress import telegram_factory
    from pathlib import Path

    owner = str(ctx.get_config('allowed_user_id',''))
    chat = str(ctx.get_config('allowed_chat_id',''))
    if not owner.isdecimal() or not chat.isdecimal():
        import logging
        logging.getLogger('margen').error('Margen bloqueado: configurar allowed_user_id y allowed_chat_id numéricos.')
        ctx.register_platform_handler('telegram',telegram_factory(ctx,None,None,owner='invalid',chat='invalid'))
        return
    state = {}

    def make_app(bot):
        if not state:
            from plugins.plugin_storage import plugin_data_dir, plugin_db
            root = plugin_data_dir('margen')
            root.chmod(0o700)
            store = Store(root/'data.db',connection=plugin_db('margen'))
            store.recover_interrupted_jobs()
            state['store'] = store
            state['root'] = root
        return Application(state['store'],owner=owner,chat=chat,bot=bot)

    def make_delivery(app,bot):
        model_root = ctx.get_config('model_dir',str(state['root']/'models'/'e5'))
        jobs = Jobs(app.store,model=HermesModel(ctx),embedder_factory=lambda:LocalE5(Path(model_root)))
        return Delivery(app.store,jobs,bot,chat)

    for command, hint in FORMATS.items():
        handle = ctx.register_command(command,handler=lambda raw_args: 'Este comando de Margen debe enviarse al bot privado de Telegram configurado.',description=hint,args_hint=hint.partition(' ')[2])
        if handle is None:
            raise RuntimeError(f'No se pudo registrar /{command}; revisar colisiones de comandos.')
    ctx.register_platform_handler('telegram',telegram_factory(ctx,make_app,make_delivery,owner=owner,chat=chat))
