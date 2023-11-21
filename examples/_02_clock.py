import datetime as dt
from dataclasses import dataclass

from sundash import App
from sundash import Component
from sundash import on
from sundash.core import EVERY_SECOND

app = App()


now = lambda: dt.datetime.now().strftime('%H:%M:%S')


# FIXME: not working, need to implement dynamic vars and scheduler
class Clock(Component):
    html = '<p><b>Time:</b> {{ time }}<p/>'

    @dataclass
    class Vars:
        time: str = now

    @on(EVERY_SECOND)
    async def update(self, _):
        await self.set('time', now())


run = lambda: app.run(layout=('<h1>🕰️ Clock</h1>', Clock))


if __name__ == '__main__':
    run()
