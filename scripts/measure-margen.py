#!/usr/bin/env python3
"""Local admission/commit timings only; bot acceptance requires real Telegram."""
import argparse
import json
from pathlib import Path
import platform
import statistics
import tempfile
import time
from margen.application import Application
from margen.domain import Event
from margen.storage import Store
p=argparse.ArgumentParser()
p.add_argument('--samples',type=int,default=100)
a=p.parse_args()
if a.samples<1:
    p.error('--samples debe ser positivo')
with tempfile.TemporaryDirectory(prefix='margen-measure-') as tmp:
    store=Store(Path(tmp)/'data.db')
    app=Application(store,owner='test',chat='test',bot='test')
    def send(i,text):
        return app.handle(Event('test','test','test',str(i),text))
    send(0,'/libro Libro de prueba | Autor ficticio')
    send(1,'/activar Libro de prueba')
    times=[]
    for i in range(a.samples):
        start=time.perf_counter()
        send(i+2,'Nota sintética para medición')
        times.append((time.perf_counter()-start)*1000)
    store.close()
print(json.dumps({'scope':'local admission+commit; excludes Telegram','machine':platform.machine(),
    'python':platform.python_version(),'samples':a.samples,'median_ms':statistics.median(times),
    'p95_ms':sorted(times)[max(0,int(a.samples*.95)-1)],'max_ms':max(times)},indent=2))
