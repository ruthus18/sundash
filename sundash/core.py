from __future__ import annotations

import asyncio
import contextvars
import functools
import logging
import typing as t
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# 1. Basics

class Var[T]:
    type Key = str
    type Value = T


type VarStorage = dict[Var.Key, Var.Value]
type HTML = str


# 2. Signals & Commands

@dataclass
class SIGNAL:
    type Name = str

    @property
    def _name(self) -> Name:
        return self.__class__.__name__

    @property
    def _data(self) -> dict:
        return self.__dict__


@dataclass
class LAYOUT_UPDATED(SIGNAL): ...
@dataclass
class LAYOUT_CLEAN(SIGNAL): ...
@dataclass
class EVERY_SECOND(SIGNAL): ...


@dataclass
class COMMAND:
    @property
    def _name(self) -> str:
        return self.__class__.__name__

    @property
    def _data(self) -> dict:
        return self.__dict__


@dataclass
class SET_VAR(COMMAND):
    key: Var.Key
    value: Var.Value


@dataclass
class CLEAR_LAYOUT(COMMAND):
    ...


@dataclass
class UPDATE_LAYOUT(COMMAND):
    html: HTML
    vars: VarStorage


signals_by_name = {c.__name__: c for c in SIGNAL.__subclasses__()}

_conn = contextvars.ContextVar('_conn', default=None)


async def emit_signal(sig: SIGNAL | type[SIGNAL]) -> None:
    if not isinstance(sig, SIGNAL): sig = sig()
    logger.info(f'{sig._name} {sig._data}')

    for callback in _callbacks.get(sig._name, set()):
        await callback(sig)


async def send_command(cmd: COMMAND | type[COMMAND]) -> None:
    if not isinstance(cmd, COMMAND): cmd = cmd()
    logger.info(f'{cmd._name} {cmd._data}')

    conn = _conn.get()
    await conn.send_command(cmd)


# 3. Components

class Component:
    html: HTML = ''

    class Storage: NotImplemented

    # @classmethod
    # def get_vars(cls) -> tuple[Var.Key]:
    #     return tuple(cls.Storage.__annotations__.keys())

    @classmethod
    async def set(self, key: str, value: str) -> None:
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
    sig_name = signal_cls._name
    if sig_name not in _callbacks:
        _callbacks[sig_name] = set()

    _callbacks[sig_name].add(callback)


def on(signal_cls: type[SIGNAL]) -> SignalCallback:
    def wrapper(func: _SignalCallbackRaw) -> SignalCallback:

        callback: SignalCallback = None
        try:
            is_comp_callback = True
        except AttributeError:
            is_comp_callback = False

        if is_comp_callback:
            cls = callback.__self__
            callback = lambda sig: func(cls, sig)
        else:
            callback = lambda sig: func(sig)

        callback = functools.wraps(func)(callback)
        subscribe(signal_cls, callback)
        return func

    return wrapper


# 5. Server & Layout

from .server import Server


class _Layout:
    _current: list[Component] = []
    _storage: VarStorage = {}

    @classmethod
    def append(cls, comp: Component) -> None:
        cls._current.append(comp)

    @classmethod
    def get_current(cls) -> tuple[HTML, VarStorage]:
        html = ''.join([comp.html for comp in cls._current])
        return html, cls._storage.copy()


# 6. App

class App:
    Server = Server
    Layout = _Layout

    def run(self, **params: dict) -> None:
        asyncio.run(self.task(**params))

    async def task(
        self,
        layout: list[Component] = [],
        host: str = 'localhost',
        port: int = 5000,
    ) -> None:
        for comp in layout: self.Layout.append(comp)

        # on(CLIENT_CONNECTED)(self.on_client_connected)
        # on(CLIENT_DISCONNECTED)(self.on_client_disconnected)
        # on(LAYOUT_CLEAN)(self.on_layout_clean)

        await self.Server.task(host, port)

    # async def on_client_connected(self, sig: CLIENT_CONNECTED) -> None:
    #     ...

    # async def on_client_disconnected(self, sig: CLIENT_DISCONNECTED) -> None:
    #     ...

    # async def on_layout_clean(self, sig: LAYOUT_CLEAN) -> None:
    #     html, vars = self.Layout.get_current()
    #     await send_command(UPDATE_LAYOUT(html=html, vars=vars))
