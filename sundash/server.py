import asyncio
import json
import logging
import os
import typing as t

import uvicorn
from starlette.responses import HTMLResponse
from starlette.staticfiles import StaticFiles
from starlette.types import Receive
from starlette.types import Scope
from starlette.types import Send
from starlette.websockets import WebSocket
from starlette.websockets import WebSocketDisconnect

from . import core
from .logging import log_config
from .messages import Command
from .messages import Event

logger = logging.getLogger(__name__)


class Session(core.AbstractSession):
    __id = 0

    @classmethod
    def new_id(cls) -> int:
        cls.__id += 1
        return cls.__id

    def __init__(self, socket: WebSocket):
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

        except WebSocketDisconnect:
            raise core.SessionClosed

    async def _send_command(self, cmd: Command):
        cmd_name = cmd.__class__.__name__
        cmd_params = json.dumps(cmd.__dict__)
        await self.socket.send_text(f'{cmd_name} {cmd_params}')


class _ASGIServer(uvicorn.Server):
    # Shutdown default OS signals catch
    # It should be implemented on another layer
    def install_signal_handlers(self) -> None: ...


response_404 = HTMLResponse(content='<b>404</b> Not found', status_code=404)
response_405 = HTMLResponse(content='<b>405</b> Not allowed', status_code=405)


type _ServerCallback[T] = t.Callable[[T], t.Awaitable[None]]


async def _dummy_callback(): ...
async def _dummy_event_callback(event: Event): ...


class Server:
    _EXIT_CODE = 1
    ALLOWED_STATIC_FILES = ('.html', 'css', '.js', '.map', '.ico')

    STATIC_DIR = os.path.dirname(__file__) + '/web'
    INDEX_HTML_PATH = STATIC_DIR + '/index.html'

    def __init__(
        self,
        *,
        host: str = 'localhost',
        port: int = 5000,
        on_session_open: _ServerCallback[None] = _dummy_callback,
        on_session_close: _ServerCallback[None] = _dummy_callback,
        on_event: _ServerCallback[Event] = _dummy_event_callback,
    ):
        self.host, self.port = host, port
        self._static_files = StaticFiles(directory=self.STATIC_DIR)

        self.on_session_open = on_session_open
        self.on_session_close = on_session_close
        self.on_event = on_event

    async def run(self) -> None:
        config = uvicorn.Config(
            app=self,
            host=self.host,
            port=self.port,
            log_level='debug',
            log_config=log_config,
        )
        server = _ASGIServer(config=config)

        logger.info('Starting server')
        try:
            await server.serve()
        finally:
            logger.info('Shutting down server')

    async def __call__(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        if scope['type'] == 'lifespan':
            exit_code = await self._handle_lifespan(scope, receive, send)
            if exit_code:
                return

        elif scope['type'] == 'http':
            await self._handle_http_request(scope, receive, send)

        elif scope['type'] == 'websocket':
            await self._handle_websocket_request(scope, receive, send)

        else:
            await response_405(scope, receive, send)

    async def _handle_lifespan(
        self, scope: Scope, receive: Receive, send: Send
    ) -> int | None:
        message = await receive()

        if message['type'] == 'lifespan.startup':
            await send({'type': 'lifespan.startup.complete'})
            return None

        elif message['type'] == 'lifespan.shutdown':
            await send({'type': 'lifespan.shutdown.complete'})
            return self._EXIT_CODE

        else:
            return None

    async def _handle_http_request(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        path = self._static_files.get_path(scope)

        if path == '.':
            resp = await self._static_files.get_response(
                self.INDEX_HTML_PATH, scope
            )
            await resp(scope, receive, send)

        elif any([path.endswith(ext) for ext in self.ALLOWED_STATIC_FILES]):
            await self._static_files(scope, receive, send)

        else:
            await response_404(scope, receive, send)

    async def _handle_websocket_request(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        socket = WebSocket(scope=scope, receive=receive, send=send)
        await socket.accept()

        with Session(socket) as session:
            await self.on_session_open()
            try:
                while True:
                    event = await session.listen_event()
                    await self.on_event(event=event)

            except (core.SessionClosed, asyncio.CancelledError):
                pass

            except Exception as e:
                logger.exception(e)

            finally:
                await self.on_session_close()
