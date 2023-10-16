from __future__ import annotations

import enum
from dataclasses import dataclass

import simplejson as json


class Signal(enum.StrEnum):
    CLIENT_CONNECTED = enum.auto()
    CLIENT_DISCONNECTED = enum.auto()
    LAYOUT_CLEAN = enum.auto()
    LAYOUT_UPDATED = enum.auto()
    EVERY_SECOND = enum.auto()
    VAR_UPDATED = enum.auto()

    def _generate_next_value_(name: str, *_, **__) -> str:
        return name.upper()

    def __repr__(self) -> str:
        return self.value


class Command(enum.StrEnum):
    clear_layout = enum.auto()
    append_component = enum.auto()
    update_var = enum.auto()


@dataclass
class Request:
    signal: Signal
    data: dict

    @classmethod
    def parse(cls, request_raw: str) -> Request:
        signal, data = request_raw.split(" ", 1)
        return cls(
            signal=Signal(signal),
            data=json.loads(data),
        )


class BusManager:
    def handle_request(self, request_raw: str) -> Request:
        return Request.parse(request_raw)  # а зачем? :^)
