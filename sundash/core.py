from __future__ import annotations

import abc
import logging
import typing as t
from contextvars import ContextVar

from .messages import Command
from .messages import Event

logger = logging.getLogger(__name__)


type HTML = str


class SessionClosed(Exception): ...


_session: ContextVar[AbstractSession] = ContextVar('session')


class AbstractSession(abc.ABC):
    type ID = str
    id: ID

    def __enter__(self):
        _session.set(self)
        return self

    def __exit__(self, *_):
        _session.set(None)

    @classmethod
    def get(cls) -> t.Self:
        return _session.get()

    @abc.abstractmethod
    async def _listen_event(self) -> Event: ...

    @abc.abstractmethod
    async def _send_command(self, cmd: Command) -> None: ...

    async def listen_event(self) -> Event:
        event = await self._listen_event()

        logger.info(f'[{self.id}] >> {event._name}  {event._data}')
        return event

    async def send_command(self, cmd: Command) -> None:
        await self._send_command(cmd)

        fmt_data = cmd._data
        # TODO: Need to move to logging level
        if 'html' in fmt_data:
            fmt_data['html'] = '...'

        logger.info(f'[{self.id}] << {cmd._name}  {fmt_data}')
