# Sundash

**Python & JS micro framework for realtime web UI applications**

* **ASGI-based** -- minimal 3rd party dependencies and clean core part
* **Flexible and extensible** -- easy to embed to existing ASGI server, extend core part, add 3rd party integrations
* **Realtime** -- operating through websockets bus, callback-based client <-> server communication
* **Lightweight frontend** -- based on Parcel
* **Crafted with ❤️**


**Usage:** check `examples` folder and run server

```bash
    python -m examples._01_clock
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

        time: Var[str] = now  # you can pass init values (static or procedural)

        @app.on(EVERY_SECOND)  # run callback when user open webpage
        async def update(self, _):
            await self.set('time', now())  # live update of value


    app.attach_to_layout('<h1>Clock Test</h1>')  # add plain HTML
    app.attach_to_layout(Clock())                # or own components

    run(app)
```

![clock](docs/examples/_01_clock.png "Clock")
