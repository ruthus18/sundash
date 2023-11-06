import datetime as dt

from sundash.bus import EVERY_SECOND
from sundash.core import App
from sundash.core import Component
from sundash.core import Var
from sundash.core import run

app = App()


class CurrentTime(Component):
    html = '<p style="padding: 30px">{{ value }}<p/>'

    # Каждый инстанс должен хранить эти переменные в памяти и восстанавливать
    value: Var[dt.time] = None

    @app.on(EVERY_SECOND)
    def update(self):
        self.value = dt.time.now()


app.attach_to_layout(CurrentTime())

run(app)
