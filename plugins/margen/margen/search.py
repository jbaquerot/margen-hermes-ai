import json
import math
import re
from .domain import Response
from . import notes
from .indexing import ensure_index


# Function words must not outweigh semantic matches in reciprocal-rank fusion.
STOPWORDS = frozenset("a al algo ante antes como cómo con contra cuando cuál de del desde donde dónde dos el ella en entre era es esa ese eso esta este esto ha hay la las le les lo los más me mi muy ni no nos o para pero por porque porqué por qué que qué recuerdo se ser si sí sin sobre son y e u su sus te tengo tiene todo tras tu un una unas unos volver ya yo".split())


def cosine(a,b):
    denom = math.sqrt(sum(x*x for x in a) * sum(x*x for x in b))
    return sum(x*y for x,y in zip(a,b)) / denom if denom else 0


def search(store, embedder, owner, query, *, threshold=0.83):
    ensure_index(store, embedder, owner)
    vectors = embedder.encode(embedder.chunks(query), query=True)
    with store.transaction() as db:
        rows = db.execute("SELECT c.ref,e.vector FROM note_chunks c JOIN note_embeddings e ON e.chunk=c.id JOIN notes n ON n.ref=c.ref WHERE n.owner=? AND c.version=n.version AND e.revision=?", (owner, embedder.revision)).fetchall()
        # A mutation during embedding must not silently yield an incomplete search.
        pending = db.execute("SELECT 1 FROM notes n JOIN index_jobs j ON j.ref=n.ref WHERE owner=? LIMIT 1", (owner,)).fetchone()
        if pending:
            raise RuntimeError("Las notas cambiaron durante la búsqueda. Repite /buscar para actualizar el índice.")
        scores = {}
        for row in rows:
            score = max(cosine(v,json.loads(row['vector'])) for v in vectors)
            scores[row['ref']] = max(scores.get(row['ref'], -1),score)
        semantic = sorted((r for r,s in scores.items() if s >= threshold), key=lambda r:(-scores[r],r))
        words = [w for w in re.findall(r'\w+',query.casefold(), re.UNICODE) if w not in STOPWORDS]
        lexical = []
        if words:
            expression = ' OR '.join('"'+w+'"' for w in words)
            lexical = [r[0] for r in db.execute("SELECT f.ref FROM notes_fts f JOIN notes n ON n.ref=f.ref WHERE notes_fts MATCH ? AND n.owner=? ORDER BY bm25(notes_fts)", (expression,owner))]
        fused = {}
        # Lexical matches are candidates but do not override the semantic floor.
        for weight, ranking in ((1.0, semantic), (0.2, [r for r in lexical if r in semantic])):
            for rank, ref in enumerate(ranking,1):
                fused[ref] = fused.get(ref,0) + weight/(10+rank)
        refs = sorted(fused,key=lambda r:(-fused[r],r))
        db.execute("INSERT INTO search_sessions VALUES(?,?,0) ON CONFLICT(owner) DO UPDATE SET refs=excluded.refs,cursor=0", (owner,json.dumps(refs)))
        return page(db,owner)


def page(db, owner):
    row = db.execute("SELECT refs,cursor FROM search_sessions WHERE owner=?", (owner,)).fetchone()
    if not row:
        return Response("No hay una búsqueda previa. Usa /buscar descripción.")
    refs, cursor = json.loads(row['refs']), row['cursor']
    output, shown = [], []
    while cursor < len(refs) and len(output) < 5:
        ref = refs[cursor]
        cursor += 1
        current = db.execute("SELECT * FROM notes WHERE ref=? AND owner=?", (ref,owner)).fetchone()
        if current:
            shown.append(ref)
            output.append(notes.describe(db,owner,current))
    db.execute("UPDATE search_sessions SET cursor=? WHERE owner=?", (cursor,owner))
    suffix = '\n/mas para más resultados.' if cursor < len(refs) else '\nNo hay más resultados.'
    return Response(('Posibles coincidencias:\n\n' + '\n\n'.join(output) if output else 'No hay coincidencias adicionales respaldadas por las notas.') + suffix, shown)
