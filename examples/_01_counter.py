from dataclasses import dataclass

from sundash import App
from sundash import Component
from sundash.app import BUTTON_CLICK

app = App()
on = app.on


class Counter(Component):
    btn_minus = '<button id="minus">-</button>'
    btn_plus = '<button id="plus">+</button>'
    html = btn_minus + '<b>{{ count }}</b>' + btn_plus

    @dataclass
    class Vars:
        count: int = 0

    @on(BUTTON_CLICK)
    async def update(self, sig: BUTTON_CLICK):
        if 'plus' == sig.button_id:
            self.vars['count'] += 1

        elif 'minus' == sig.button_id:
            self.vars['count'] -= 1

        await self.set('count', self.vars['count'])


def run():
    app.run_sync(['<h1>🧮 Counter</h1>', Counter])


if __name__ == '__main__':
    run()
