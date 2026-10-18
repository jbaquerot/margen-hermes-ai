#!/usr/bin/env bash
# Diagnóstico de solo lectura. Ejecutar como claw, sin sudo.
# No arranca Hermes, no contacta con proveedores ni ejecuta el backup.
# Informe JSON por stdout; redirigirlo a un archivo si se desea conservarlo.
set -eu

if [ -x /home/claw/.hermes/hermes-agent/.venv/bin/python ]; then
  margen_python=/home/claw/.hermes/hermes-agent/.venv/bin/python
elif [ -x /home/claw/.hermes/hermes-agent/venv/bin/python ]; then
  margen_python=/home/claw/.hermes/hermes-agent/venv/bin/python
elif command -v python3 >/dev/null 2>&1; then
  margen_python=$(command -v python3)
else
  printf '%s\n' 'Se necesita Python 3 para generar el informe.' >&2
  exit 1
fi

# -I aísla Python del directorio actual y PYTHONPATH; -B evita crear bytecode.
exec "$margen_python" -I -B - <<'PY'
import datetime
import glob
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import re
import shlex
import shutil
import subprocess
import sys
import time

START = time.monotonic()
ACCOUNT = Path('/home/claw')
HERMES = ACCOUNT / '.hermes'
REPO = HERMES / 'hermes-agent'
DEST = Path('/mnt/backup-ssd/backups')
LIMIT = 131072


def read(path):
    """Lectura acotada; nunca devuelve errores con contenido del fichero."""
    try:
        p = Path(path)
        if not p.is_file() or p.stat().st_size > LIMIT:
            return None
        return p.read_text(errors='replace')
    except (OSError, ValueError):
        return None


def run(args, timeout=3):
    if time.monotonic() - START > 45:
        return {'estado': 'omitido_por_tiempo'}
    if not shutil.which(args[0]):
        return {'estado': 'comando_no_disponible'}
    try:
        # Nunca incluir stderr: puede contener líneas de configuración privadas.
        p = subprocess.run(args, capture_output=True, text=True,
                           timeout=timeout, env={**os.environ, 'LC_ALL': 'C',
                           'GIT_OPTIONAL_LOCKS': '0', 'GIT_TERMINAL_PROMPT': '0'})
        if p.returncode:
            return {'estado': 'no_comprobado', 'codigo': p.returncode}
        return {'estado': 'ok', 'datos': p.stdout[:65536].strip()}
    except (OSError, subprocess.TimeoutExpired):
        return {'estado': 'no_comprobado'}


def identifier(value):
    # Solo identificadores breves de proveedor/modelo; nunca cadenas arbitrarias.
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9_./:+-]{1,140}', value):
        return 'no_comprobado'
    if re.search(r'(?:sk-|sk_|Bearer|token|secret|password|api.key)', value, re.I):
        return 'valor_omitido'
    return value


def package(name):
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return 'no_instalado_en_este_interprete'


def safe_paths(text):
    # No evaluar variables ni sustituciones de shell. No devolver líneas enteras.
    result = set()
    for line in text.splitlines():
        if line.lstrip().startswith('#'):
            continue
        try:
            tokens = shlex.split(line, comments=True)
        except ValueError:
            continue
        for token in tokens:
            if re.fullmatch(r'/(?:home|mnt|media|srv|var/backups|etc|usr/local/bin|usr/local/sbin)/[\w./ -]+', token):
                if not any(part in token.lower() for part in ('secret', 'token', 'password')):
                    result.add(token)
    return sorted(result)[:30]


def backup_evidence(path, text):
    active = '\n'.join(line for line in text.splitlines()
                       if line.strip() and not line.lstrip().startswith('#'))
    # Evidencias, no interpretación de un programa arbitrario.
    return {
        'archivo': str(path),
        'menciona_rsync': bool(re.search(r'\brsync\b', active)),
        'menciona_home_hermes': bool(re.search(r'(?:/home/claw/|\$HOME/|~/)\.hermes', active)),
        'menciona_home_claw': '/home/claw' in active,
        'menciona_destino_backup': '/mnt/backup-ssd' in active,
        'usa_exclusiones': bool(re.search(r'--exclude|--filter|--files-from', active)),
        'usa_delete': bool(re.search(r'--delete\b', active)),
        'menciona_snapshot_sqlite': bool(re.search(r'\.backup\b|Connection\.backup|VACUUM\s+INTO', active, re.I)),
        'rutas_literales_detectadas': safe_paths(active),
        'cobertura_hermes': 'requiere_revision_de_fuentes_y_exclusiones',
    }


