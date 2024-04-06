from dataclasses import dataclass

from sundash import App
from sundash import Component
from sundash import on
from sundash.app import ButtonClick

app = App()


class Counter(Component):
    btn_minus = '<button id="minus">-</button>'
    btn_plus = '<button id="plus">+</button>'
    html = btn_minus + '<b>{{ count }}</b>' + btn_plus

    @dataclass
    class Vars:
        count: int = 0

    @on(ButtonClick)
    async def on_click(self, event: ButtonClick):
        if 'plus' == event.button_id:
            self.vars.count += 1

        elif 'minus' == event.button_id:
            self.vars.count -= 1

        await self.update_var('count')


app.run_sync(['<h1>🧮 Counter</h1>', Counter])
