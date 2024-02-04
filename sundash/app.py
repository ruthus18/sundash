import asyncio
import dataclasses as dc
import logging

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


type Components = list[HTML]


class Layout(list[HTML]):

    @property
    def as_html(self) -> HTML:
        return ''.join(self)


class _AppSingleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        else:
            raise RuntimeError('Only one instance of `App` is allowed')

        return cls._instances[cls]


class App(metaclass=_AppSingleton):
    Server = Server
    Layout = Layout

    def __init__(self):
        register_system_callback('on_session_open', self.update_layout)
        register_system_callback('on_event', self.dispatch_event)

    def run_sync(self, components: Components = []) -> None:
        try:
            asyncio.run(self.run(components))
        except KeyboardInterrupt:
            pass

    async def run(self, components: Components = []) -> None:
        self.server = self.Server()
        self.layout = self.Layout(components)

        await self.server.run()

    async def update_layout(self, session: Session):
        await session.send_command(UPDATE_LAYOUT(html=self.layout.as_html))

    async def dispatch_event(self, event: EVENT):
        logger.info(f'dispatching event {event._name}')
