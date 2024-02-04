from __future__ import annotations

import abc
import asyncio
import contextlib
import logging
import typing as t
from dataclasses import asdict
from dataclasses import dataclass

logger = logging.getLogger(__name__)


type HTML = str


class SessionClosed(Exception): ...


class AbstractSession(abc.ABC):
    type ID = str
    id: ID

    @abc.abstractmethod
    async def _listen_event(self) -> EVENT: ...

    @abc.abstractmethod
    async def _send_command(self, cmd: COMMAND) -> None: ...

    async def listen_event(self) -> EVENT:
        event = await self._listen_event()

        logger.info(f'[{self.id}] >> {event._name}  {event._data}')
        return event

    async def send_command(self, cmd: COMMAND):
        await self._send_command(cmd)

        fmt_data = cmd._data
        if 'html' in fmt_data:
            fmt_data['html'] = '...'

        logger.info(f'[{self.id}] >> {cmd._name}  {fmt_data}')


@dataclass
class MessageContext:
    session: AbstractSession


class _MESSAGE(abc.ABC):
    type Name = str
    type T = type[_MESSAGE]

    _ctx: MessageContext

    _cls = property(lambda self: self.__class__)
    _name = property(lambda self: self._cls.__name__)
    _data = property(lambda self: asdict(self))


@dataclass
class EVENT(_MESSAGE):
    """`Client` -> `Server` message
    """
    type T = type[EVENT]

    @classmethod
    def get_by_name(cls, name: EVENT.Name) -> EVENT.T:
        return {ec.__name__: ec for ec in EVENT.__subclasses__()}[name]


@dataclass
class COMMAND(_MESSAGE):
    """`Server` -> `Client` message
    """
    type T = type[COMMAND]


async def _dummy_callback(**kwargs): ...


_system_callbacks = {
    'on_session_open': _dummy_callback,  # <- session
    'on_session_closed': _dummy_callback,  # <- session
    'on_event': _dummy_callback,  # <- event
}


def register_system_callback(name: str, callback: t.Awaitable):
    _system_callbacks[name] = callback


async def run_system_callback(name: str, **kwargs):
    await _system_callbacks[name](**kwargs)


async def _listen_events(session: AbstractSession, events_q: asyncio.Queue):

    with contextlib.suppress(SessionClosed, asyncio.CancelledError):
        while True:
            event = await session.listen_event()
            event._ctx = MessageContext(session=session)

            await run_system_callback('on_event', event=event)
            await events_q.put(event)


async def _dispatch_events(session: AbstractSession, events_q: asyncio.Queue):

    with contextlib.suppress(asyncio.CancelledError):
        while True:
            event = await events_q.get()
            for callback in get_event_callbacks(event._name):
                await callback(event)


async def on_session(
    session: AbstractSession,
    tasks: tuple[t.Awaitable] = (_listen_events, _dispatch_events)
):
    await run_system_callback('on_session_open', session=session)

    events_q = asyncio.Queue()
    try:
        await asyncio.wait([
            asyncio.create_task(t(session, events_q)) for t in tasks
        ])
    except asyncio.CancelledError:
        pass
    finally:
        await run_system_callback('on_session_closed', session=session)


type EventCallback = t.Awaitable[t.Callable[[EVENT], None]]

_callbacks: dict[EVENT.Name, list[EventCallback]] = {}


def get_event_callbacks(event_name: EVENT.Name) -> list[EventCallback]:
    return _callbacks.get(event_name) or []


def register_event_callback(event_name: EVENT.Name, callback: EventCallback):
    event_callbacks = get_event_callbacks(event_name)
    event_callbacks.append(callback)

    _callbacks[event_name] = event_callbacks


def on(event_cls: EVENT.T) -> EventCallback:
    def wrapper(callback: EventCallback) -> EventCallback:
        register_event_callback(event_cls.__name__, callback)
        return callback

    return wrapper
