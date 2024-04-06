from .app import Component
from .core import HTML

type _DatasheetRow = tuple[str, ...]

# first row using as data header
type _Datasheet = tuple[_DatasheetRow, ...]


TABLE = '<table>{}</table>'
TH = '<th>{}</th>'
TD = '<td>{}</td>'
TR = '<tr>{}</tr>'


def tr(items: list[HTML]) -> HTML:
    return TR.format(''.join(items))


def render_table(data: _Datasheet) -> HTML:
    headers, *rows = data

    html_headers = tr(TH.format(item) for item in headers)
    html_items = ''
    for row in rows:
        html_items += tr(TD.format(item) for item in row)

    return TABLE.format(html_headers + html_items)


# Framework adapter


class Table(Component):
    table_data: _Datasheet = None

    def __init__(self):
        super().__init__()
        if self.table_data is None:
            raise ValueError('`table_data` param is missing')

        self.html = render_table(self.table_data)
