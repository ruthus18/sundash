from __future__ import annotations

import asyncio
import logging
import typing as t
from abc import ABC
from dataclasses import dataclass

from . import _utils

logger = logging.getLogger(__name__)


type HTML = str


# 1. Bus


class _MESSAGE(ABC):
    type Name = str

    _name = property(lambda self: self.__class__.__name__)
    _data = property(lambda self: self.__dict__)


@dataclass
class SIGNAL(_MESSAGE):
    type T = type[SIGNAL]


@dataclass
class EVERY_SECOND(SIGNAL): ...


@dataclass
class COMMAND(_MESSAGE):
    type T = type[COMMAND]


get_signals_map = lambda: {s.__name__: s for s in SIGNAL.__subclasses__()}


async def emit_signal(sig: SIGNAL | SIGNAL.T) -> None:
    if not isinstance(sig, SIGNAL): sig = sig()

    conn = get_connection()
    logger.info(f'[{conn.id}] -> {sig._name}  {sig._data}')

    for callback in _callbacks.get(sig._name, set()):
        await callback(sig)


from .server import get_connection


async def send_command(cmd: COMMAND | type[COMMAND]) -> None:
    if not isinstance(cmd, COMMAND): cmd = cmd()

    conn = get_connection()
    logger.info(f'[{conn.id}] <- {cmd._name}  {cmd._data}')

    await conn.send_command(cmd)


# 2. Callbacks


type _FunctionCallback = t.Callable[[object, SIGNAL], None]
type _ClassCallback = t.Callable[[SIGNAL], None]

type ClassCallback = t.Awaitable[_ClassCallback]
type FunctionCallback = t.Awaitable[_FunctionCallback]

type AnyCallback = FunctionCallback | ClassCallback
type Callback = FunctionCallback


_callbacks: dict[SIGNAL.Name, set[Callback]] = {}


def subscribe(signal_cls: SIGNAL.T, callback: Callback) -> None:
    sig_name = signal_cls.__name__
    if sig_name not in _callbacks:
        _callbacks[sig_name] = set()

    _callbacks[sig_name].add(callback)


def unsubscribe(signal_cls: SIGNAL.T, callback: Callback) -> None:
    sig_name = signal_cls.__name__
    _callbacks[sig_name].remove(callback)


def on(signal_cls: SIGNAL.T) -> AnyCallback:
    def wrapper(func: AnyCallback) -> AnyCallback:
        self = _utils.get_f_self(func)
        cls_name = _utils.get_f_cls_name(func)

        if self is not None and cls_name:
            # `on` called for `self.method` -> valid callback
            subscribe(signal_cls, func)

        elif self is None and not cls_name:
            # `on` called for module function -> valid callback
            subscribe(signal_cls, func)

        elif self is None and cls_name:
            # `on` called for class function -> not valid callback...
            # only valid in component interface
            from .layout import Component
            Component.schedule_callback(signal_cls, cls_name, func.__name__)

        elif self is not None and not cls_name:
            raise RuntimeError  # no way...

        return func

    return wrapper


# 3. App


from .layout import Component
from .layout import Layout
from .server import Server


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

        self.server = Server()
        await self.server.task()
