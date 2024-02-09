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


class Component:
    html: HTML

    def __str__(self) -> str:
        return self.html


class HTMLComponent(Component):
    def __init__(self, html: HTML):
        self.html = html


type InputLayout = t.Iterable[Component | HTML]


class Layout(list[Component]):

    def __init__(self, input_items: InputLayout):
        items = []

        for item in input_items:
            if isinstance(item, str):
                item = HTMLComponent(html=item)
            elif issubclass(item, Component):
                pass
            else:
                raise ValueError(
                    f'Incorrect type of layout component: {type(item)}'
                )

            items.append(item)
        super().__init__(items)

    @property
    def as_html(self) -> HTML:
        return ''.join((item.html for item in self))


class App:
    Server = Server
    Layout = Layout

    def __init__(self):
        self._callbacks: dict[Session.ID, list[t.Awaitable]] = {}

        register_system_callback('on_session_open', self.update_layout)
        register_system_callback('on_event', self.dispatch_event)

    def run_sync(self, layout: InputLayout = []) -> None:
        try:
            asyncio.run(self.run(layout))
        except KeyboardInterrupt:
            pass

    async def run(self, input_layout: InputLayout = []) -> None:
        self.server = self.Server()
        self.layout = self.Layout(input_layout)

        await self.server.run()

    async def update_layout(self, session: Session):
        await session.send_command(UPDATE_LAYOUT(html=self.layout.as_html))

    async def dispatch_event(self, event: EVENT):
        logger.info(f'dispatching event {event._name}')

    def on(self, event: EVENT) -> t.Awaitable:
        async def wrapper(*args, **kwargs): ...  # TODO

        return functools.wraps(wrapper)
