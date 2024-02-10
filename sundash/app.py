import asyncio
import dataclasses as dc
import functools
import logging
import typing as t

from .core import COMMAND
from .core import EVENT
from .core import HTML
from .core import register_system_callback
from .server import Server
from .server import Session

logger = logging.getLogger(__name__)


@dc.dataclass
class UPDATE_LAYOUT(COMMAND):
    html: HTML
    vars: dict = dc.field(default_factory=dict)


@dc.dataclass
class LAYOUT_UPDATED(EVENT): ...


@dc.dataclass
class BUTTON_CLICK(EVENT):
    button_id: str


@dc.dataclass
class INPUT_UPDATED(EVENT):
    name: str
    value: str


class Component:
    html: HTML

    def __str__(self) -> str:
        return self.html


class HTMLComponent(Component):
    def __init__(self, html: HTML): self.html = html


type LayoutTemplate = t.Iterable[type[Component] | HTML]
type CurrentLayout = list[Component | HTML]


class Layout:

    def __init__(self, template: LayoutTemplate = []):
        self.template: LayoutTemplate = []
        self.storage: dict = {}

        self.current: CurrentLayout = []

        for item in template:
            if isinstance(item, str):
                pass
            elif issubclass(item, Component):
                pass
            else:
                raise ValueError(
                    f'Incorrect type of layout component: {item}'
                )
            self.template.append(item)

    @property
    def as_html(self) -> HTML:
        return ''.join((item.html for item in self.current))

    async def init_session(self, session: Session) -> None:

        for item in self.template:
            if isinstance(item, str):
                component = HTMLComponent(html=item)
            else:
                component = item()

            self.current.append(component)

        cmd = UPDATE_LAYOUT(html=self.as_html)
        await session.send_command(cmd)

    def close_session(self) -> None:
        self.current = []


class App:
    Server = Server
    Layout = Layout

    def __init__(self):
        self._callbacks: dict[Session.ID, list[t.Awaitable]] = {}

        register_system_callback('on_session_open', self.on_session_open)
        register_system_callback('on_session_close', self.on_session_close)
        register_system_callback('on_event', self.on_event)

    def run_sync(self, layout_tpl: LayoutTemplate = None) -> None:
        try:
            asyncio.run(self.run(layout_tpl))
        except KeyboardInterrupt:
            pass

    async def run(self, layout_tpl: LayoutTemplate = None) -> None:
        self.server = self.Server()
        self.layout = self.Layout(layout_tpl)

        await self.server.run()

    async def on_session_open(self, session: Session) -> None:
        await self.layout.init_session(session)

    async def on_session_close(self, session: Session) -> None:
        self.layout.close_session()

    def on(self, event: EVENT) -> t.Awaitable:
        async def wrapper(*args, **kwargs): ...  # TODO

        return functools.wraps(wrapper)

    async def on_event(self, event: EVENT) -> None:
        logger.info(f'dispatching event {event._name}')
