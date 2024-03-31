import datetime as dt
import dataclasses as dc

from sundash import App as _App
from sundash import Component
from sundash import on


from sundash.scheduler import SchedulerMixin, EVERY_SECOND


class App(SchedulerMixin, _App): ...


app = App()


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


def run():
    app.run_sync(['<h1>🕰️ Clock</h1>', Clock])


if __name__ == '__main__':
    run()
