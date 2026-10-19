#!/usr/bin/env python3
"""Verify real Hermes registration in the lab; never starts a bot or inference."""
import argparse
from datetime import datetime, timezone
import importlib.metadata
import json
import os
from pathlib import Path
import sqlite3
import tempfile


PROFILE_HOME = Path('/opt/data/profiles/margen')


def atomic_private_write(path, content):
    fd, temporary = tempfile.mkstemp(prefix='.margen-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def apply_soul(source, target):
    content = Path(source).read_bytes()
    target = Path(target)
    if target.exists():
        old = target.read_bytes()
        if old == content:
            return 'already_applied'
        backup = target.with_name('SOUL.before-margen.md')
        if backup.exists():
            raise RuntimeError('SOUL modificado después de una copia anterior; revisar antes de reemplazarlo')
        fd = os.open(backup, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'wb') as stream:
            stream.write(old)
            stream.flush()
            os.fsync(stream.fileno())
    atomic_private_write(target, content)
    return 'applied'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply-soul', action='store_true')
    args = parser.parse_args()
    if Path(os.environ.get('HERMES_HOME', '')).resolve() not in (Path('/opt/data'), PROFILE_HOME):
        raise RuntimeError('Este preflight exige HERMES_HOME=/opt/data/profiles/margen')
    os.environ['HERMES_HOME'] = str(PROFILE_HOME)
    # Same pre-import activation used by the pinned Hermes entrypoints.
    import hermes_bootstrap  # noqa: F401
    from hermes_cli.config import load_config, get_env_value
    from hermes_cli.plugins import get_plugin_commands, get_plugin_manager
    from hermes_cli.profiles import get_active_profile_name
    from margen.commands import FORMATS

    config = load_config()
    settings = config.get('plugins', {}).get('entries', {}).get('margen', {}).get('settings', {})
    owner, chat = str(settings.get('allowed_user_id', '')), str(settings.get('allowed_chat_id', ''))
    allowed = [x.strip() for x in (get_env_value('TELEGRAM_ALLOWED_USERS') or '').split(',') if x.strip()]
    registered = sorted(name for name, entry in get_plugin_commands().items() if entry.get('plugin') == 'margen')
    factories = [entry for entry in get_plugin_manager().get_platform_handler_factories('telegram') if entry[1] == 'margen']
    with sqlite3.connect(':memory:') as db:
        db.execute('CREATE VIRTUAL TABLE test USING fts5(text)')
    search = json.loads((PROFILE_HOME/'plugin-data/margen/validation/search-arm64.json').read_text())
    model = config.get('model', {})
    if not isinstance(model, dict):
        model = {}
    checks = {
        'profile_margen': get_active_profile_name() == 'margen',
        'all_17_commands_registered': registered == sorted(FORMATS),
        'one_telegram_factory_registered': len(factories) == 1,
        'single_owner_and_private_chat': owner.isdecimal() and owner == chat,
        'telegram_allowlist_matches_owner': allowed == [owner],
        'telegram_home_matches_chat': str(get_env_value('TELEGRAM_HOME_CHANNEL') or '') == chat,
        'local_model_path': settings.get('model_dir') == str(PROFILE_HOME/'plugin-data/margen/models/e5'),
        'openrouter_model': model.get('provider') == 'openrouter' and model.get('default') == 'anthropic/claude-haiku-5.5',
        'search_quality': search.get('hits', 0) >= 8 and search.get('total') == 10,
        'search_linux_arm64': search.get('machine') == 'aarch64' and search.get('platform', '').startswith('Linux'),
        'negative_queries_empty': len(search.get('negative', [])) == 2 and all(not row['top5'] for row in search['negative']),
    }
    report = {
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'checks': checks,
        'registered_commands': registered,
        'sqlite': sqlite3.sqlite_version,
        'fts5': True,
        'packages': {name: importlib.metadata.version(name) for name in ('onnxruntime', 'tokenizers', 'numpy', 'python-telegram-bot', 'openai')},
        'search': {key: search.get(key) for key in ('hits', 'total', 'machine', 'python', 'load_seconds', 'max_rss_native_units', 'rss_unit', 'model_revision')},
        'soul': 'not_requested',
        'ok': all(checks.values()),
        'scope': 'registration and local search; real Telegram and Haiku still pending',
    }
    if args.apply_soul and report['ok']:
        report['soul'] = apply_soul('/lab/profile/SOUL.md', PROFILE_HOME/'SOUL.md')
    output = PROFILE_HOME/'plugin-data/margen/validation/preflight.json'
    output.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    atomic_private_write(output, (json.dumps(report, ensure_ascii=False, indent=2)+'\n').encode())
    # Whitelisted report only: no credentials, IDs, config dump or note content.
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
