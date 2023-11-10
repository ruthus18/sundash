import datetime as dt

from sundash.bus import EVERY_SECOND
from sundash.core import App
from sundash.core import Component
from sundash.core import Var

app = App()


now = lambda: dt.datetime.now().strftime('%H:%M:%S')


class Clock(Component):
    html = '<p><b>Time: </b> {{ time }}<p/>'

    time: Var[str] = now

    @app.on(EVERY_SECOND)
    async def update(self, _):
        await self.set('time', now())


app.attach_to_layout('<h1>Clock Test</h1>')
app.attach_to_layout(Clock())
