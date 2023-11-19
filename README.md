# Sundash

**Python & JS micro framework for realtime web UI applications**

* **ASGI-based** -- minimal 3rd party dependencies and clean core part
* **Flexible and extensible** -- easy to customize, add 3rd party integrations
* **Realtime** -- operating through websockets bus, client & backend in app
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

    from sundash import EVERY_SECOND
    from sundash import App
    from sundash import Component
    from sundash import on
    

    app = App()

    now = lambda: dt.datetime.now().strftime('%H:%M:%S')


    class Clock(Component):
        html = '<p><b>Time:</b> {{ time }}<p/>'

        class Vars:
            # you can pass init values (static or procedural)
            time: str = now

        # run callback when user open webpage
        @on(EVERY_SECOND)
        async def update(self, _):
            await self.set('time', now())  # live update of value

    # add plain HTML or own components
    app.run(layout=('<h1>Clock Test</h1>', Clock()))
```

![clock](docs/examples/_02_clock.png "Clock")


### Development

* Required: npm, nodejs, python 3.12, poetry, virtualenv
* Install JS dependencies: `npm install`
* Install Python dependencies: `poetry install --with=dev`
* Run local linters: `poe q`
* Publish package: `poetry publish --build`