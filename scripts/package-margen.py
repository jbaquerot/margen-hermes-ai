#!/usr/bin/env python3
"""Allowlist-only deterministic release; never packages the workspace wholesale."""
import hashlib
import io
import json
from pathlib import Path
import tarfile
ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'dist'
DEST.mkdir(exist_ok=True)
files=[]
for name in ('plugins/margen','profile','deployment','docs','scripts','tests','.specify'):
    files.extend(p for p in (ROOT/name).rglob('*') if p.is_file())
files.extend(ROOT/name for name in ('README.md','pyproject.toml','requirements-runtime.lock','.gitignore'))
files=sorted({p for p in files if '__pycache__' not in p.parts
              and p.suffix not in ('.pyc','.db','.log') and p.name!='release-manifest.json'})
allowed={'.py','.sql','.yaml','.md','.json','.sh','.lock','.example','.gitignore','.toml'}
files=[p for p in files if p.suffix in allowed or p.name=='.gitignore']
manifest={'version':'0.1.0','schema':1,'hermes_revision':'22063fc099ec9ad8357d7f8f6e6248a0400680d3',
          'python_target':'3.14.7','python_domain_tests':'3.11.15','platform_target':'Linux aarch64 Debian 13',
          'runtime_validation':'Raspberry Docker lab verified; definitive promotion and full acceptance pending; see docs/validation.md',
          'files':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
data=json.dumps(manifest,indent=2).encode()+b'\n'
(ROOT/'docs/release-manifest.json').write_bytes(data)
with tarfile.open(DEST/'margen-0.1.0.tar','w') as archive:
    for p in files:
        content=p.read_bytes()
        item=tarfile.TarInfo('margen-0.1.0/'+str(p.relative_to(ROOT)))
        item.size=len(content)
        item.mode=0o644
        archive.addfile(item,io.BytesIO(content))
    item=tarfile.TarInfo('margen-0.1.0/docs/release-manifest.json')
    item.size=len(data)
    item.mode=0o644
    archive.addfile(item,io.BytesIO(data))
print(DEST/'margen-0.1.0.tar')
