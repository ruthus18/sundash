# Sundash

**Python & JS micro framework for realtime web UI applications**

* **ASGI-based** -- minimal 3rd party dependencies and clean core part
* **Flexible and extensible** -- easy to embed to existing ASGI server, extend core part, add 3rd party integrations
* **Realtime** -- operating through websockets bus, callback-based client <-> server communication
* **Crafted with ❤️**


**Usage:** check `examples` folder

To run example, create a file `test.py`:

```python
from examples._01_clock import app
from sundash.core import run

run(app)
```

And run:

```bash
python -m test
```


### В чем идея?

Хочу пробрасывать real-time интерфейс к JS либам, чтобы была возможность
написать любую веб-морду для любых системных инструментов.

**Примеры использования:** любые админки, торговые терминалы, дашборды мониторинга, тулзы для аналитики.
Все кастомное и интерактивное, что хочется нарисовать, но ты бэкендер и хочешь писать
преимущественно на Python с минимальным использованием JavaScript-а,
без тяжеловесного инструментария фронтендеров (React и пр).


### Basic example

```python
import datetime as dt

from sundash.bus import EVERY_SECOND
from sundash.core import App
from sundash.core import Component
from sundash.core import Var
from sundash.core import run

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

run(app)
```

![clock](docs/example_01_clock.png "Clock")
