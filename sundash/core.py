from __future__ import annotations

import asyncio
import functools
import logging
import typing as t
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# 1. Basics

class Var[T]:
    type Key = str
    type Value = T


# type VarStorage = dict[Var.Key, Var.Value]
type HTML = str


# 2. Signals & Commands

class _MESSAGE:
    type Name = str

    @property
    def _name(self) -> Name:
        return self.__class__.__name__

    @property
    def _data(self) -> dict:
        return self.__dict__


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
    # vars: VarStorage


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


# 3. Components

class Component:
    html: HTML = ''

    class Storage: NotImplemented

    # @classmethod
    # def get_vars(cls) -> tuple[Var.Key]:
    #     return tuple(cls.Storage.__annotations__.keys())

    @classmethod
    async def set(self, key: Var.Key, value: Var.Value) -> None:
        setattr(self, key, value)
        await send_command(SET_VAR(key=key, value=value))


# 4. Signal Callbacks

type _SignalClassCallback = t.Callable[[type[object], SIGNAL], None]
type _SignalModuleCallback = t.Callable[[SIGNAL], None]

type SignalClassCallback = t.Awaitable[_SignalClassCallback]
type SignalModuleCallback = t.Awaitable[_SignalModuleCallback]

type _SignalCallbackRaw = SignalClassCallback | SignalModuleCallback
type SignalCallback = SignalModuleCallback


_callbacks: dict[SIGNAL.Name, set[SignalCallback]] = {}


def subscribe(signal_cls: type[SIGNAL], callback: SignalCallback) -> None:
    sig_name = signal_cls.__name__
    if sig_name not in _callbacks:
        _callbacks[sig_name] = set()

    _callbacks[sig_name].add(callback)


def on(signal_cls: type[SIGNAL]) -> SignalCallback:
    def wrapper(func: _SignalCallbackRaw) -> SignalCallback:

        callback: SignalCallback = None
        try:
            cls = callback.__self__
        except AttributeError:
            is_comp_callback = False
        else:
            is_comp_callback = True

        if is_comp_callback:
            callback = lambda sig: func(cls, sig)
        else:
            callback = lambda sig: func(sig)

        callback = functools.wraps(func)(callback)
        subscribe(signal_cls, callback)
        return func

    return wrapper


# 5. Layout

class Layout(list[Component]):
    def append(self, item: Component | HTML) -> None:
        if isinstance(item, str):
            comp_obj = Component()
            comp_obj.html = item
        else:
            comp_obj = item
        super().append(comp_obj)

    def get_html(self) -> HTML:
        return ''.join((c.html for c in self))


# 6. App

class App:
    def __init__(self):
        self.layout = Layout()

    def run(self, **params: dict) -> None:
        from .server import build_ui

        build_ui()
        try:
            asyncio.run(self.task(**params))
        except KeyboardInterrupt:
            pass

    async def task(
        self,
        layout: t.Iterable[Component | HTML] = [],
    ) -> None:
        for comp in layout: self.layout.append(comp)

        from . import server
        self.server = server.Server()

        on(server.CLIENT_CONNECTED)(self.on_client_connected)
        await self.server.task()

    async def on_client_connected(self, _) -> None:
        layout_html = self.layout.get_html()
        await send_command(UPDATE_LAYOUT(html=layout_html))
