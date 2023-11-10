import asyncio
import logging
import typing as t
from collections import defaultdict

logger = logging.getLogger(__name__)


Signal: t.TypeAlias = str
SignalData: t.TypeAlias = dict
SignalHandler: t.TypeAlias = t.Callable[[SignalData], t.Awaitable[None]]

Command: t.TypeAlias = str
CommandParams: t.TypeAlias = dict


# server-level signals
SERVER_STARTUP: Signal = 'SERVER_STARTUP'
SERVER_SHUTDOWN: Signal = 'SERVER_SHUTDOWN'
CLIENT_CONNECTED: Signal = 'CLIENT_CONNECTED'
CLIENT_DISCONNECTED: Signal = 'CLIENT_DISCONNECTED'
CMD_CALL: Signal = 'CMD_CALL'

# app-level signals
LAYOUT_CLEAN: Signal = 'LAYOUT_CLEAN'
LAYOUT_UPDATED: Signal = 'LAYOUT_UPDATED'
EVERY_SECOND: Signal = 'EVERY_SECOND'
VAR_UPDATED: Signal = 'VAR_UPDATED'


# commands
C_CLEAR_LAYOUT: Command = 'clear_layout'
C_APPEND_COMPONENT: Command = 'append_component'
C_UPDATE_VAR: Command = 'update_var'


_messages: asyncio.Queue[tuple[Signal, SignalData]] = asyncio.Queue()
_handlers: dict[Signal : set[SignalHandler]] = defaultdict(set)


async def emit_signal(signal: Signal, data: SignalData | None = None) -> None:
    await _messages.put((signal, data or {}))


async def call_command(command: Command, params: CommandParams = None) -> None:
    await emit_signal(CMD_CALL, {'command': command, 'params': params or {}})


def add_handler(signal: Signal, handler: SignalHandler) -> None:
    _handlers[signal].add(handler)


async def listener_task():
    asyncio.create_task(on_tick())

    try:
        while True:
            signal, data = await _messages.get()
            logger.info(f'{signal}  {data}')

            if signal not in _handlers:
                continue

            for handler in _handlers[signal]:
                await handler(data)

    except Exception as e:
        logger.exception(e)


async def on_tick():
    while True:
        await asyncio.sleep(1)
        if EVERY_SECOND not in _handlers:
            continue

        for handler in _handlers[EVERY_SECOND]:
            await handler({})
