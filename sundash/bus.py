import asyncio
import logging
import typing as t
from collections import defaultdict

logger = logging.getLogger(__name__)


Signal: t.TypeAlias = str
SignalData: t.TypeAlias = dict
SignalHandler: t.TypeAlias = t.Callable[[SignalData], t.Awaitable[None]]


SERVER_STARTUP: Signal = 'SERVER_STARTUP'
SERVER_SHUTDOWN: Signal = 'SERVER_SHUTDOWN'
CLIENT_CONNECTED: Signal = 'CLIENT_CONNECTED'
CLIENT_DISCONNECTED: Signal = 'CLIENT_DISCONNECTED'
CMD_CALL: Signal = 'CMD_CALL'

LAYOUT_CLEAN: Signal = 'LAYOUT_CLEAN'
LAYOUT_UPDATED: Signal = 'LAYOUT_UPDATED'
EVERY_SECOND: Signal = 'EVERY_SECOND'
VAR_UPDATED: Signal = 'VAR_UPDATED'


_messages: asyncio.Queue[tuple[Signal, SignalData]] = asyncio.Queue()
_handlers: dict[Signal : set[SignalHandler]] = defaultdict(set)


async def emit_signal(signal: Signal, data: SignalData | None = None) -> None:
    await _messages.put((signal, data or {}))


def add_handler(signal: Signal, handler: SignalHandler) -> None:
    _handlers[signal].add(handler)


async def listener_task():
    while True:
        signal, data = await _messages.get()
        logger.info(f'{signal}  {data}')

        if signal not in _handlers:
            continue

        for handler in _handlers[signal]:
            await handler(data)
