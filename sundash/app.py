from __future__ import annotations

import asyncio
import dataclasses as dc
import logging
import typing as t
from collections import defaultdict

from . import utils
from .html import HTML
from .messages import Command
from .messages import Event
from .server import Server
from .sessions import Session

logger = logging.getLogger(__name__)


@dc.dataclass
class UpdateLayout(Command):
    html: HTML
    vars: dict = dc.field(default_factory=dict)


@dc.dataclass
class LayoutUpdated(Event): ...


@dc.dataclass
class SetVar(Command):
    name: str
    value: str


@dc.dataclass
class VarSet(Event): ...


@dc.dataclass
class ButtonClick(Event):
    button_id: str


@dc.dataclass
class InputUpdated(Event):
    name: str
    value: str


type Callback = t.Callable[[Event], t.Awaitable[None]]
type CallbacksMap = list[tuple[Event.T, Callback]]

type _CpName = str  # component name
type _CbName = str  # callback name
type _ComponentRegistry = dict[_CpName, list[tuple[Event.T, _CbName]]]

_registry: _ComponentRegistry = defaultdict(list)


def on(event_cls: Event.T) -> t.Callable:
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

    async def update_var(self, name: str) -> None:
        value = getattr(self.vars, name)

        await Session.get().send_command(SetVar(name=name, value=value))


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
    def update_command(self) -> UpdateLayout:
        return UpdateLayout(html=self.html, vars=self.vars)


class App:
    Server = Server

    def __init__(self):
        self.raw_pages: dict[Route, RawPage] = {}
        self.layouts: dict[Session.ID, Layout] = {}

    @property
    def session(self) -> Session:
        return Session.get()

    @property
    def session_layout(self) -> Layout:
        return self.layouts[self.session.id]

    async def on_session_open(self) -> None:
        layout = Layout()
        for route, page in self.raw_pages.items():
            layout.add_page(route, page)

        self.layouts[self.session.id] = layout

        await self.session.send_command(layout.update_command)

    async def on_session_close(self) -> None:
        self.layouts.pop(self.session.id)

    async def on_event(self, event: Event) -> None:
        callbacks_map = self.session_layout.callbacks_map

        for event_cls, callback in callbacks_map:
            if event_cls == event._cls:
                await callback(event)

    async def switch_page(self, route: Route):
        if route not in self.raw_pages:
            raise ValueError(f'Incorrect route: `{route}`')

        layout = self.session_layout
        layout.switch_page(route)

        await self.session.send_command(layout.update_command)

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

        self.server = self.Server(
            on_session_open=self.on_session_open,
            on_session_close=self.on_session_close,
            on_event=self.on_event,
        )
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
