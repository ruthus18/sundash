import dataclasses as dc
import datetime as dt

from sundash import Component
from sundash import on
from sundash.scheduler import EVERY_SECOND
from sundash.scheduler import SchedulerApp

app = SchedulerApp()


now = lambda: dt.datetime.now().strftime('%H:%M:%S')


class Clock(Component):
    html = '<p><b>Time:</b> {{ time }}<p/>'

    @dc.dataclass
    class Vars:
        time: str = dc.field(default_factory=now)

    @on(EVERY_SECOND)
    async def update(self, event: EVERY_SECOND):
        self.vars.time = now()
        await self.update_var('time', event=event)


app.run_sync(['<h1>🕰️ Clock</h1>', Clock])
