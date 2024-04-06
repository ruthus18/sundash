import dataclasses as dc
import datetime as dt

from sundash import Component
from sundash import on
from sundash.scheduler import EverySecond
from sundash.scheduler import SchedulerApp

app = SchedulerApp()


now = lambda: dt.datetime.now().strftime('%H:%M:%S')


class Clock(Component):
    html = '<p><b>Time:</b> {{ time }}<p/>'

    @dc.dataclass
    class Vars:
        time: str = dc.field(default_factory=now)

    @on(EverySecond)
    async def update(self, _):
        self.vars.time = now()
        await self.update_var('time')


app.run_sync(['<h1>🕰️ Clock</h1>', Clock])