def config_info(home):
    cfg = home / 'config.yaml'
    result = {'perfil': home.name if home != HERMES else 'default',
              'directorio': str(home), 'config_existe': cfg.is_file(),
              'env_existe_sin_leer': (home / '.env').is_file()}
    content = read(cfg)
    if content is None:
        return result
    # Parsers seguros y conocidos; nunca importar Hermes o ejecutar sus plugins.
    try:
        try:
            from ruamel.yaml import YAML
            data = YAML(typ='safe').load(content)
        except ImportError:
            import yaml
            data = yaml.safe_load(content)
        if not isinstance(data, dict):
            raise ValueError()
        model = data.get('model')
        if isinstance(model, dict):
            result['proveedor'] = identifier(model.get('provider'))
            result['modelo'] = identifier(model.get('model', model.get('default')))
        elif isinstance(model, str):
            result['modelo'] = identifier(model)
        terminal = data.get('terminal')
        if isinstance(terminal, dict):
            result['terminal_backend'] = identifier(terminal.get('backend'))
        gateway = data.get('gateway')
        if isinstance(gateway, dict):
            value = gateway.get('multiplex_profiles')
            result['multiplex_profiles_configurado'] = value is not None
        result['lectura_selectiva'] = 'ok; no se muestran otras claves'
    except Exception:
        result['lectura_selectiva'] = 'no_comprobada; no se imprime YAML ni error'
    return result


report = {
    'diagnostico': 'Margen — solo lectura, sin sudo ni acceso a red',
    'fecha_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'privacidad': 'No se imprimen .env, credenciales, notas, logs, comandos de procesos ni contenido de scripts.',
    'sistema': {'arquitectura': platform.machine(), 'kernel': platform.release(),
                'usuario_efectivo_es_claw': os.geteuid() == getattr(__import__('pwd').getpwnam('claw'), 'pw_uid', -1)
                if sys.platform == 'linux' and ACCOUNT.exists() else 'no_comprobado'},
}
os_release = read('/etc/os-release') or ''
report['sistema']['distribucion'] = next((line.split('=', 1)[1].strip('"')
    for line in os_release.splitlines() if line.startswith('PRETTY_NAME=')), 'no_comprobada')
memory = read('/proc/meminfo') or ''
report['sistema']['memoria'] = {k: v.strip() for k, v in
    re.findall(r'^(MemTotal|MemAvailable|SwapTotal|SwapFree):\s*(.+)$', memory, re.M)}
report['sistema']['discos'] = run(['lsblk', '-o', 'NAME,TYPE,SIZE,FSTYPE,MOUNTPOINTS,TRAN'])
report['sistema']['usb'] = run(['lsusb'])  # Sin números de serie ni logs del kernel.
report['almacenamiento'] = {}
for label, target in [('hermes', HERMES), ('destino_backup', DEST)]:
    report['almacenamiento'][label] = {
        'ruta': str(target), 'existe': target.exists(),
        'montaje_que_cubre_ruta': run(['findmnt', '-n', '-T', str(target), '-o', 'TARGET,SOURCE,FSTYPE']),
        'espacio': run(['df', '-h', str(target)]),
    }
report['almacenamiento']['ssd_backup_montado_exactamente'] = run(
    ['findmnt', '-n', '-M', '/mnt/backup-ssd', '-o', 'TARGET,SOURCE,FSTYPE'])
# No listar las copias: pueden contener nombres de documentos personales.
report['almacenamiento']['destino_backup']['listado_contenido'] = 'omitido'

runtime = {'ejecutable': sys.executable, 'python': platform.python_version(),
           'paquetes': {n: package(n) for n in ('openai', 'python-telegram-bot', 'ruamel.yaml', 'PyYAML')}}
try:
    import sqlite3
    db = sqlite3.connect(':memory:')
    try:
        db.execute('CREATE VIRTUAL TABLE probe USING fts5(text)')
        fts = True
    except sqlite3.Error:
        fts = False
    db.close()
    runtime['sqlite'] = {'version': sqlite3.sqlite_version, 'fts5': fts,
                         'backup_api': hasattr(sqlite3.Connection, 'backup'),
                         'prueba': 'solo base en memoria; no se abren bases existentes'}
except ImportError:
    runtime['sqlite'] = 'modulo_no_disponible'
report['runtime'] = runtime
report['hermes'] = {
    'repositorio': str(REPO), 'existe': REPO.is_dir(),
    'revision': run(['git', '-C', str(REPO), 'rev-parse', '--verify', 'HEAD']),
    'version_git': run(['git', '-C', str(REPO), 'describe', '--tags', '--always']),
    'hermes_en_path': shutil.which('hermes'),
}
homes = [HERMES]
try:
    homes += sorted(p for p in (HERMES / 'profiles').iterdir()
                    if p.is_dir() and not p.is_symlink())[:30]
except OSError:
    pass
report['hermes']['perfiles'] = [config_info(p) for p in homes]
# Comprobación estática; presencia de símbolos no demuestra funcionamiento.
symbols = {'register_platform_handler': False, 'register_command': False,
           'post_gateway_admission': False, 'plugin_data_dir': False,
           'class PluginLlm': False}
files_examined = 0
for dirname in ('hermes_cli', 'plugins', 'agent', 'gateway'):
    for p in (REPO / dirname).glob('*.py'):
        content = read(p)
        if content is not None:
            files_examined += 1
            for key in symbols:
                symbols[key] = symbols[key] or key in content
