#!/usr/bin/env python3
"""Synthetic-only E5 evaluation; no live notes or external inference."""
import argparse
import json
from pathlib import Path
import platform
import resource
import tempfile
import time
from margen.application import Application
from margen.domain import Event
from margen.storage import Store
from margen.embeddings import LocalE5
from margen.search import search
p=argparse.ArgumentParser()
p.add_argument('model_dir')
p.add_argument('--output',required=True,type=Path)
a=p.parse_args()
root=Path(__file__).resolve().parents[1]/'tests/fixtures'
fixture=json.loads((root/'reading_notes.json').read_text())
queries=json.loads((root/'search_queries.json').read_text())
started=time.perf_counter()
encoder=LocalE5(a.model_dir)
load_seconds=time.perf_counter()-started
with tempfile.TemporaryDirectory(prefix='margen-eval-') as tmp:
    store=Store(Path(tmp)/'data.db')
    app=Application(store,owner='synthetic',chat='test',bot='test')
    counter=0
    def send(text):
        global counter
        counter+=1
        return app.handle(Event('test','synthetic','test',str(counter),text))
    ids={}
    for book in fixture['books']:
        send('/libro '+book['title']+' | '+book['author'])
        row=store.db.execute('SELECT id FROM books WHERE title=? AND author=?',(book['title'],book['author'])).fetchone()
        ids[book['key']]=row[0]
    refs={}
    for note in fixture['notes']:
        with store.transaction() as db:
            book=ids.get(note['book'])
            db.execute('INSERT INTO reading_state VALUES(?,?) ON CONFLICT(owner) DO UPDATE SET book=excluded.book',('synthetic',book))
        refs[note['key']]=send('/nota '+note['text']).refs[0]
    reverse={v:k for k,v in refs.items()}
    results=[]
    for q in queries['queries']:
        start=time.perf_counter()
        found=search(store,encoder,'synthetic',q['description']).refs
        results.append({'query':q['description'],'expected':q['expected'],
            'top5':[reverse[r] for r in found],'hit':refs[q['expected']] in found,
            'seconds':time.perf_counter()-start})
    negative=[{'query':q,'top5':[reverse[r] for r in search(store,encoder,'synthetic',q).refs]} for q in queries['negative']]
    store.close()
report={'model_revision':encoder.revision,'platform':platform.platform(),'machine':platform.machine(),
    'python':platform.python_version(),'threshold':0.83,'load_seconds':load_seconds,
    'max_rss_native_units':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    'rss_unit':'bytes on macOS; KiB on Linux','hits':sum(r['hit'] for r in results),'total':10,
    'passed_local_quality':sum(r['hit'] for r in results)>=8,'results':results,'negative':negative}
a.output.parent.mkdir(parents=True,exist_ok=True)
a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(f"{report['hits']}/10; {report['machine']}; evidence: {a.output}")
