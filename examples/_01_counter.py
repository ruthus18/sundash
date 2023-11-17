from sundash.core import BUTTON_CLICK
from sundash.core import App
from sundash.core import Component
from sundash.core import on

app = App()


class Counter(Component):
    _btn = '<button id="b-plus">+</button>'
    html = '<b>{{ count }}</b>' + _btn

    class Vars:
        count: int = 0

    @on(BUTTON_CLICK)
    async def update(self, sig: BUTTON_CLICK):
        await self.set('count', self.Vars.count + 1)


app.run(layout=('<h1>Counter</h1>', Counter()))
