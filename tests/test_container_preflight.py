import importlib.util
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location('container_preflight', Path('scripts/preflight-container-margen.py'))
preflight = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preflight)


def test_soul_application_preserves_original_and_refuses_later_edits(tmp_path):
    source, target = tmp_path/'source.md', tmp_path/'SOUL.md'
    source.write_text('Personalidad Margen')
    target.write_text('Personalidad anterior')
    assert preflight.apply_soul(source,target) == 'applied'
    assert (tmp_path/'SOUL.before-margen.md').read_text() == 'Personalidad anterior'
    assert preflight.apply_soul(source,target) == 'already_applied'
    target.write_text('Cambio posterior del usuario')
    with pytest.raises(RuntimeError):
        preflight.apply_soul(source,target)
    assert target.read_text() == 'Cambio posterior del usuario'
    assert (tmp_path/'SOUL.before-margen.md').read_text() == 'Personalidad anterior'