report['hermes']['simbolos_en_fuentes'] = {'coincidencias_textuales': symbols,
    'archivos_examinados': files_examined, 'ausencia': 'no concluyente; búsqueda acotada a módulos de primer nivel'}

service_pattern = re.compile(r'hermes|margen|backup|rsync|restic|borg|rclone', re.I)
services = []
schedule_files = set()
for scope in ([], ['--user']):
    label = 'usuario' if scope else 'sistema'
    listing = run(['systemctl', *scope, 'list-unit-files', '--type=service', '--type=timer', '--no-legend', '--no-pager'])
    if listing.get('estado') != 'ok':
        services.append({'ambito': label, 'estado': listing['estado']})
        continue
    units = [line.split()[0] for line in listing['datos'].splitlines()
             if line.split() and service_pattern.search(line.split()[0])][:15]
    for unit in units:
        if not re.fullmatch(r'[A-Za-z0-9_.@:-]+', unit):
            continue
        info = run(['systemctl', *scope, 'show', unit, '--no-pager',
                    '--property=Id,ActiveState,SubState,UnitFileState,User,FragmentPath,NextElapseUSecRealtime,LastTriggerUSec'])
        services.append({'ambito': label, 'unidad': unit, 'propiedades': info})
        for line in info.get('datos', '').splitlines():
            if line.startswith('FragmentPath=/'):
                schedule_files.add(Path(line.split('=', 1)[1]))
report['servicios_y_timers'] = services

cron = run(['crontab', '-l'])
cron_lines = []
if cron.get('estado') == 'ok':
    for line in cron['datos'].splitlines():
        if service_pattern.search(line) and not line.lstrip().startswith('#'):
            parts = line.split()
            schedule = ' '.join(parts[:1] if line.startswith('@') else parts[:5])
            # El horario solo puede tener caracteres de cron, nunca el comando.
            if re.fullmatch(r'[@A-Za-z0-9*/?, -]{1,90}', schedule):
                cron_lines.append({'horario': schedule, 'evidencias': backup_evidence('crontab del usuario', line)})
                for literal in safe_paths(line):
                    candidate = Path(literal)
                    if re.search(r'backup|rsync|sync', candidate.name, re.I) and candidate.suffix in ('.sh', '.py', ''):
                        schedule_files.add(candidate)
report['cron_usuario'] = {'estado': cron['estado'], 'entradas_relacionadas': cron_lines}
for pattern in ('/etc/cron.d/*', '/etc/cron.daily/*', '/etc/cron.weekly/*',
                '/home/claw/bin/*backup*', '/home/claw/.local/bin/*backup*',
                '/home/claw/scripts/*backup*', '/home/claw/*backup*.sh',
                '/usr/local/bin/*backup*', '/usr/local/sbin/*backup*'):
    schedule_files.update(Path(p) for p in glob.glob(pattern)[:30])
schedule_files.add(Path('/etc/crontab'))
evidence = []
# Una segunda pasada recoge scripts de backup referenciados por cron/systemd.
for iteration in range(2):
    extra = set()
    for p in sorted(schedule_files)[:80]:
        if any(item['archivo'] == str(p) for item in evidence):
            continue
        content = read(p)
        if content is None or not service_pattern.search(content):
            continue
        item = backup_evidence(p, content)
        # Solo horarios declarados; nunca ExecStart/Environment ni comando cron.
        item['horarios_systemd'] = [line.split('=', 1)[1].strip()
            for line in content.splitlines() if re.match(r'^\s*(OnCalendar|OnBootSec|OnUnitActiveSec)=', line)
            and re.fullmatch(r'[A-Za-z0-9*:,./ +?=-]{1,120}', line.split('=', 1)[1].strip())]
        evidence.append(item)
        for literal in item['rutas_literales_detectadas']:
            candidate = Path(literal)
            if re.search(r'backup|rsync|sync', candidate.name, re.I) and candidate.suffix in ('.sh', '.py', ''):
                extra.add(candidate)
    schedule_files.update(extra)
report['backup_evidencias_selectivas'] = evidence
report['limitaciones'] = [
    'Sin sudo: archivos o servicios no legibles figuran como no comprobados.',
    'No se leen .env, claves, credenciales, notas, sesiones, logs ni contenido de backups.',
    'No se ejecuta Hermes, sus plugins, scripts de backup, rsync ni inferencia.',
    'No hay pruebas de escritura, velocidad de disco, restauración ni conexión Telegram/OpenRouter.',
    'No se consultan UUID/seriales, IP, puertos, variables de procesos ni argumentos de servicios.',
    'Las evidencias de scripts no certifican cobertura, periodicidad efectiva ni retención: pueden usar variables, includes o exclusiones.',
    'No se decide automáticamente política de copias, propietario del futuro bot ni conservación de notas eliminadas.',
]
report['duracion_segundos'] = round(time.monotonic() - START, 1)
print(json.dumps(report, ensure_ascii=True, indent=2))
PY
