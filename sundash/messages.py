from __future__ import annotations

import abc
import dataclasses as dc


class _Message(abc.ABC):
    type Name = str
    type T = type[_Message]

    _cls = property(lambda self: self.__class__)
    _name = property(lambda self: self._cls.__name__)
    _data = property(lambda self: dc.asdict(self))


@dc.dataclass
class Event(_Message):
    """`Client` -> `Server` message
    """
    type T = type[Event]

    @classmethod
    def get_by_name(cls, name: Event.Name) -> Event.T:
        return {ec.__name__: ec for ec in Event.__subclasses__()}[name]


@dc.dataclass
class Command(_Message):
    """`Server` -> `Client` message
    """
    type T = type[Command]
