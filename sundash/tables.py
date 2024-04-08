from .app import Component
from .html import HTML
from .html import table
from .html import td
from .html import th
from .html import tr

type _DatasheetRow = tuple[str, ...]
type _Datasheet = tuple[_DatasheetRow, ...]  # first row using as data header


def render_table(data: _Datasheet) -> HTML:
    headers, *rows = data

    html_headers = tr(th(item) for item in headers)
    html_items = [tr(td(item) for item in row) for row in rows]

    return table([html_headers, *html_items])


# Framework adapter

class Table(Component):
    table_data: _Datasheet = None

    def __init__(self):
        super().__init__()
        if self.table_data is None:
            raise ValueError('`table_data` param is missing')

        self.html = render_table(self.table_data)
