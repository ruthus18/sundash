from __future__ import annotations
import logging

import asyncio
import subprocess
import typing as t

# import simplejson as json
import uvicorn
from starlette import routing
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.staticfiles import StaticFiles
from starlette.websockets import WebSocket

from .bus import BusManager

logger = logging.getLogger(__name__)

_V = t.TypeVar("_V")


class Var(t.Generic[_V]):
    ...  # data bridge type between front and back


_bus = ...


def init_bus(cls: type[BusManager] = BusManager) -> None:
    global _bus
    _bus = cls()


async def _html_endpoint(request: Request) -> HTMLResponse:
    with open("static/index.html") as f:
        return HTMLResponse(content=f.read(), status_code=200)


# async def _pusher(socket: WebSocket, push_text: str) -> None:
#     for i in range(1, 6):
#         await asyncio.sleep(1)

#         text = ' '.join([push_text, str(i)])
#         await socket.send_text(text)
#         logger.info(f'message sent: {text}')


async def _listener(socket: WebSocket) -> None:
    logger.info("listener connected")
    try:
        while True:
            request_raw = await socket.receive_text()
            logger.info(f"request received: {request_raw}")

            request = _bus.handle_request(request_raw)  # TODO

    except asyncio.CancelledError:
        pass
    finally:
        logger.info("shutdown listener")


async def _ws_endpoint(socket: WebSocket) -> None:
    await socket.accept()
    logger.info(f"connection opened: {socket.client.host}")

    await socket.send_text("shh it's ok")

    listener_task = asyncio.create_task(_listener(socket))

    await asyncio.sleep(10)

    # await _pusher(socket, 'PING')

    listener_task.cancel()
    await listener_task

    await socket.close(reason="thats all folks...")
    logger.info(f"connection closed: {socket.client.host}")


class Sundash:
    routes = [
        routing.Route("/", _html_endpoint),
        routing.WebSocketRoute("/", _ws_endpoint, name="ws"),
        routing.Mount("/", app=StaticFiles(directory="static"), name="static"),
    ]

    def __init__(self, *, starlette_params: dict = None):
        self.asgi_app = Starlette(
            routes=self.routes,
            **starlette_params or {},
        )
        self.layout: list = []

        # FIXME Не придумал способа лучше, чтобы из endpoint-ов достучаться до инстанса шины
        if _bus is not Ellipsis:
            raise RuntimeError("Only one instance of Sundash is allowed")
        init_bus()

    @property
    @staticmethod
    def bus() -> BusManager:
        return _bus

    def on(self, f) -> t.Awaitable:
        async def wrapper(*args, **kwargs):
            return await f(*args, **kwargs)

        return wrapper

    def attach_to_page(self, component: Component) -> None:
        ...

    def run(self):
        logger.info("Building web UI...")
        subprocess.run(["npm", "run", "build"])

        logger.info("Starting server...")
        uvicorn.run(self.asgi_app, port=5000, log_level="warning")


class Component:
    ...
