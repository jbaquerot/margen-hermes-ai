#!/usr/bin/env python3
import argparse
from margen.backup import restore
p=argparse.ArgumentParser(description='Restaurar solo en un directorio nuevo de cuarentena')
p.add_argument('archive')
p.add_argument('quarantine')
p.add_argument('--current-database',help='Base actual para contrastar eliminaciones posteriores')
a=p.parse_args()
restore(a.archive,a.quarantine,current_database=a.current_database)
print('Cuarentena preparada. Revisión manual obligatoria antes de activar.')
