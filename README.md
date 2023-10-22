# Sundash

**Python & JS micro framework for realtime web UI applications**

* **ASGI-based** -- minimal 3rd party dependencies and clean core part
* **Flexible and extensible** -- easy to embed to existing ASGI server, extend core part, add 3rd party integrations
* **Realtime** -- operating through websockets bus, callback-based client <-> server communication
* **Crafted with ❤️**

Launch: `python -m app`

~~Check examples~~  *Work in progress, making proto...*


### В чем идея?

Хочу пробрасывать real-time интерфейс к JS либам, чтобы была возможность
написать любую веб-морду для любых системных инструментов.

**Примеры использования:** любые админки, торговые терминалы, дашборды мониторинга, тулзы для аналитики.
Все кастомное и интерактивное, что хочется нарисовать, но ты бэкендер и хочешь писать
преимущественно на Python с минимальным использованием JavaScript-а,
без тяжеловесного инструментария фронтендеров (React и пр).

Чтобы в конечном итоге написание компонентов веб-морды выглядело так:

```python
from sundash import App, Component, Signal


app = App()


class CurrentTime(Component):
    html = '<p>{{ value }}<p/>'

    # Каждый инстанс должен хранить эти переменные в памяти и восстанавливать
    value: Var[dt.time] = None

    @app.on(Signal.EVERY_SECOND)
    def update(self):
        self.value = dt.time.now()


app.run(layout=[CurrentTime()])
```
