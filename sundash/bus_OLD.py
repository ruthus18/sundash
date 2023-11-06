"""Service bus to communicate client and server. Using as internal tool for main communtication in realtime.

Bus operates with 2 main abstraction for messages: Signal and Command

Signal
    - event that something happened. Emiting by server and by client in equal way

Command
    - request to do something from server to client. No need to response.
    CLIENT_DISCONNECTED = enum.auto()
"""

from __future__ import annotations

import enum
import json
import typing as t
from dataclasses import dataclass


class Signal(enum.StrEnum):
    def _generate_next_value_(name: str, *_, **__) -> str:
        return name.upper()

    CLIENT_CONNECTED = enum.auto()
    CLIENT_DISCONNECTED = enum.auto()
    LAYOUT_CLEAN = enum.auto()
    LAYOUT_UPDATED = enum.auto()
    EVERY_SECOND = enum.auto()
    VAR_UPDATED = enum.auto()

    def __repr__(self) -> str:
        return self.value


class Command(enum.StrEnum):
    clear_layout = enum.auto()
    append_component = enum.auto()
    update_var = enum.auto()


SignalData: t.TypeAlias = dict
SignalHandler: t.TypeAlias = t.Callable[[SignalData], t.Awaitable[None]]


@dataclass
class Request:
    signal: Signal
    data: SignalData

    @classmethod
    def parse(cls, request_raw: str) -> Request:
        signal, data = request_raw.split(" ", 1)
        return cls(signal=Signal(signal), data=json.loads(data))


class BusManager:
    # TODO: Unfinished abstraction, need to clarify the interface to use as tool

    _signal_to_handler: dict[Signal, SignalHandler] = {}

    def add_handler(self, signal: Signal, handler_f: SignalHandler) -> None:
        self._signal_to_handler[signal] = handler_f

    async def _handle_signal(self, signal: Signal, signal_data: SignalData) -> None:
        handler = self._signal_to_handler.get(signal)
        if not handler:
            return

        await handler(signal_data)

    async def handle_request(self, request_raw: str) -> None:
        request = Request.parse(request_raw)
        await self._handle_signal(request.signal, request.data)
