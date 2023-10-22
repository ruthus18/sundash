from __future__ import annotations

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

from .bus import BusManager
from .bus import Command
from .bus import Signal
from .bus import SignalData
from .logging import log_config

logger = logging.getLogger(__name__)

_V = t.TypeVar("_V")


# class Var(t.Generic[_V]):
#     ...  # data bridge type between front and back


class Component:
    ...


class App:
    def __init__(self):
        self.layout: list = []

        self.server = AppServer(self)
        self.bus = BusManager()

        self._init_default_signal_handlers()

    async def on_startup(self):
        pass  # Add your startup logic

    async def on_shutdown(self):
        pass  # Add your shutdown logic

    async def _on_client_connected(self, data: SignalData) -> None:
        self.emit_signal()

    async def _on_client_disconnected(self, data: SignalData) -> None:
        ...

    async def _on_layout_clean(self, data: SignalData) -> None:
        ...

    async def _on_layout_updated(self, data: SignalData) -> None:
        ...

    async def _on_every_second(self, data: SignalData) -> None:
        ...

    async def _on_var_updated(self, data: SignalData) -> None:
        ...

    def _init_default_signal_handlers(self) -> None:
        self.on(Signal.CLIENT_CONNECTED)(self._on_client_connected)
        self.on(Signal.CLIENT_DISCONNECTED)(self._on_client_disconnected)
        self.on(Signal.LAYOUT_CLEAN)(self._on_layout_clean)
        self.on(Signal.LAYOUT_UPDATED)(self._on_layout_updated)
        self.on(Signal.EVERY_SECOND)(self._on_every_second)
        self.on(Signal.VAR_UPDATED)(self._on_var_updated)

    def on(self, signal: Signal) -> t.Awaitable:
        def wrapper(f: t.Awaitable):
            @functools.wraps(f)
            async def handler_f(signal_data: SignalData):
                logger.info(f"signal emitted: {signal}, data={signal_data}")
                return await f(signal_data)

            self.bus.add_handler(signal, handler_f)

            return handler_f

        return wrapper

    def emit_signal(self, signal: Signal) -> None:
        ...

    def call_command(self, command: Command) -> None:
        ...

    def attach_to_page(self, component: Component) -> None:
        ...

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        await self.server(scope, receive, send)


class AppServer:
    """Proxy entrypoint for all incoming requests from client side.

    Responsible for managing low-level backend operations like requests routing, handling and responding.
    In some cases, return control flow to the main app, calling interface methods: emitting signals, handling bus.
    """

    _EXIT_CODE = 1

    ALLOWED_STATIC_FILES = (".html", "css", ".js", ".map", ".ico")

    def __init__(self, app: App):
        self.app = app  # FIXME: Should be connected to bus and emit events to app

    async def handle_lifespan(self, scope: Scope, receive: Receive, send: Send) -> _EXIT_CODE | None:
        message = await receive()
        if message["type"] == "lifespan.startup":
            await self.app.on_startup()

            await send({"type": "lifespan.startup.complete"})
            return None

        elif message["type"] == "lifespan.shutdown":
            await self.app.on_shutdown()

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
        ...  # TODO

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


# [UNDER CONSTRUCTION]
# websockets draft logic -> upgrade and embed to `AppServer`
# //-----//-----//-----//-----//-----//-----//-----//-----//-----


# TODO: Update ws endpoint code
# async def _ws_endpoint(socket: WebSocket) -> None:
#     await socket.accept()
#     logger.info(f"connection opened: {socket.client.host}")

#     await socket.send_text("OK")

#     # FIXME: KeyboardInterrput
#     listener_task = asyncio.create_task(_listener(socket))

#     await asyncio.sleep(3)

#     # Пример, когда мы не просто засыпаем, а отсылаем что-то клиенту
#     # await _pusher(socket, 'PING')

#     listener_task.cancel()
#     try:
#         await listener_task
#     except WebSocketDisconnect:
#         pass
#     else:
#         await socket.close(reason="thats all folks...")

#     logger.info(f"connection closed: {socket.client.host}")


# async def _pusher(socket: WebSocket, push_text: str) -> None:
#     for i in range(1, 6):
#         await asyncio.sleep(1)

#         text = ' '.join([push_text, str(i)])
#         await socket.send_text(text)
#         logger.info(f'message sent: {text}')


# async def _listener(socket: WebSocket) -> None:
#     logger.info("listener connected")
#     try:
#         while True:
#             request_raw = await socket.receive_text()
#             # await _bus.handle_request(request_raw)

#     except asyncio.CancelledError:
#         pass

#     except WebSocketDisconnect as exc:
#         logger.info(f"client disconnected: [{exc.code}] {exc.reason}")
#         raise

#     finally:
#         logger.info("shutdown listener")


# //-----//-----//-----//-----//-----//-----//-----//-----//-----


def run(app: App, *, host: str = "localhost", port: int = 5000) -> None:
    logger.info("Building web UI...")
    subprocess.run(["npm", "run", "build"])  # FIXME control outputa and redirect to logger

    logger.info(f"Starting server at http://{host}:{port}/")
    uvicorn.run(app, host=host, port=port, log_level="debug", log_config=log_config)
