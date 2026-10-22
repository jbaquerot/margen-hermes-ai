#!/usr/bin/env python3
"""Promote the existing isolated volume; never prints Docker inspect secrets."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
COMPOSE = ROOT / 'deployment/docker/compose.production.yaml'
PARAMETERS = ROOT / 'deployment/docker/.env.production'
LAB = 'margen-lab-supervised-gateway'
SERVICE = 'margen'
IMAGE = 'margen-hermes-lab:22063fc099ec'
VOLUME = 'margen-hermes-lab_data'
REVISION = '22063fc099ec9ad8357d7f8f6e6248a0400680d3'
PARAMETER_KEYS = {'MARGEN_UID', 'MARGEN_GID', 'MARGEN_DATA_VOLUME'}


class Deployment:
    def __init__(self, *, sudo=False):
        self.prefix = ['sudo', 'docker'] if sudo else ['docker']

    def docker(self, *args, env=None, capture=True):
        result = subprocess.run(self.prefix + list(args), check=True, text=True,
                                stdout=subprocess.PIPE if capture else None,
                                env=env)
        return result.stdout.strip() if capture else ''

    def inspect(self, name):
        return json.loads(self.docker('inspect', name))[0]

    @staticmethod
    def mounted_volume(container):
        matches = [m for m in container.get('Mounts', []) if m.get('Destination') == '/opt/data']
        if len(matches) != 1 or matches[0].get('Type') != 'volume':
            raise RuntimeError('Se requiere un único volumen Docker en /opt/data.')
        return matches[0]['Name']

    def consumers(self, volume):
        return set(self.docker('ps', '--filter', 'volume=' + volume,
                               '--format', '{{.Names}}').splitlines())

    def compose(self, params, *args, capture=True):
        return self.docker('compose', '--project-name', 'margen', '-f', str(COMPOSE), *args,
                           env={**os.environ, **params}, capture=capture)

    def preflight(self):
        lab = self.inspect(LAB)
        if not lab['State']['Running']:
            raise RuntimeError('El laboratorio supervisado debe estar funcionando antes del cambio.')
        volume = self.mounted_volume(lab)
        if volume != VOLUME:
            raise RuntimeError('El volumen no coincide con el laboratorio validado; no se modifica nada.')
        if self.consumers(volume) != {LAB}:
            raise RuntimeError('Hay otra instancia usando el volumen; no se modifica nada.')
        if self.docker('ps', '-a', '--filter', 'name=^/' + SERVICE + '$', '--format', '{{.ID}}'):
            raise RuntimeError('Ya existe el contenedor margen; revisar su estado antes de desplegar otra vez.')
        image = json.loads(self.docker('image', 'inspect', IMAGE))[0]
        if image['Id'] != lab['Image'] or (image['Os'], image['Architecture']) != ('linux', 'arm64'):
            raise RuntimeError('La imagen local no coincide con la imagen ARM64 del laboratorio.')
        if (image.get('Config', {}).get('Labels') or {}).get('org.opencontainers.image.revision') != REVISION:
            raise RuntimeError('La etiqueta de revisión de la imagen no coincide con Hermes aprobado.')
        # Inspect may contain credentials. Select these three non-secret values only.
        values = dict(item.split('=', 1) for item in lab['Config']['Env'] if '=' in item)
        uid, gid = values.get('HERMES_UID', ''), values.get('HERMES_GID', '')
        if not uid.isdecimal() or not gid.isdecimal() or int(uid) == 0:
            raise RuntimeError('No se ha podido comprobar el UID/GID no root del laboratorio.')
        params = {'MARGEN_UID': uid, 'MARGEN_GID': gid, 'MARGEN_DATA_VOLUME': volume}
        self.compose(params, 'config', '--quiet')
        return params

    @staticmethod
    def save_parameters(params):
        # Only non-secret numeric IDs and the already checked volume name, mode 0600.
        with tempfile.NamedTemporaryFile(mode='w', dir=PARAMETERS.parent, delete=False) as stream:
            temporary = Path(stream.name)
            try:
                for key in sorted(PARAMETER_KEYS):
                    stream.write(key + '=' + params[key] + '\n')
                stream.flush()
                os.fsync(stream.fileno())
                os.replace(temporary, PARAMETERS)
            finally:
                temporary.unlink(missing_ok=True)

    @staticmethod
    def load_parameters():
        params = dict(line.split('=', 1) for line in PARAMETERS.read_text().splitlines() if line)
        if (set(params) != PARAMETER_KEYS or params['MARGEN_DATA_VOLUME'] != VOLUME
                or not params['MARGEN_UID'].isdecimal() or int(params['MARGEN_UID']) == 0
                or not params['MARGEN_GID'].isdecimal()):
            raise RuntimeError('Parámetros locales de despliegue no válidos.')
        return params

    def backup(self, container):
        if self.mounted_volume(self.inspect(container)) != VOLUME:
            raise RuntimeError('No se crea copia: el contenedor usa otro volumen.')
        self.docker('exec', '--user', 'hermes', '-e',
                    'PYTHONPATH=/opt/hermes:/opt/data/profiles/margen/plugins/margen',
                    container, '/opt/hermes/.venv/bin/python', '-c',
                    'import hermes_bootstrap; from margen.backup import snapshot; '
                    'snapshot("/opt/data/profiles/margen/plugin-data/margen/data.db", '
                    '"/opt/data/profiles/margen/plugin-data/margen/current.tar")')
        print('Instantánea SQLite local verificada.', flush=True)

    def deploy(self):
        params = self.preflight()
        self.save_parameters(params)
        self.backup(LAB)
        self.docker('stop', '--time', '60', LAB)
        try:
            if self.consumers(VOLUME):
                raise RuntimeError('El volumen sigue en uso; se cancela el arranque definitivo.')
            self.compose(params, 'up', '-d', '--pull', 'never', '--wait',
                         '--wait-timeout', '180', 'hermes', capture=False)
        except (subprocess.CalledProcessError, RuntimeError, KeyboardInterrupt):
            # Only restart the laboratory after the replacement is certainly stopped.
            self.compose(params, 'stop', 'hermes')
            if self.consumers(VOLUME):
                raise RuntimeError('Recuperación detenida: queda una instancia activa; revisar Docker.')
            self.docker('start', LAB)
            print('El arranque definitivo falló; laboratorio arrancado de nuevo. Revisar sus logs.', flush=True)
            raise
        print('Servicio margen arrancado; gateway y estado Telegram comprobados.', flush=True)
        print('Verificar /libros en Telegram. La aceptación completa sigue pendiente.')

    def rollback(self):
        params = self.load_parameters()
        if self.mounted_volume(self.inspect(SERVICE)) != VOLUME or self.mounted_volume(self.inspect(LAB)) != VOLUME:
            raise RuntimeError('Los volúmenes no coinciden; se cancela la reversión.')
        if self.consumers(VOLUME) - {SERVICE}:
            raise RuntimeError('Otra instancia usa los datos; se cancela la reversión.')
        self.compose(params, 'stop', 'hermes')
        if self.consumers(VOLUME):
            raise RuntimeError('El servicio no se ha detenido; no se arranca el laboratorio.')
        self.docker('start', LAB)
        print('Laboratorio arrancado con el volumen conservado; comprobar Telegram.')
        print('Esto revierte el arranque, no el código del plugin ni los datos.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sudo', action='store_true', help='Ejecutar Docker mediante sudo')
    parser.add_argument('action', choices=['check', 'deploy', 'status', 'backup', 'rollback'])
    args = parser.parse_args()
    deployment = Deployment(sudo=args.sudo)
    try:
        if args.action == 'check':
            params = deployment.preflight()
            print('Preflight correcto. Volumen:', params['MARGEN_DATA_VOLUME'])
            print('Imagen ARM64 y UID/GID coinciden con el laboratorio; todavía no se ha cambiado el servicio.')
        elif args.action == 'deploy':
            deployment.deploy()
        elif args.action == 'rollback':
            deployment.rollback()
        elif args.action == 'backup':
            deployment.backup(SERVICE)
        else:
            deployment.compose(deployment.load_parameters(), 'ps', capture=False)
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.CalledProcessError) as exc:
        # Never print captured inspect/config JSON or exception payloads from Docker.
        if isinstance(exc, RuntimeError):
            parser.exit(1, str(exc) + '\n')
        parser.exit(1, 'La operación Docker no terminó correctamente; revisar el estado y los logs del servicio.\n')


if __name__ == '__main__':
    main()
