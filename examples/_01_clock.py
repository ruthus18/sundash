import datetime as dt

from sundash import App
from sundash import Component
from sundash import Var
from sundash.bus import EVERY_SECOND

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

app.run()
