from .domain import Response, display_date
from .books import label


def render(payload):
    book = payload['book']
    parts = [f"# {book['title']}", f"Autor: {book['author']}"]
    for n in payload['notes']:
        parts.append(f"## {n['ref']}\n\nGuardada: {display_date(n['created_at'])}\n\n{n['text']}")
    return Response('Exportación de ' + label(book), [n['ref'] for n in payload['notes']],
                    filename=f"margen-{book['id']}.md", document='\n\n'.join(parts) + '\n')
