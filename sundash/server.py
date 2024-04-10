import asyncio
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

from .logging import log_config
from .messages import Event
from .sessions import Session
from .sessions import AbstractSession
from .sessions import SessionClosed

logger = logging.getLogger(__name__)

type _ServerCallback[T] = t.Callable[[T], t.Awaitable[None]]

EXIT_CODE = 1

response_404 = HTMLResponse(content='<b>404</b> Not found', status_code=404)
response_405 = HTMLResponse(content='<b>405</b> Not allowed', status_code=405)


class _ASGIServer(uvicorn.Server):
    # Shutdown default OS signals catch
    # It should be implemented on another layer
    def install_signal_handlers(self) -> None: ...


class Server:
    ALLOWED_STATIC_FILES = ('.html', 'css', '.js', '.map', '.ico')

    STATIC_DIR = os.path.dirname(__file__) + '/web'
    INDEX_HTML_PATH = STATIC_DIR + '/index.html'

    def __init__(
        self,
        *,
        on_session_open: _ServerCallback[None],
        on_session_close: _ServerCallback[None],
        on_event: _ServerCallback[Event],
        host: str = 'localhost',
        port: int = 5000,
        session_cls: type[AbstractSession] = Session,
    ):
        self.host, self.port = host, port
        self.static_files = StaticFiles(directory=self.STATIC_DIR)

        self.on_session_open = on_session_open
        self.on_session_close = on_session_close
        self.on_event = on_event
        self.session_cls = session_cls

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
            exit_code = await self.handle_lifespan(scope, receive, send)
            if exit_code:
                return

        elif scope['type'] == 'http':
            await self.handle_http_request(scope, receive, send)

        elif scope['type'] == 'websocket':
            await self.handle_websocket_request(scope, receive, send)

        else:
            await response_405(scope, receive, send)

    async def handle_lifespan(
        self, scope: Scope, receive: Receive, send: Send
    ) -> int | None:
        message = await receive()

        if message['type'] == 'lifespan.startup':
            await send({'type': 'lifespan.startup.complete'})
            return None

        elif message['type'] == 'lifespan.shutdown':
            await send({'type': 'lifespan.shutdown.complete'})
            return EXIT_CODE

        else:
            return None

    async def handle_http_request(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        path = self.static_files.get_path(scope)

        if path == '.':
            resp = await self.static_files.get_response(
                self.INDEX_HTML_PATH, scope
            )
            await resp(scope, receive, send)

        elif any([path.endswith(ext) for ext in self.ALLOWED_STATIC_FILES]):
            await self.static_files(scope, receive, send)

        else:
            await response_404(scope, receive, send)

    async def handle_websocket_request(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        socket = WebSocket(scope=scope, receive=receive, send=send)
        await socket.accept()

        with self.session_cls(socket) as session:
            await self.on_session_open()
            try:
                while True:
                    event = await session.listen_event()
                    await self.on_event(event=event)

            except (SessionClosed, asyncio.CancelledError):
                pass

            except Exception as e:
                logger.exception(e)

            finally:
                await self.on_session_close()
