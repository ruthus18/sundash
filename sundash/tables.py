import os

from .core import HTML
from .layout import Component

__all__ = ('Table', )

DIR = os.path.dirname(__file__)


class Table(Component):
    type Data = tuple[tuple[str], ...]

    init_data: Data = []

    def __init__(self):
        super().__init__()
        self.html = render_table(self.init_data)


table = lambda c: f'<table>{c}</table>'
th = lambda c: f'<th>{c}</th>'
td = lambda c: f'<td>{c}</td>'

tr = lambda cc: f'<tr>{''.join(c for c in cc)}</tr>'
tr_th = lambda cc: tr(th(c) for c in cc)
tr_td = lambda cc: tr(td(c) for c in cc)


def render_table(data: Table.Data) -> HTML:
    headers, items = data[0], data[1:]

    html_headers = tr_th(name.capitalize() for name in headers)
    html_items = ''

    for item in items:
        html_items += tr_td(value for value in item)

    return table(html_headers + html_items)
