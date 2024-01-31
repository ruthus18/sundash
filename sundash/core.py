from __future__ import annotations

import logging
import typing as t
from abc import ABC
from dataclasses import dataclass

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


def on(signal_cls: SIGNAL.T) -> AnyCallback:
    def wrapper(func: AnyCallback) -> AnyCallback:
        self = _get_f_self(func)
        cls_name = _get_f_cls_name(func)

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
            Component.schedule_subscribe(signal_cls, cls_name, func.__name__)

        elif self is not None and not cls_name:
            raise RuntimeError  # no way...

        return func

    return wrapper
