from __future__ import annotations

import asyncio
import collections
import functools
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

from .bus import CLIENT_CONNECTED
from .bus import CLIENT_DISCONNECTED
from .bus import CMD_CALL
from .bus import LAYOUT_CLEAN
from .bus import SERVER_SHUTDOWN
from .bus import SERVER_STARTUP
from .bus import Signal
from .bus import SignalData
from .bus import SignalHandler
from .bus import add_handler
from .bus import emit_signal
from .bus import listener_task
from .logging import log_config

logger = logging.getLogger(__name__)

_V = t.TypeVar("_V")


class Var(t.Generic[_V]):
    ...  # data bridge type between front and back


class Component:
    html: str = ''

    async def set(self, name, value):
        if type_annotation := self.__annotations__.get(name):
            if type_annotation.__origin__ is Var:
                await emit_signal(CMD_CALL, {'command': 'update_var', 'params': {'name': name, 'value': str(value)}})

        setattr(self, name, value)


class App:
    def __init__(self):
        self.server = AppServer()
        self.layout: list = []
        self.layout_handlers = collections.defaultdict(set)

        self._init_default_handlers()

    def _init_default_handlers(self) -> None:
        add_handler(CLIENT_CONNECTED, self._on_client_connected)
        add_handler(LAYOUT_CLEAN, self._on_layout_clean)

    def on(self, signal: Signal) -> t.Awaitable:
        def wrapper(f: SignalHandler):
            @functools.wraps(f)
            async def handler_f(data: SignalData):
                return await f(data)

            @functools.wraps(f)
            async def component_handler_f(self: Component, data: SignalData):
                return await f(self, data)

            is_component_handler = False
            path = f.__qualname__.split('.')
            if len(path) > 1:
                is_component_handler = True

            if is_component_handler:
                component_name, handler_name = path[-2:]
                self.layout_handlers[component_name].add((signal, handler_name))
                return component_handler_f
            else:
                add_handler(signal, handler_f)
                return handler_f

        return wrapper

    def attach_to_layout(self, component: Component | str) -> None:
        if type(component) is str:
            component_obj = Component()
            component_obj.html = component
            component = component_obj

        self.layout.append(component)

    async def _on_client_connected(self, data: dict) -> None:
        await emit_signal(CMD_CALL, {'command': 'clear_layout'})

    async def _on_layout_clean(self, data: dict) -> None:
        for component in self.layout:
            await emit_signal(CMD_CALL, {'command': 'append_component', 'params': {'html': component.html}})

            component_name = component.__class__.__name__
            if component_name in self.layout_handlers:
                for signal, handler_name in self.layout_handlers[component_name]:
                    handler = getattr(component, handler_name)
                    add_handler(signal, handler)


class AppServer:
    """Proxy entrypoint for all incoming requests from client side.

    Responsible for managing low-level backend operations like requests routing, handling and responding.
    In some cases, return control flow to the main app, calling interface methods: emitting signals, handling bus.
    """

    _EXIT_CODE = 1

    ALLOWED_STATIC_FILES = (".html", "css", ".js", ".map", ".ico")

    class _Server(uvicorn.Server):
        def install_signal_handlers(self) -> None:
            pass  # catch server interrupt

    def __init__(self):
        add_handler(CMD_CALL, self.call_command)

    async def run(self, **config_params: dict) -> None:
        config = uvicorn.Config(app=self, **config_params)
        server = self._Server(config=config)
        await server.serve()

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
        self._s = socket  # FIXME: client sessions
        await socket.accept()

        data = await socket.receive_text()
        if data != 'LOGIN':
            await socket.close(code=1008)
            return

        await socket.send_text('LOGIN OK')
        await emit_signal(CLIENT_CONNECTED)

        try:
            while True:
                message = await socket.receive_text()  # noqa
                signal, data = message.split(" ", 1)

                await emit_signal(signal=signal, data=json.loads(data))

        except WebSocketDisconnect as exc:
            await emit_signal(CLIENT_DISCONNECTED, {'code': exc.code, 'reason': exc.reason})
            # raise

    async def call_command(self, data):
        command, params = data['command'], data.get('params', {})
        await self._s.send_text(f'{command} {json.dumps(params)}')


def run(app: App, *, host: str = "localhost", port: int = 5000) -> None:
    logger.info("Building web UI...")
    subprocess.run(["npm", "run", "build"])  # FIXME control output and redirect to logger

    logger.info(f"Starting server at http://{host}:{port}/")
    server_task = app.server.run(host=host, port=port, log_level="debug", log_config=log_config)
    bus_listener_task = listener_task()

    try:
        asyncio.run(_run(server_task, bus_listener_task))
    except KeyboardInterrupt:
        pass

    finally:
        logger.info('Shutting down server')


async def _run(*tasks: t.Iterable[t.Awaitable]) -> None:
    await asyncio.wait(
        [asyncio.create_task(t) for t in tasks],
        return_when=asyncio.FIRST_COMPLETED,
    )
