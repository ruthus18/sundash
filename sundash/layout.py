import functools
import typing as t
from dataclasses import dataclass
from dataclasses import is_dataclass

from .core import COMMAND
from .core import HTML
from .core import SIGNAL
from .core import Callback
from .core import on
from .core import send_command
from .core import subscribe
from .core import unsubscribe
from .server import CLIENT_CONNECTED
from .server import CLIENT_DISCONNECTED
from .server import get_connection


class Var[T]:
    type Key = str
    type Value = T


type VarStorage = dict[Var.Key, Var.Value]


@dataclass
class CLEAR_LAYOUT(COMMAND): ...


@dataclass
class LAYOUT_UPDATED(SIGNAL): ...


@dataclass
class LAYOUT_CLEAN(SIGNAL): ...


@dataclass
class VAR_SET(SIGNAL): ...


@dataclass
class SET_VAR(COMMAND):
    key: Var.Key
    value: Var.Value


@dataclass
class UPDATE_LAYOUT(COMMAND):
    html: HTML
    vars: VarStorage


class Component:
    html: HTML = ''

    @dataclass
    class Vars: ...

    _callbacks: set[tuple[SIGNAL.T, str, str]] = set()

    def __init__(self):
        if not is_dataclass(self.Vars):
            raise RuntimeError

        # TODO: init procedural values
        self.vars: dict = self.Vars().__dict__
        self.conn_id = get_connection().id

    def callback_wrapper(self, callback: Callback) -> Callback:
        async def wrapper(sig: SIGNAL):
            conn_id = get_connection().id
            if conn_id != self.conn_id:
                return
            await callback(sig)

        return functools.wraps(callback)(wrapper)

    @classmethod
    def schedule_callback(
        cls, signal_cls: SIGNAL.T, cls_name: str, func_name: str
    ) -> None:
        cls._callbacks.add((signal_cls, cls_name, func_name))

    def callbacks_map(self) -> t.Generator:
        cls = self.__class__
        for signal_cls, cls_name, func_name in self.__class__._callbacks:
            if cls.__name__ != cls_name: continue

            callback = getattr(self, func_name)
            yield signal_cls, callback

    def subscribe_callbacks(self) -> None:
        for signal_cls, callback in self.callbacks_map():
            subscribe(signal_cls, self.callback_wrapper(callback))

    def unsubscribe_callbacks(self) -> None:
        for signal_cls, callback in self.callbacks_map():
            unsubscribe(signal_cls, callback)

    async def set(self, key: Var.Key, value: Var.Value) -> None:
        self.vars[key] = value
        await send_command(SET_VAR(key=key, value=value))


class Layout(list[type[Component]]):
    _sessions: dict[int, list[Component]] = {}

    def __init__(self):
        super().__init__()

        on(CLIENT_CONNECTED)(self.open_session)
        on(CLIENT_DISCONNECTED)(self.close_session)

    def append(self, item: type[Component] | HTML) -> None:
        if isinstance(item, str):
            class HTMLComponent(Component):
                html = item

            comp = HTMLComponent
        else:
            comp = item

        super().append(comp)

    async def open_session(self, _) -> None:
        layout = []
        for comp_cls in self:
            comp = comp_cls()
            comp.subscribe_callbacks()
            layout.append(comp)

        data = {}
        for comp in layout:
            data.update(**comp.vars)

        html = ''.join((c.html for c in layout))

        id = get_connection().id
        self._sessions[id] = layout

        await send_command(UPDATE_LAYOUT(html=html, vars=data))

    async def close_session(self, _) -> None:
        id = get_connection().id
        for comp in self._sessions[id]:
            comp.unsubscribe_callbacks()

        self._sessions.pop(id)
