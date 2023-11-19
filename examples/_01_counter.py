from dataclasses import dataclass

from sundash import App
from sundash import Component
from sundash import on
from sundash.core import BUTTON_CLICK
from sundash.server import get_connection

app = App()


class Counter(Component):
    btn_minus = '<button id="minus">-</button>'
    btn_plus = '<button id="plus">+</button>'
    html = '   '.join((btn_minus, '<b>{{ count }}</b>', btn_plus))

    @dataclass
    class Vars:
        count: int = 0

    def __init__(self):
        super().__init__()
        self.conn_id = get_connection().id

    @on(BUTTON_CLICK)
    async def update(self, sig: BUTTON_CLICK):
        conn_id = get_connection().id
        if conn_id != self.conn_id:
            return

        if 'plus' == sig.button_id:
            self.vars['count'] += 1

        elif 'minus' == sig.button_id:
            self.vars['count'] -= 1

        await self.set('count', self.vars['count'])


app.run(layout=('<h1>🧮 Counter</h1>', Counter))
