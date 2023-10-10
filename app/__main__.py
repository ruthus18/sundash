import datetime as dt

from sundash import Component
from sundash import Signal as sig
from sundash import Sundash
from sundash import Var

sun_app = Sundash()


class CurrentTime(Component):
    html = '<p style="padding: 30px">{{ value }}<p/>'

    # Каждый инстанс должен хранить эти переменные в памяти и восстанавливать
    value: Var[dt.time] = None

    @sun_app.on(sig.EVERY_SECOND)
    def update(self):
        self.value = dt.time.now()


sun_app.attach_to_layout(CurrentTime())
sun_app.run()
