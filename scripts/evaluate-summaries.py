#!/usr/bin/env python3
"""Generate synthetic review cases through a running Hermes PluginContext.

No direct OpenRouter client or API keys: import build_cases from a test harness
that provides the real plugin ctx. Running this script only prints the rubric.
"""
import json
from pathlib import Path
from margen.summaries import generate
from margen.model import HermesModel
ROOT=Path(__file__).resolve().parents[1]/'tests/fixtures'

async def build_cases(ctx):
    fixture=json.loads((ROOT/'reading_notes.json').read_text())
    expectations=json.loads((ROOT/'summary_expectations.json').read_text())
    for book in fixture['books']:
        selected=[n for n in fixture['notes'] if n['book']==book['key']]
        for mode in ('brief','detailed'):
            payload={'book':book,'mode':mode,'notes':[{'ref':n['key'],'text':n['text']} for n in selected]}
            yield {'book':book,'mode':mode,'sources':selected,
                   'summary':await generate(HermesModel(ctx),payload),
                   'expectations':next(e for e in expectations['books'] if e['book']==book['key']),
                   'human_review':{'all_principal_ideas':None,'order':None,'no_unsupported_claims':None,
                                   'quotes_and_reflections':None,'no_invented_pages':None}}

if __name__=='__main__':
    print('Revisar ambos modos por libro con PluginContext real; todas las ideas, orden, fidelidad, citas y vacíos. Ningún aprobado automático sustituye la revisión humana. Ver docs/summary-evaluation.md.')
