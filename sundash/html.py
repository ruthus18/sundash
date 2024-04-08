# FIXME
#
#  This module is bad idea. No need to work with HTML from Python, it's not OK
#
#  * For simple cases, HTML can be passed as string to `Component`
#  * For more complex cases, HTML should be set in Jinja-template or frontend

import typing as t
from functools import partial

type HTML = str

type Tag = HTML
type TagItems = t.Iterable[HTML]


BUTTON: Tag = '<button {params}>{inner}</button>'
TABLE: Tag = '<table {params}>{items}</table>'
TR: Tag = '<tr {params}>{items}</tr>'
TH: Tag = '<th {params}>{inner}</th>'
TD: Tag = '<td {params}>{inner}</td>'


def _html_params(params: dict) -> HTML:
    return ''.join('{k}={v} ' for k, v in params.items())


def container_tag(tag: Tag, items: TagItems, **params) -> HTML:
    return tag.format(
        items=''.join(items),
        params=_html_params(params),
    )


def text_tag(tag: Tag, inner: str, **params) -> HTML:
    return tag.format(
        inner=inner,
        params=_html_params(params),
    )


button = partial(text_tag, BUTTON)

table = partial(container_tag, TABLE)
tr = partial(container_tag, TR)
th = partial(text_tag, TH)
td = partial(text_tag, TD)
