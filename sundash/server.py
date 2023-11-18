import contextvars
import json
import logging
import subprocess
from dataclasses import dataclass

import uvicorn
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.staticfiles import StaticFiles
from starlette.types import Receive
from starlette.types import Scope
from starlette.types import Send
from starlette.websockets import WebSocket
from starlette.websockets import WebSocketDisconnect

from .core import COMMAND
from .core import HTML
from .core import SIGNAL
from .core import emit_signal
from .core import signals
from .logging import log_config

logger = logging.getLogger(__name__)


@dataclass
class CLIENT_CONNECTED(SIGNAL):
    id: int


@dataclass
class CLIENT_DISCONNECTED(SIGNAL):
    id: int


class WSConnection:
    __id = 0

    @classmethod
    def new_id(cls) -> int:
        cls.__id += 1
        return cls.__id

    def __init__(self, socket: WebSocket) -> None:
        self.id = self.__class__.new_id()
        self.socket = socket

    async def receive_signal(self) -> None:
        message = await self.socket.receive_text()

        signal_name, data = message.split(" ", 1)
        signal_cls = signals[signal_name]
        data = json.loads(data)

        await emit_signal(signal_cls(**data))

    async def send_command(self, cmd: COMMAND) -> None:
        cmd_name = cmd.__class__.__name__
        cmd_params = json.dumps(cmd.__dict__)
        await self.socket.send_text(f'{cmd_name} {cmd_params}')


_conn = contextvars.ContextVar('_conn', default=None)


def set_connection(conn: WSConnection) -> None:
    _conn.set(conn)


def get_connection() -> WSConnection:
    return _conn.get()


class Server:
    _EXIT_CODE = 1
    ALLOWED_STATIC_FILES = ('.html', 'css', '.js', '.map', '.ico')

    class _ASGIServer(uvicorn.Server):
        def install_signal_handlers(self) -> None:
            # replace default signal catch
            # because I want `Ctrl + C` to work correct
            pass

    def __init__(
        self,
        host: str = 'localhost',
        port: int = 5000,
        html_title: str = 'Sundash',
    ):
        self.host = host
        self.port = port
        self.html_title = html_title

        self._index_html: str = None
        self._connections: dict[int: WSConnection] = {}

    async def task(self) -> None:
        build_ui()
        logger.info(f'Starting server at http://{self.host}:{self.port}/')

        config = uvicorn.Config(
            app=self,
            host=self.host,
            port=self.port,
            log_level='debug',
            log_config=log_config,
        )
        server = self._ASGIServer(config=config)
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
            response = HTMLResponse(
                content='<b>Not allowed</b>', status_code=405
            )
            await response(scope, receive, send)

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

        request = Request(scope, receive, send)
        path = request.url.components.path

        if any([path.endswith(ext) for ext in self.ALLOWED_STATIC_FILES]):
            static_files = StaticFiles(directory='static')
            await static_files(scope, receive, send)

        else:
            content = self._get_index_html_content()
            response = HTMLResponse(content=content, status_code=200)
            await response(scope, receive, send)

    def _get_index_html_content(self) -> HTML:
        if not self._index_html:
            with open('static/index.html') as f:
                self._index_html = (
                    f.read().replace('{{ _app_title }}', self.html_title)
                )
        return self._index_html

    async def _handle_websocket_request(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        socket = WebSocket(scope=scope, receive=receive, send=send)
        await socket.accept()

        conn = WSConnection(socket)
        set_connection(conn)

        try:
            await emit_signal(CLIENT_CONNECTED(id=conn.id))
            while True:
                await conn.receive_signal()

        except WebSocketDisconnect:
            pass

        except Exception as exc:
            logger.exception(exc)

        finally:
            await emit_signal(CLIENT_DISCONNECTED(id=conn.id))
            set_connection(None)


def build_ui():
    logger.info('Building web UI...')
    # FIXME control output and redirect to logger
    subprocess.run(['npm', 'run', 'build'])
