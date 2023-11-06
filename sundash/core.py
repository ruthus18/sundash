from __future__ import annotations

import asyncio
import functools
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

from .bus import CLIENT_CONNECTED
from .bus import CLIENT_DISCONNECTED
from .bus import SERVER_SHUTDOWN
from .bus import SERVER_STARTUP
from .bus import Signal
from .bus import SignalData
from .bus import SignalHandler
from .bus import add_handler
from .bus import emit_signal
from .logging import log_config

logger = logging.getLogger(__name__)

_V = t.TypeVar("_V")


class Var(t.Generic[_V]):
    ...  # data bridge type between front and back


class Component:
    ...


class App:
    def __init__(self):
        self.server = AppServer()
        self.layout: list = []

    def on(self, signal: Signal) -> t.Awaitable:
        def wrapper(f: SignalHandler):
            @functools.wraps(f)
            async def handler_f(data: SignalData):
                return await f(data)

            add_handler(signal, handler_f)

            return handler_f

        return wrapper

    def attach_to_layout(self, component: Component) -> None:
        logger.info(f"attached to layout: {component.__class__.__name__}")

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        await self.server(scope, receive, send)


class AppServer:
    """Proxy entrypoint for all incoming requests from client side.

    Responsible for managing low-level backend operations like requests routing, handling and responding.
    In some cases, return control flow to the main app, calling interface methods: emitting signals, handling bus.
    """

    _EXIT_CODE = 1

    ALLOWED_STATIC_FILES = (".html", "css", ".js", ".map", ".ico")

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "lifespan":
            exit_code = await self.handle_lifespan(scope, receive, send)
            if exit_code:
                return

        elif scope["type"] == "http":
            await self.handle_http_request(scope, receive, send)

        elif scope["type"] == "websocket":
            await self.handle_websocket_request(scope, receive, send)

        else:
            response = HTMLResponse(content="<b>Not allowed</b>", status_code=405)
            await response(scope, receive, send)

    async def handle_lifespan(self, scope: Scope, receive: Receive, send: Send) -> _EXIT_CODE | None:
        message = await receive()
        if message["type"] == "lifespan.startup":
            await emit_signal(SERVER_STARTUP)

            await send({"type": "lifespan.startup.complete"})
            return None

        elif message["type"] == "lifespan.shutdown":
            await emit_signal(SERVER_SHUTDOWN)

            await send({"type": "lifespan.shutdown.complete"})
            return self._EXIT_CODE

        else:
            return None

    async def handle_http_request(self, scope: Scope, receive: Receive, send: Send) -> None:
        request = Request(scope, receive, send)
        path = request.url.components.path

        if any([path.endswith(ext) for ext in self.ALLOWED_STATIC_FILES]):
            static_files = StaticFiles(directory="static")
            await static_files(scope, receive, send)

        else:
            with open("static/index.html") as f:
                response = HTMLResponse(content=f.read(), status_code=200)
                await response(scope, receive, send)

    async def handle_websocket_request(self, scope: Scope, receive: Receive, send: Send) -> None:
        socket = WebSocket(scope=scope, receive=receive, send=send)
        await socket.accept()

        data = await socket.receive_text()
        if data != 'LOGIN':
            await socket.close(code=1008)
            return

        await socket.send_text('LOGIN OK')
        await emit_signal(CLIENT_CONNECTED)

        await self.client_lifetime_task(socket)

    async def client_lifetime_task(self, socket: WebSocket) -> None:
        logger.debug(f'startup lifetime task, host={socket.client.host}')
        try:
            while True:
                message = await socket.receive_text()  # noqa
                # TODO

        except asyncio.CancelledError:
            pass

        except WebSocketDisconnect as exc:
            await emit_signal(CLIENT_DISCONNECTED, {'code': exc.code, 'reason': exc.reason})
            # raise

        finally:
            logger.debug(f"shutdown lifetime task, host={socket.client.host}")


# TODO access event loop to run bus listener
# https://github.com/encode/uvicorn/issues/706
def run(app: App, *, host: str = "localhost", port: int = 5000) -> None:
    logger.info("Building web UI...")
    subprocess.run(["npm", "run", "build"])  # FIXME control outputa and redirect to logger

    logger.info(f"Starting server at http://{host}:{port}/")
    uvicorn.run(app, host=host, port=port, log_level="debug", log_config=log_config)
