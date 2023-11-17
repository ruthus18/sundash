import datetime as dt

from sundash.core import EVERY_SECOND
from sundash.core import App
from sundash.core import Component

app = App()


now = lambda: dt.datetime.now().strftime('%H:%M:%S')


class Clock(Component):
    html = '<p><b>Time: </b> {{ time }}<p/>'

    class Vars:
        time: str = now

    # @app.on(EVERY_SECOND)
    # async def update(self, _):
    #     await self.set('time', now())


app.run(layout=['<h1>Clock Test</h1>', Clock()])
