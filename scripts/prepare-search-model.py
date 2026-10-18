#!/usr/bin/env python3
"""Explicit artifact download; the search runtime never downloads anything."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
import urllib.request
p=argparse.ArgumentParser(description='Descargar el modelo E5 aprobado y verificar hashes fijados')
p.add_argument('destination',type=Path)
a=p.parse_args()
spec=json.loads((Path(__file__).resolve().parents[1]/'deployment/search-artifacts.json').read_text())
if a.destination.exists():
    p.error('El destino debe ser nuevo; no se reemplaza un modelo en uso')
a.destination.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
with tempfile.TemporaryDirectory(dir=a.destination.parent,prefix='.e5-') as tmp:
    root=Path(tmp)
    hashes={}
    for local,item in spec['files'].items():
        url=f"https://huggingface.co/{spec['model']}/resolve/{spec['revision']}/{item['path']}"
        h=hashlib.sha256()
        size=0
        with urllib.request.urlopen(url,timeout=120) as stream, (root/local).open('xb') as out:
            while block:=stream.read(1024*1024):
                out.write(block)
                h.update(block)
                size+=len(block)
        if h.hexdigest()!=item['sha256'] or size!=item['size']:
            raise ValueError('Hash o tamaño del artefacto incorrecto: '+local)
        hashes[local]=h.hexdigest()
    (root/'manifest.json').write_text(json.dumps({**spec,'files':hashes},indent=2)+'\n')
    # Rename whole directory only after every artifact passes verification.
    os.rename(root,a.destination)
print('Modelo preparado; la búsqueda puede ejecutarse sin red.')
