"""Failure-ordering checks: never start two pollers or lose the lab on startup failure."""
import importlib.util
import json
from pathlib import Path
import subprocess
import pytest

spec = importlib.util.spec_from_file_location('docker_deploy', Path('scripts/deploy-docker-margen.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class Docker(module.Deployment):
    def __init__(self, *, startup_fails=False, backup_fails=False, competing=False):
        self.calls = []
        self.active = {module.LAB} | ({'other-poller'} if competing else set())
        self.startup_fails, self.backup_fails = startup_fails, backup_fails
        self.volume = module.VOLUME

    def docker(self, *args, **kwargs):
        self.calls.append(args)
        if args[0] == 'inspect':
            return json.dumps([{'State': {'Running': args[1] in self.active}, 'Image': 'image-id',
                'Mounts': [{'Destination':'/opt/data','Type':'volume','Name':self.volume}],
                'Config': {'Env':['HERMES_UID=1000','HERMES_GID=1000','SECRET=DO_NOT_PRINT']}}])
        if args[:2] == ('image', 'inspect'):
            return json.dumps([{'Id':'image-id','Os':'linux','Architecture':'arm64',
                'Config': {'Labels':{'org.opencontainers.image.revision':module.REVISION}}}])
        if args[0] == 'ps':
            return '' if '-a' in args else '\n'.join(sorted(self.active))
        if args[0] == 'exec':
            if self.backup_fails:
                raise subprocess.CalledProcessError(1, 'backup')
        elif args[0] == 'stop':
            self.active.discard(args[-1])
        elif args[0] == 'start':
            assert not self.active  # Starting a second poller must never be attempted.
            self.active.add(args[-1])
        elif args[0] == 'compose':
            if 'up' in args:
                assert not self.active
                self.active.add(module.SERVICE)
                if self.startup_fails:
                    raise subprocess.CalledProcessError(1, 'compose up')
            if 'stop' in args:
                self.active.discard(module.SERVICE)
        return ''


@pytest.fixture
def parameters(tmp_path, monkeypatch):
    path = tmp_path/'.env.production'
    monkeypatch.setattr(module, 'PARAMETERS', path)
    return path


def test_promotion_preserves_volume_identity_and_starts_only_after_lab_stops(parameters, capsys):
    docker = Docker()
    docker.deploy()
    assert docker.active == {module.SERVICE}
    assert docker.calls.index(next(c for c in docker.calls if c[0] == 'exec')) < docker.calls.index(('stop','--time','60',module.LAB))
    assert module.Deployment.load_parameters()['MARGEN_DATA_VOLUME'] == module.VOLUME
    assert parameters.stat().st_mode & 0o777 == 0o600
    assert 'SECRET' not in parameters.read_text() + capsys.readouterr().out


def test_failed_start_stops_replacement_before_recovering_lab(parameters):
    docker = Docker(startup_fails=True)
    with pytest.raises(subprocess.CalledProcessError):
        docker.deploy()
    assert docker.active == {module.LAB}
    assert any(c[0] == 'compose' and 'stop' in c for c in docker.calls)


def test_failed_snapshot_leaves_existing_gateway_running(parameters):
    docker = Docker(backup_fails=True)
    with pytest.raises(subprocess.CalledProcessError):
        docker.deploy()
    assert docker.active == {module.LAB}
    assert not any(c[0] in ('stop','start') or 'up' in c for c in docker.calls)


def test_competing_volume_consumer_prevents_all_mutations(parameters):
    docker = Docker(competing=True)
    with pytest.raises(RuntimeError, match='otra instancia'):
        docker.deploy()
    assert not parameters.exists()
    assert not any(c[0] in ('stop','start','exec') or 'up' in c for c in docker.calls)


def test_unexpected_volume_prevents_promotion(parameters):
    docker = Docker()
    docker.volume = 'unrelated-personal-volume'
    with pytest.raises(RuntimeError, match='volumen no coincide'):
        docker.deploy()
    assert not parameters.exists()


def test_rollback_keeps_single_poller_and_does_not_remove_volume(parameters):
    docker = Docker()
    docker.deploy()
    docker.rollback()
    assert docker.active == {module.LAB}
    assert not any('down' in c or 'rm' in c for c in docker.calls)
