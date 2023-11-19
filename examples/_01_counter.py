from dataclasses import dataclass

from sundash import App
from sundash import Component
from sundash import on
from sundash.core import BUTTON_CLICK
from sundash.server import get_connection

app = App()


class Counter(Component):
    html = '<b>{{ count }}</b> <button id="{{ conn_id }}">+</button>'

    @dataclass
    class Vars:
        conn_id: int
        count: int = 0

    def __init__(self):
        conn_id = get_connection().id
        self.vars: dict = self.Vars(conn_id).__dict__

    @on(BUTTON_CLICK)
    async def update(self, _):
        conn_id = get_connection().id
        if conn_id != self.vars['conn_id']:
            return

        await self.set('count', self.vars['count'] + 1)


app.run(layout=('<h1>🧮 Counter</h1>', Counter))
