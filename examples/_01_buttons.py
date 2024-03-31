from dataclasses import dataclass

from sundash import on
from sundash import App
from sundash import Component
from sundash.app import BUTTON_CLICK


class Counter(Component):
    btn_minus = '<button id="minus">-</button>'
    btn_plus = '<button id="plus">+</button>'
    html = btn_minus + '<b>{{ count }}</b>' + btn_plus

    @dataclass
    class Vars:
        count: int = 0

    @on(BUTTON_CLICK)
    async def on_click(self, event: BUTTON_CLICK):
        if 'plus' == event.button_id:
            self.vars.count += 1

        elif 'minus' == event.button_id:
            self.vars.count -= 1

        await self.update_var('count', event=event)


def run():
    App().run_sync(['<h1>🧮 Counter</h1>', Counter])


if __name__ == '__main__':
    run()
