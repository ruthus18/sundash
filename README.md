# Sundash

**Python & JS micro framework for realtime web UI applications**

* **ASGI-based** -- minimal 3rd party dependencies and clean core part
* **Flexible and extensible** -- easy to customize, add 3rd party integrations
* **Realtime** -- operating through websockets bus, client & backend in app
* **Crafted with ❤️**

Link to project on PyPi: https://pypi.org/project/sundash/


### Installation

```bash
    pip install sundash
```


### Examples

```bash
    python -m examples <num | name>
```

To run Hello World example:

```bash
    python -m examples hello  # passing 01 also works
```

Available examples:

* `01 hello` - show plain HTML string
* `02 buttons` - counter with clickable buttons
* `03 clock` - realtime clock (scheduler events)
* `04 menu` - simple page routing
* `05 search` - handling signle form input
* `06 tables` - static tables


**Client interaction example:**

```python
from dataclasses import dataclass

from sundash import App
from sundash import Component
from sundash import on
from sundash.app import ButtonClick

app = App()


class Counter(Component):
    html = '''
        <button id="minus">-</button>
        <b>{{ count }}</b>
        <button id="plus">+</button>
    '''

    @dataclass
    class Vars:
        count: int = 0

    @on(ButtonClick)
    async def on_click(self, event: ButtonClick):
        if 'plus' == event.button_id:
            self.vars.count += 1

        elif 'minus' == event.button_id:
            self.vars.count -= 1

        await self.update_var('count')


app.run_sync(['<h1>🧮 Counter</h1>', Counter])
```


**Server Interaction Example:**

```python
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
```


### В чем идея?

Хочу пробрасывать real-time интерфейс к JS либам, чтобы была возможность
написать любую веб-морду для любых системных инструментов.

**Примеры использования:** любые админки, торговые терминалы, дашборды мониторинга, тулзы для аналитики.
Все кастомное и интерактивное, что хочется нарисовать, но ты бэкендер и хочешь писать
преимущественно на Python с минимальным использованием JavaScript-а,
без тяжеловесного инструментария фронтендеров (React и пр).


### Development

* Required: python 3.12, poetry, virtualenv
* Install Python dependencies: `poetry install --with=dev`
* Run local linters: `poe q`
* Publish package: `poetry publish --build`
