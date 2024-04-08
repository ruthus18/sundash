from __future__ import annotations

import abc
import json
import logging
import typing as t
from contextvars import ContextVar

from starlette import websockets

from .messages import Command
from .messages import Event

logger = logging.getLogger(__name__)


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

        logger.info(f'[{self.id}] E >> {event._name:>20}  {event._data}')
        return event

    async def send_command(self, cmd: Command) -> None:
        await self._send_command(cmd)

        fmt_data = cmd._data
        # TODO: Need to move to logging level
        if 'html' in fmt_data:
            fmt_data['html'] = '...'

        logger.info(f'[{self.id}] C << {cmd._name:>20}  {fmt_data}')


class Session(AbstractSession):
    __id = 0

    @classmethod
    def new_id(cls) -> int:
        cls.__id += 1
        return cls.__id

    def __init__(self, socket: websockets.WebSocket):
        self.id = str(self.__class__.new_id())
        self.socket = socket

    def _parse_event(self, message: str) -> Event:
        name, data = message.split(" ", 1)
        event_cls = Event.get_by_name(name)

        return event_cls(**json.loads(data))

    async def _listen_event(self) -> Event:
        try:
            message = await self.socket.receive_text()
            return self._parse_event(message)

        except websockets.WebSocketDisconnect:
            raise SessionClosed

    async def _send_command(self, cmd: Command):
        cmd_name = cmd.__class__.__name__
        cmd_params = json.dumps(cmd.__dict__)
        await self.socket.send_text(f'{cmd_name} {cmd_params}')
