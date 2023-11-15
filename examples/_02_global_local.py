from dataclasses import dataclass

from sundash.core import SIGNAL
from sundash.core import on


class Counter:
    @dataclass
    class PLUS_BTN_CLICK(SIGNAL): ...

    html = '<b>{{ count }}</b><button>+</button>'

    @on(PLUS_BTN_CLICK)
    async def on_plus_click():
        ...
