from __future__ import annotations

import asyncio
import functools
import typing as t
from dataclasses import dataclass

from starlette.websockets import WebSocket

# 1. Basics


class Var[T]:
    type Key = str
    type Value = T


type VarStorage = dict[Var.Key, Var.Value]
type HTML = str


# 2. Signals & Commands

@dataclass
class SIGNAL: ...


class SERVER_STARTUP(SIGNAL): ...
class SERVER_SHUTDOWN(SIGNAL): ...
class CLIENT_CONNECTED(SIGNAL): ...
class CLIENT_DISCONNECTED(SIGNAL): ...
class LAYOUT_UPDATED(SIGNAL): ...
class LAYOUT_CLEAN(SIGNAL): ...
class EVERY_SECOND(SIGNAL): ...


@dataclass
class COMMAND: ...


@dataclass
class SET_VAR(COMMAND):
    key: Var.Key
    value: Var.Value


class CLEAR_LAYOUT(COMMAND): ...


@dataclass
class UPDATE_LAYOUT(COMMAND):
    html: HTML
    vars: VarStorage


_signals: asyncio.Queue[SIGNAL] = asyncio.Queue()
_commands: asyncio.Queue[COMMAND] = asyncio.Queue()


async def send_signal(sig: SIGNAL | type[SIGNAL]) -> None:
    if not isinstance(sig, SIGNAL): sig = sig()
    await _signals.put(sig)


async def send_command(cmd: COMMAND | type[COMMAND]) -> None:
    if not isinstance(cmd, COMMAND): cmd = cmd()
    await _commands.put(cmd)


# 3. Components

class Component:
    html: HTML = ''

    class Storage: NotImplemented

    @classmethod
    def get_vars(cls) -> tuple[Var.Key]:
        return tuple(cls.Storage.__annotations__.keys())

    @classmethod
    async def set(self, key: str, value: str) -> None:
        setattr(self, key, value)
        await send_command(SET_VAR(key=key, value=value))


# 4. Signal Callbacks

type _SignalClassCallback = t.Callable[[object, SIGNAL], None]
type _SignalModuleCallback = t.Callable[[SIGNAL], None]

type SignalClassCallback = t.Awaitable[_SignalClassCallback]
type SignalModuleCallback = t.Awaitable[_SignalModuleCallback]

type _SignalCallbackRaw = SignalClassCallback | SignalModuleCallback
type SignalCallback = SignalModuleCallback


_callbacks: dict[SIGNAL, set[SignalCallback]] = {}


def subscribe(signal_cls: type[SIGNAL], callback: SignalCallback) -> None:
    if signal_cls not in _callbacks:
        _callbacks[signal_cls] = set()

    _callbacks[signal_cls].add(callback)


def on(signal_cls: type[SIGNAL]) -> SignalCallback:
    def wrapper(func: _SignalCallbackRaw) -> SignalCallback:

        callback: SignalCallback = None
        try:
            self = callback.__self__
            callback = lambda sig: func(self, sig)
        except AttributeError:
            callback = lambda sig: func(sig)

        callback = functools.wraps(func)(callback)
        subscribe(signal_cls, callback)
        return func

    return wrapper


# 5. Server & Layout

class _Server:
    _connections: set[WebSocket] = set()

    @classmethod
    async def listen_connections(cls, host: str, port: int) -> None:
        ...  # TODO produces

        # await send_signal(CLIENT_CONNECTED)
        # await send_signal(CLIENT_DISCONNECTED)

    async def task(self) -> None:
        command: COMMAND = await _commands.get()
        ...


class _Layout:
    _current: list[Component] = []
    _storage: VarStorage = {}

    @classmethod
    def append(cls, comp: Component) -> None:
        cls._current.append(comp)

    @classmethod
    def get_current(cls) -> tuple[HTML, VarStorage]:
        html = ''
        for comp in cls._current:
            html += comp.html

        return html, cls._storage.copy()


@on(SERVER_STARTUP)
async def on_server_startup(_): print('SERVER_STARTUP')


@on(SERVER_SHUTDOWN)
async def on_server_shutdown(_): print('SERVER_SHUTDOWN')


# 6. App

class App:
    Server = _Server
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

        on(CLIENT_CONNECTED)(self.on_client_connected)
        on(CLIENT_DISCONNECTED)(self.on_client_disconnected)
        on(LAYOUT_CLEAN)(self.on_layout_clean)

        await self.Server.listen_connections(host, port)

    async def on_client_connected(self, sig: CLIENT_CONNECTED) -> None:
        await send_command()

    async def on_client_disconnected(self, sig: CLIENT_DISCONNECTED) -> None:
        ...

    async def on_layout_clean(self, sig: LAYOUT_CLEAN) -> None:
        html, vars = self.Layout.get_current()
        await send_command(UPDATE_LAYOUT(html=html, vars=vars))
