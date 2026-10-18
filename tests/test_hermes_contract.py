"""Static source contract plus isolated registration. Not a running Hermes test."""
import ast
import importlib.util
import os
from pathlib import Path
import pytest
from margen.commands import FORMATS


def test_plugin_registration_profile_scope_and_public_interfaces():
    spec=importlib.util.spec_from_file_location('margen_plugin',Path('plugins/margen/__init__.py'),submodule_search_locations=['plugins/margen'])
    plugin=importlib.util.module_from_spec(spec)
    import sys
    sys.modules[spec.name]=plugin
    spec.loader.exec_module(plugin)
    class Context:
        profile_name='other'
        def __init__(self):
            self.commands=[]
            self.factories=[]
        def get_config(self,name,default=None):
            return {'allowed_user_id':'1','allowed_chat_id':'1'}.get(name,default)
        def register_command(self,name,**kwargs):
            self.commands.append(name)
            return object()
        def register_platform_handler(self,platform,factory):
            self.factories.append((platform,factory))
    ctx=Context()
    plugin.register(ctx)
    assert not ctx.commands
    ctx.profile_name='margen'
    plugin.register(ctx)
    assert set(ctx.commands)==set(FORMATS)
    assert [f[0] for f in ctx.factories]==['telegram']


def test_pinned_hermes_source_contract():
    source=os.environ.get('HERMES_SOURCE')
    if not source:
        pytest.skip('HERMES_SOURCE: archivo público de la revisión objetivo, sin ejecutar Hermes')
    root=Path(source)
    tree=ast.parse((root/'hermes_cli/commands.py').read_text())
    names=set()
    for call in ast.walk(tree):
        if isinstance(call,ast.Call) and isinstance(call.func,ast.Name) and call.func.id=='CommandDef':
            if call.args and isinstance(call.args[0],ast.Constant):
                names.add(call.args[0].value)
            for kw in call.keywords:
                if kw.arg=='aliases':
                    names.update(ast.literal_eval(kw.value))
    assert names and not names.intersection(FORMATS)
    tree=ast.parse((root/'hermes_cli/plugins.py').read_text())
    functions={n.name:n for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
    assert {'name','handler','description','args_hint'} <= {a.arg for a in functions['register_command'].args.args}
    assert {'platform','factory'} <= {a.arg for a in functions['register_platform_handler'].args.args}
    llm=ast.parse((root/'agent/plugin_llm.py').read_text())
    complete=next(n for n in ast.walk(llm) if isinstance(n,ast.AsyncFunctionDef) and n.name=='acomplete')
    assert {'max_tokens','timeout','purpose'} <= {a.arg for a in complete.args.kwonlyargs}
    telegram=(root/'plugins/platforms/telegram/adapter.py').read_text()
    assert '_wire_plugin_handlers(self._app)' in telegram
