#!/usr/bin/env python3
"""Run with the installed Margen package; no credentials or sudo required."""
import argparse
from margen.backup import snapshot, transfer
p=argparse.ArgumentParser(description='Instantánea actual consistente de Margen')
p.add_argument('--database',required=True)
p.add_argument('--snapshot',required=True,help='Archivo .tar actual, fuera del SSD')
p.add_argument('--mount',help='Punto de montaje exacto; no se intenta montar')
p.add_argument('--expected-source',help='Dispositivo estable /dev/disk/by-uuid/...')
a=p.parse_args()
if bool(a.mount) != bool(a.expected_source):
    p.error('--mount y --expected-source deben indicarse juntos')
snapshot(a.database,a.snapshot)
if a.mount:
    transfer(a.snapshot,a.mount,a.expected_source)
print('Instantánea verificada'+('; transferencia verificada' if a.mount else '; sin transferencia'))
