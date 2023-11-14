from __future__ import annotations

import asyncio
import dataclasses
import functools
import typing as t

# 1. Basics


class Var[T]:
    type Key = str
    type Value = T


type VarStorage = dict[Var.Key, Var.Value]
type HTML = str


# 2. Signals & Commands

@dataclasses.dataclass
class SIGNAL: ...


class SERVER_STARTUP(SIGNAL): ...
class SERVER_SHUTDOWN(SIGNAL): ...
class CLIENT_CONNECTED(SIGNAL): ...
class CLIENT_DISCONNECTED(SIGNAL): ...
class LAYOUT_UPDATED(SIGNAL): ...
class LAYOUT_CLEAN(SIGNAL): ...


@dataclasses.dataclass
class COMMAND: ...


class SET_VAR(COMMAND):
    key: Var.Key
    value: Var.Value


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

    def collect_vars(cls):
        ...  # TODO

    async def set(self, key: str, value: str) -> None:
        setattr(self, key, value)
        await send_command(SET_VAR(key=key, value=value))


# 4. Signal Callbacks

type _ComponentSignalCallback = t.Callable[[Component, SIGNAL], None]
type _ModuleSignalCallback = t.Callable[[SIGNAL], None]

type ComponentSignalCallback = t.Awaitable[_ComponentSignalCallback]
type ModuleSignalCallback = t.Awaitable[_ModuleSignalCallback]

type SignalCallback = ComponentSignalCallback | ModuleSignalCallback


async def subscribe(signal: SIGNAL, callback: SignalCallback) -> None:
    ...


# TODO maybe app don't need...
def on_signal(app: App, signal_cls: type[SIGNAL]) -> SignalCallback:
    def wrapper(func: SignalCallback):

        async def module_callback(signal: SIGNAL) -> None:
            return await func(signal)

        async def component_callback(self: Component, signal: SIGNAL) -> None:
            return await func(self, signal)

        # TODO define callback type based on passed func
        callback: SignalCallback = module_callback or component_callback

        ...  # TODO add callback to scheduler
        return functools.wraps(func)(callback)

    return wrapper


# 5. Server & Layout

class _Server:

    @classmethod
    async def listen_connections(cls, host: str, port: int) -> None:
        ...  # TODO produces

        # await send_signal(CLIENT_CONNECTED)
        # await send_signal(CLIENT_DISCONNECTED)


class _Layout:
    _current: list[Component] = []
    _storage: VarStorage = {}

    @classmethod
    def append(cls, comp: Component) -> None:
        cls._current.append(comp)

    @classmethod
    def get_current(cls) -> tuple[HTML, dict]:
        html = ''
        for comp in cls._current:
            html += comp.html


# 6. App

class App:
    type Server = _Server
    type Layout = _Layout
    on = on_signal

    def run(self, **params: dict) -> None:
        asyncio.run(self.main_task(**params))

    async def main_task(
        self,
        layout: list[Component],
        host: str = 'localhost',
        port: int = 5000,
    ) -> None:
        for comp in layout: self.Layout.append(comp)

        self.on(CLIENT_CONNECTED)(self.on_client_connected)
        self.on(CLIENT_DISCONNECTED)(self.on_client_disconnected)
        self.on(LAYOUT_CLEAN)(self.on_layout_clean)

        await self.Server.listen_connections(host, port)

    async def on_client_connected(self, sig: CLIENT_CONNECTED) -> None:
        ...

    async def on_client_disconnected(self, sig: CLIENT_DISCONNECTED) -> None:
        ...

    async def on_layout_clean(self, sig: LAYOUT_CLEAN) -> None:
        ...
