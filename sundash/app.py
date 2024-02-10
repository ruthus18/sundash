from __future__ import annotations
import asyncio
from collections import defaultdict
import dataclasses as dc
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



type Callback = t.Awaitable[t.Callable[[EVENT], None]]
type CallbackRegistry = dict[EVENT.T, list[Callback]]

type LayoutTemplate = t.Iterable[type[Component] | HTML]


class Component:
    html: HTML

    def __init__(self):
        self.callbacks: CallbackRegistry = {}


class HTMLComponent(Component):
    def __init__(self, html: HTML): self.html = html


class Layout:

    def __init__(self, template: LayoutTemplate = []):
        self.template: LayoutTemplate = []
        self.current: list[Component] = []
        # self.storage: dict = {}

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

    def get_component_callbacks(self) -> t.Generator[CallbackRegistry]:
        return (cmp.callbacks for cmp in self.current)


class App:
    Server = Server
    Layout = Layout

    def __init__(self):
        self._layouts: dict[Session.ID, Layout] = {}
        self._callbacks: dict[Session.ID, CallbackRegistry] = {}

        register_system_callback('on_session_open', self._on_session_open)
        register_system_callback('on_session_close', self._on_session_close)
        register_system_callback('on_event', self._on_event)

    async def _on_session_open(self, session: Session) -> None:
        layout = self.Layout(self.layout_tpl)
        self._layouts[session.id] = layout

        await layout.init_session(session)

        # TODO: * impl merge op over registry
        #       * run once instead every instance
        callback_registry = defaultdict(list)

        for callbacks in layout.get_component_callbacks():
            for event_cls, callback in callbacks.items():
                callback_registry[event_cls].append(callback)
        
        self._callbacks[session.id] = callback_registry

    async def _on_session_close(self, session: Session) -> None:
        self._layouts.pop(session.id)
        self._callbacks.pop(session.id)

    async def _on_event(self, event: EVENT) -> None:
        session = event._ctx.session
        callbacks = self._callbacks[session.id][event._cls]

        for cb in callbacks:
            await cb(event)

    async def run(self, layout_tpl: LayoutTemplate = None) -> None:
        self.layout_tpl = layout_tpl

        self.server = self.Server()
        await self.server.run()

    def run_sync(self, layout_tpl: LayoutTemplate = None) -> None:
        try:
            asyncio.run(self.run(layout_tpl))
        except KeyboardInterrupt:
            pass


def on(event_cls: EVENT.T) -> t.Callable:
    def wrapper(callback: Callback) -> Callback:
        # self = _utils.get_f_self(func)
        # cls_name = _utils.get_f_cls_name(func)

        # if self is not None and cls_name:
        #     # `on` called for `self.method` -> valid callback
        #     subscribe(signal_cls, func)

        # elif self is None and not cls_name:
        #     # `on` called for module function -> valid callback
        #     subscribe(signal_cls, func)

        # elif self is None and cls_name:
        #     # `on` called for class function -> not valid callback...
        #     # only valid in component interface
        #     from .layout import Component
        #     Component.schedule_callback(signal_cls, cls_name, func.__name__)

        # elif self is not None and not cls_name:
        #     raise RuntimeError  # no way...

        return callback

    return wrapper