from __future__ import annotations

import asyncio
import logging
import typing as t
from abc import ABC
from dataclasses import dataclass
from dataclasses import is_dataclass

logger = logging.getLogger(__name__)


# 1. Basics

class Var[T]:
    type Key = str
    type Value = T


type VarStorage = dict[Var.Key, Var.Value]
type HTML = str


# 2. Signal Bus & Commands Sending

class _MESSAGE(ABC):
    type Name = str

    _name = property(lambda self: self.__class__.__name__)
    _data = property(lambda self: self.__dict__)


@dataclass
class SIGNAL(_MESSAGE): ...


@dataclass
class LAYOUT_UPDATED(SIGNAL): ...


@dataclass
class LAYOUT_CLEAN(SIGNAL): ...


@dataclass
class BUTTON_CLICK(SIGNAL):
    button_id: str


@dataclass
class EVERY_SECOND(SIGNAL): ...


@dataclass
class COMMAND(_MESSAGE): ...


@dataclass
class SET_VAR(COMMAND):
    key: Var.Key
    value: Var.Value


@dataclass
class CLEAR_LAYOUT(COMMAND): ...


@dataclass
class UPDATE_LAYOUT(COMMAND):
    html: HTML
    vars: VarStorage


signals = {s.__name__: s for s in SIGNAL.__subclasses__()}


async def emit_signal(sig: SIGNAL | type[SIGNAL]) -> None:
    if not isinstance(sig, SIGNAL): sig = sig()
    logger.info(f'{sig._name} {sig._data}')

    for callback in _callbacks.get(sig._name, set()):
        await callback(sig)


from .server import get_connection


async def send_command(cmd: COMMAND | type[COMMAND]) -> None:
    if not isinstance(cmd, COMMAND): cmd = cmd()
    logger.info(f'-> {cmd._name} {cmd._data}')

    conn = get_connection()
    await conn.send_command(cmd)


# 3. Signal Callbacks

type _FunctionCallback = t.Callable[[object, SIGNAL], None]
type _ClassCallback = t.Callable[[SIGNAL], None]

type ClassCallback = t.Awaitable[_ClassCallback]
type FunctionCallback = t.Awaitable[_FunctionCallback]

type AnyCallback = FunctionCallback | ClassCallback
type Callback = FunctionCallback


_callbacks: dict[SIGNAL.Name, set[Callback]] = {}


def subscribe(signal_cls: type[SIGNAL], callback: Callback) -> None:
    sig_name = signal_cls.__name__
    if sig_name not in _callbacks:
        _callbacks[sig_name] = set()

    _callbacks[sig_name].add(callback)


def unsubscribe(signal_cls: type[SIGNAL], callback: Callback) -> None:
    sig_name = signal_cls.__name__
    _callbacks[sig_name].remove(callback)


def _get_f_self(func: t.Callable) -> object | None:
    try:
        return func.__self__
    except AttributeError:
        return None


def _get_f_cls_name(func: t.Callable) -> str | None:
    name = func.__qualname__.split('.')
    if len(name) > 2:
        raise RuntimeError

    return name[0] if len(name) == 2 else None


def on(signal_cls: type[SIGNAL]) -> AnyCallback:
    def wrapper(func: AnyCallback) -> AnyCallback:
        self = _get_f_self(func)
        cls_name = _get_f_cls_name(func)

        if self and cls_name:
            # `on` called for `self.method` -> valid callback
            subscribe(signal_cls, func)

        elif not self and not cls_name:
            # `on` called for module function -> valid callback
            subscribe(signal_cls, func)

        elif not self and cls_name:
            # `on` called for class function -> not valid callback...
            # only valid in component interface
            Component.schedule_callback(signal_cls, cls_name, func.__name__)

        elif self and not cls_name:
            raise RuntimeError  # no way...

        return func

    return wrapper


# 4. Layout & Components

class Component:
    html: HTML = ''

    @dataclass
    class Vars: ...

    _callbacks: set[tuple[type[SIGNAL], str, str]] = set()

    def __init__(self):
        if not is_dataclass(self.Vars):
            raise RuntimeError

        # TODO: init procedural values
        self.vars: dict = self.Vars().__dict__

    @classmethod
    def schedule_callback(
        cls, signal_cls: type[SIGNAL], cls_name: str, func_name: str
    ) -> None:
        cls._callbacks.add((signal_cls, cls_name, func_name))

    def subscribe_callbacks(self) -> None:
        cls = self.__class__
        for signal_cls, cls_name, func_name in self.__class__._callbacks:
            if cls.__name__ != cls_name: continue

            callback = getattr(self, func_name)
            subscribe(signal_cls, callback)

    def unsubscribe_callbacks(self) -> None:
        cls = self.__class__
        for signal_cls, cls_name, func_name in self.__class__._callbacks:
            if cls.__name__ != cls_name: continue

            callback = getattr(self, func_name)
            unsubscribe(signal_cls, callback)

    async def set(self, key: Var.Key, value: Var.Value) -> None:
        # TODO if not getattr(self.Vars, key, value): ...
        await send_command(SET_VAR(key=key, value=value))


class Layout(list[type[Component]]):
    _sessions: dict[int, list[Component]] = {}

    def append(self, item: type[Component] | HTML) -> None:
        if isinstance(item, str):
            class HTMLComponent(Component):
                html = item

            comp = HTMLComponent
        else:
            comp = item

        super().append(comp)

    def open_session(self) -> tuple[HTML, VarStorage]:
        layout = []
        for comp_cls in self:
            comp = comp_cls()
            comp.subscribe_callbacks()
            layout.append(comp)

        data = {}
        for comp in layout:
            data.update(**comp.vars)

        html = ''.join((c.html for c in layout))

        id = get_connection().id
        self._sessions[id] = layout
        return html, data

    def close_session(self) -> None:
        id = get_connection().id
        for comp in self._sessions[id]:
            comp.unsubscribe_callbacks()

        self._sessions.pop(id)


# 5. App

from . import server


class App:
    def run(self, **params: dict) -> None:
        try:
            asyncio.run(self.task(**params))
        except KeyboardInterrupt:
            pass

    async def task(
        self,
        layout: t.Iterable[Component | HTML] = [],
    ) -> None:
        self.layout = Layout()
        for comp in layout: self.layout.append(comp)

        on(server.CLIENT_CONNECTED)(self.open_layout_session)
        on(server.CLIENT_DISCONNECTED)(self.close_layout_session)

        self.server = server.Server()
        await self.server.task()

    async def open_layout_session(self, _) -> None:
        html, data = self.layout.open_session()
        await send_command(UPDATE_LAYOUT(html=html, vars=data))

    async def close_layout_session(self, _) -> None:
        self.layout.close_session()


@on(server.CLIENT_CONNECTED)
async def log_something(sig: server.CLIENT_CONNECTED) -> None:
    logger.info('Я мясистая улиточка со шпинатом и сыром')
