from __future__ import annotations

import asyncio
import dataclasses as dc
import logging
import typing as t
from collections import defaultdict

from . import utils
from .core import COMMAND
from .core import EVENT
from .core import HTML
from .core import ON_EVENT
from .core import ON_SESSION_CLOSE
from .core import ON_SESSION_OPEN
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
class SET_VAR(COMMAND):
    name: str
    value: str


@dc.dataclass
class VAR_SET(EVENT): ...


@dc.dataclass
class BUTTON_CLICK(EVENT):
    button_id: str


@dc.dataclass
class INPUT_UPDATED(EVENT):
    name: str
    value: str


type Callback = t.Awaitable[t.Callable[[EVENT], None]]
type CallbacksMap = list[tuple[EVENT.T, Callback]]

type _CpName = str  # component name
type _CbName = str  # callback name
type _ComponentRegistry = dict[_CpName, list[tuple[EVENT.T, _CbName]]]

_registry: _ComponentRegistry = defaultdict(list)


def on(event_cls: EVENT.T) -> t.Callable:
    def wrapper(callback: Callback) -> Callback:
        self = utils.get_f_self(callback)
        cmp_cls_name = utils.get_f_cls_name(callback)

        if self is None and cmp_cls_name:
            _registry[cmp_cls_name].append((event_cls, callback.__name__))
        else:
            raise RuntimeError

        return callback
    return wrapper


class Component:
    html: HTML

    @dc.dataclass
    class Vars: pass

    def __init__(self):
        self.vars = self.Vars()

    @property
    def callbacks_map(self) -> CallbacksMap:
        return [
            (event_cls, getattr(self, callback_name))
            for event_cls, callback_name
            in _registry[self.__class__.__name__]
        ]

    async def update_var(self, name: str, event: EVENT) -> None:
        session = event._ctx.session
        value = getattr(self.vars, name)

        await session.send_command(SET_VAR(name=name, value=value))


class HTMLComponent(Component):
    """Proxy component for plain HTML string"""
    def __init__(self, html: HTML):
        super().__init__()
        self.html = html


class Page(list[Component]):

    @property
    def callbacks_map(self) -> CallbacksMap:
        cb_map = []
        for component in self:
            cb_map += component.callbacks_map
        return cb_map


type RawPage = t.Iterable[type[Component] | HTML]
type Route = str


def convert_to_page(raw_page: RawPage) -> Page:
    page = Page()
    for item in raw_page:
        if isinstance(item, str):
            component = HTMLComponent(html=item)
        else:
            component = item()

        page.append(component)
    return page


class Layout:
    def __init__(self, raw_page: RawPage | None = None):
        self.pages: dict[Route, Page] = {}
        self.current_route = None

        if raw_page is not None:
            self.add_page(route=self.current_route, page=raw_page)

    def add_page(self, route: Route, page: RawPage) -> None:
        if not self.current_route:
            self.current_route = route

        self.pages[route] = convert_to_page(page)

    def switch_page(self, route: Route) -> None:
        self.current_route = route

    @property
    def current_page(self) -> Page:
        return self.pages[self.current_route]

    @property
    def html(self) -> HTML:
        return ''.join((comp.html for comp in self.current_page))

    @property
    def vars(self) -> dict:
        result = {}
        for comp in self.current_page:
            result.update(comp.vars.__dict__)
        return result

    @property
    def callbacks_map(self) -> CallbacksMap:
        return self.current_page.callbacks_map

    @property
    def update_layout_event(self) -> UPDATE_LAYOUT:
        return UPDATE_LAYOUT(html=self.html, vars=self.vars)


class App:
    Server = Server

    def __init__(self):
        self.raw_pages: dict[Route, RawPage] = {}
        self.layouts: dict[Session.ID, Layout] = {}

        register_system_callback(ON_SESSION_OPEN, self._on_session_open)
        register_system_callback(ON_SESSION_CLOSE, self._on_session_close)
        register_system_callback(ON_EVENT, self._on_event)

    async def _on_session_open(self, session: Session) -> None:
        layout = Layout()
        for route, page in self.raw_pages.items():
            layout.add_page(route, page)

        self.layouts[session.id] = layout

        await session.send_command(layout.update_layout_event)

    async def _on_session_close(self, session: Session) -> None:
        self.layouts.pop(session.id)

    async def _on_event(self, event: EVENT) -> None:
        session = event._ctx.session
        callbacks_map = self.layouts[session.id].callbacks_map

        for event_cls, callback in callbacks_map:
            if event_cls == event._cls:
                await callback(event)

    async def switch_page(self, route: Route, *, session: Session):
        if route not in self.raw_pages:
            raise ValueError(f'Incorrect route: `{route}`')

        layout = self.layouts[session.id]
        layout.switch_page(route)

        await session.send_command(layout.update_layout_event)

    async def run(
        self,
        page: RawPage = None,
        *,
        routed_pages: dict[Route, RawPage] = None,
    ) -> None:
        assert page or routed_pages
        if page is not None:
            self.raw_pages = {'*': page}

        elif routed_pages is not None:
            self.raw_pages = routed_pages

        self.server = self.Server()
        await self.server.run()

    def run_sync(
        self,
        page: RawPage = None,
        *,
        routed_pages: dict[Route, RawPage] = None,
    ) -> None:
        try:
            asyncio.run(self.run(page, routed_pages=routed_pages))
        except KeyboardInterrupt:
            pass
