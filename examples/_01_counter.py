from dataclasses import dataclass

from sundash import App
from sundash import Component
from sundash import on
from sundash.core import BUTTON_CLICK

app = App()


class Counter(Component):
    html = '<b>{{ count }}</b> <button id="b-plus">+</button>'

    @dataclass
    class Vars:
        count: int = 0

    @on(BUTTON_CLICK)
    async def update(self, _):
        await self.set('count', self.vars['count'] + 1)


app.run(layout=('<h1>🧮 Counter</h1>', Counter))
