import asyncio
import enum
import subprocess
import typing as t

import uvicorn
from starlette import routing
from starlette.applications import Starlette
from starlette.endpoints import WebSocketEndpoint as _BaseWebSocketEndpoint
from starlette.responses import HTMLResponse
from starlette.staticfiles import StaticFiles
from starlette.websockets import WebSocket

from .logger_ import logger


async def _load_app(_) -> HTMLResponse:
    with open("static/index.html") as f:
        return HTMLResponse(content=f.read(), status_code=200)


class Signal(enum.StrEnum):
    CONNECTED = enum.auto()
    DISCONNECT = enum.auto()
    CLEAR_SCREEN = enum.auto()


class _BusServer:
    def __init__(self):
        self.queue = asyncio.Queue()

    # def emit_signal(self, signal: Signal):

    # async def connect(self, socket: WebSocket):

    #     ...

    async def handle_message(self, socket: WebSocket, req_data: t.Any) -> None:
        logger.info(f"{self.LOG_DATA_RECV} {req_data}")

        resp_data = {"msg": "ok"}
        await socket.send_json(resp_data)
        logger.info(f"{self.LOG_DATA_SENT} {resp_data}")

    async def disconnect(self, socket: WebSocket, close_code: int) -> None:
        logger.info(f"{self.LOG_CONN_CLOSE} {socket.client.host}")
        ...


bus = _BusServer()


class _WebSocketEndpoint(_BaseWebSocketEndpoint):
    encoding = "json"

    LOG_CONN_OPEN = "[WS] CONN_OPEN:"
    LOG_CONN_CLOSE = "[WS] CONN_CLOSE:"
    LOG_DATA_RECV = "[WS] DATA_RECV:"
    LOG_DATA_SENT = "[WS] DATA_SENT:"

    async def on_connect(self, socket: WebSocket) -> None:
        await socket.accept()
        await bus.emit_signal(Signal.CONNECTED)
        logger.info(f"{self.LOG_CONN_OPEN} {socket.client.host}")

    async def on_receive(self, socket: WebSocket, data: t.Any) -> None:
        await bus.handle_message(socket, data)

    async def on_disconnect(self, socket: WebSocket, close_code: int) -> None:
        await bus.disconnect(socket, close_code)


class SundashServer:
    routes = [
        routing.Route("/", _load_app),
        routing.WebSocketRoute("/", _WebSocketEndpoint, name="ws"),
        routing.Mount("/", app=StaticFiles(directory="static"), name="static"),
    ]

    def __init__(self, **starlette_params):
        self.asgi_app = Starlette(routes=self.routes, **starlette_params)
        self.layout: list = []
        self.event_handlers = []

    # def on(self, coro: t.Awaitable, signal: Signal) -> :

    def run(self):
        logger.info("Building web UI...")
        subprocess.run(["npm", "run", "build"])

        logger.info("Starting server...")
        uvicorn.run(self.asgi_app, port=5000, log_level="info")
