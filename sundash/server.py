import asyncio
from dataclasses import dataclass
import json
import logging
import subprocess
import typing as t

import uvicorn
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.staticfiles import StaticFiles
from starlette.types import Receive
from starlette.types import Scope
from starlette.types import Send
from starlette.websockets import WebSocket
from starlette.websockets import WebSocketDisconnect

from .core import SIGNAL
from .core import COMMAND
from .core import HTML
from .core import reg_signal
from .logging import log_config

logger = logging.getLogger(__name__)


@dataclass
class CLIENT_CONNECTED(SIGNAL):
    client_id: int


@dataclass
class CLIENT_DISCONNECTED(SIGNAL):
    client_id: int


_id = 0


def new_id() -> int:
    global _id
    _id += 1
    return _id


class WSConnection:
    def __init__(self, socket: WebSocket) -> None:
        self.id = new_id()
        self.socket = socket

    async def send(self, message: str) -> None:
        await self.socket.send_text(message)

    async def send_command(self, command: COMMAND) -> None:
        cmd_name = command.__class__.__name__
        cmd_params = json.dumps(command.__dict__)
        await self.send(f'{cmd_name} {cmd_params}')


class Server:
    _EXIT_CODE = 1
    ALLOWED_STATIC_FILES = (".html", "css", ".js", ".map", ".ico")

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
        logger.info(f"Starting server at http://{self.host}:{self.port}/")

        server_task = self.server_task(
            host=self.host,
            port=self.port,
            log_level="debug",
            log_config=log_config,
        )
        # listener_task = self.listener_task()

        try:
            # await run_tasks(server_task, listener_task)
            await run_tasks(server_task)
        finally:
            logger.info('Shutting down server')

    # async def listener_task(cls) -> None:
    #     while command := await listen_commands():
    #         logger.info(f'RECV_CMD {command.message}')

    async def server_task(self, **config_params: dict) -> None:
        config = uvicorn.Config(app=self, **config_params)
        server = self._ASGIServer(config=config)
        await server.serve()

    async def __call__(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        if scope["type"] == "lifespan":
            exit_code = await self._handle_lifespan(scope, receive, send)
            if exit_code:
                return

        elif scope["type"] == "http":
            await self._handle_http_request(scope, receive, send)

        elif scope["type"] == "websocket":
            await self._handle_websocket_request(scope, receive, send)

        else:
            response = HTMLResponse(
                content="<b>Not allowed</b>", status_code=405
            )
            await response(scope, receive, send)

    async def _handle_lifespan(
        self, scope: Scope, receive: Receive, send: Send
    ) -> int | None:
        message = await receive()

        if message["type"] == "lifespan.startup":
            await send({"type": "lifespan.startup.complete"})
            return None

        elif message["type"] == "lifespan.shutdown":
            await send({"type": "lifespan.shutdown.complete"})
            return self._EXIT_CODE

        else:
            return None

    async def _handle_http_request(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:

        request = Request(scope, receive, send)
        path = request.url.components.path

        if any([path.endswith(ext) for ext in self.ALLOWED_STATIC_FILES]):
            static_files = StaticFiles(directory="static")
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
        self._connections[conn.id] = conn

        await reg_signal(CLIENT_CONNECTED(client_id=conn.id))
        try:
            while True:
                message = await socket.receive_text()  # noqa
                logger.info(f'RECV MSG: {message}')

                # signal, data = message.split(" ", 1)
                # await emit_signal(signal=signal, data=json.loads(data))

        except WebSocketDisconnect:
            pass

        finally:
            await reg_signal(CLIENT_DISCONNECTED(client_id=conn.id))
            self._connections.pop(conn.id)


def build_ui():
    logger.info("Building web UI...")
    # FIXME control output and redirect to logger
    subprocess.run(["npm", "run", "build"])


async def run_tasks(*tasks: t.Iterable[t.Awaitable]) -> None:
    await asyncio.wait(
        [asyncio.create_task(t) for t in tasks],
        return_when=asyncio.FIRST_COMPLETED,
    )


if __name__ == '__main__':
    server = Server()

    build_ui()
    asyncio.run(server.task())
