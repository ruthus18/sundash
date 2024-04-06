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


![clock](examples/img/_02_clock.png "Clock")


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
