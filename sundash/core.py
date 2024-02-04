from __future__ import annotations

import abc
import asyncio
import logging
import typing as t
import dataclasses

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

        logger.info(f'[{self.id}] << {cmd._name}  {fmt_data}')


@dataclasses.dataclass
class MessageContext:
    session: AbstractSession


class _MESSAGE(abc.ABC):
    type Name = str
    type T = type[_MESSAGE]

    _ctx: MessageContext
    _name = property(lambda self: self.__class__.__name__)
    _data = property(lambda self: dataclasses.asdict(self))


@dataclasses.dataclass
class EVENT(_MESSAGE):
    """`Client` -> `Server` message
    """
    type T = type[EVENT]

    @classmethod
    def get_by_name(cls, name: EVENT.Name) -> EVENT.T:
        return {ec.__name__: ec for ec in EVENT.__subclasses__()}[name]


@dataclasses.dataclass
class COMMAND(_MESSAGE):
    """`Server` -> `Client` message
    """
    type T = type[COMMAND]


async def _dummy_callback(**kwargs): ...


_system_callbacks = {
    'on_session_open': _dummy_callback,  # <- session
    'on_session_close': _dummy_callback,  # <- session
    'on_event': _dummy_callback,  # <- event
}


def register_system_callback(name: str, callback: t.Awaitable):
    _system_callbacks[name] = callback


async def run_system_callback(name: str, **kwargs):
    await _system_callbacks[name](**kwargs)


async def on_session(session: AbstractSession):
    await run_system_callback('on_session_open', session=session)
    try:
        while True:
            event = await session.listen_event()
            event._ctx = MessageContext(session=session)

            await run_system_callback('on_event', event=event)

    except (SessionClosed, asyncio.CancelledError):
        pass

    except Exception as e:
        logger.exception(e)

    finally:
        await run_system_callback('on_session_close', session=session)
