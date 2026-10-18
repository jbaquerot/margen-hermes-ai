from pathlib import Path
import itertools
import pytest
from margen.storage import Store
from margen.application import Application
from margen.domain import Event


class Harness:
    def __init__(self, path):
        self.store = Store(path)
        self.app = Application(self.store,owner='1',chat='1',bot='2')
        self.ids = itertools.count(1)

    def send(self, text, message=None):
        return self.app.handle(Event('2','1','1',str(message or next(self.ids)),text))

    def activate(self, title='Libro A', author='Autora A'):
        self.send(f'/libro {title} | {author}')
        self.send(f'/activar {title}')


@pytest.fixture
def h(tmp_path):
    harness = Harness(tmp_path/'data.db')
    yield harness
    harness.store.close()
