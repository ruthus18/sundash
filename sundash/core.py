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

from . import bus
from .bus import C_APPEND_COMPONENT
from .bus import C_CLEAR_LAYOUT
from .bus import C_UPDATE_VAR
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
from .bus import call_command
from .bus import emit_signal
from .logging import log_config

logger = logging.getLogger(__name__)

_V = t.TypeVar("_V")


class Var(t.Generic[_V]):
    ...  # data bridge type between front and back


class Component:
    html: str = ''

    # FIXME: refactor mad tech
    async def set(self, name: str, value: t.Any) -> None:
        if type_annotation := self.__annotations__.get(name):
            if type_annotation.__origin__ is Var:
                await call_command(
                    C_UPDATE_VAR,
                    {'name': name, 'value': str(value)},
                )
        setattr(self, name, value)


# High-level interface
class App:
    def __init__(self):
        self.server = AppServer()
        self.layout: list = []
        self.layout_handlers = collections.defaultdict(set)

        self._init_default_handlers()

    def _init_default_handlers(self) -> None:
        add_handler(CLIENT_CONNECTED, self._on_client_connected)
        add_handler(LAYOUT_CLEAN, self._on_layout_clean)

    async def _on_client_connected(self, data: dict) -> None:
        await call_command(C_CLEAR_LAYOUT)

    # FIXME: refactor mad tech
    async def _on_layout_clean(self, data: dict) -> None:  # noqa: C901
        for component in self.layout:
            await call_command(C_APPEND_COMPONENT, {'html': component.html})

            for field, annotation in component.__annotations__.items():
                try:
                    annotation_origin = annotation.__origin__
                except AttributeError:
                    continue

                # set init value of var
                if annotation_origin is Var:
                    init_value = getattr(component, field)
                    if isinstance(init_value, t.Callable):
                        init_value = init_value.__func__()

                    await call_command(C_UPDATE_VAR, {'name': field, 'value': init_value})

            # connect component signal handlers
            component_name = component.__class__.__name__
            if component_name in self.layout_handlers:
                for signal, handler_name in self.layout_handlers[component_name]:
                    handler = getattr(component, handler_name)
                    add_handler(signal, handler)

    # FIXME: refactor mad tech
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

    def run(
        self,
        layout: list[Component],
        host: str = 'localhost',
        port: int = 5000,
    ) -> None:
        for comp in layout:
            self.attach_to_layout(comp)
        self.server.run(host, port)


class AppServer:
    """ASGI backend entrypoint

    * listen port and handle HTTP, WS and staticfiles requests
    * submit bus handler to control frontend (`.on_call_command`)
    * emit system signals
    * redirect signal requests to bus
    """

    _EXIT_CODE = 1

    ALLOWED_STATIC_FILES = (".html", "css", ".js", ".map", ".ico")

    class _Server(uvicorn.Server):
        def install_signal_handlers(self) -> None:
            # replace default signal catch
            # because I want `Ctrl + C` to work correct
            pass

    def __init__(self):
        add_handler(CMD_CALL, self.on_call_command)

    async def on_call_command(self, data: dict) -> None:
        command, params = data['command'], data.get('params', {})
        await self._s.send_text(f'{command} {json.dumps(params)}')

    def run(self, host: str, port: int) -> None:
        build_ui()

        logger.info(f"Starting server at http://{host}:{port}/")
        server_task = self.server_task(
            host=host,
            port=port,
            log_level="debug",
            log_config=log_config,
        )
        bus_listener_task = bus.listener_task()

        try:
            asyncio.run(_run_tasks(server_task, bus_listener_task))
        except KeyboardInterrupt:
            pass

        finally:
            logger.info('Shutting down server')

    async def server_task(self, **config_params: dict) -> None:
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
        self._s = socket  # FIXME client sessions
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
            # raise  # FIXME client sessions


# TODO  maybe separate system part?
#       (~ bash & `manage.py` replacement)
def build_ui():
    logger.info("Building web UI...")
    # FIXME control output and redirect to logger
    subprocess.run(["npm", "run", "build"])


async def _run_tasks(*tasks: t.Iterable[t.Awaitable]) -> None:
    await asyncio.wait(
        [asyncio.create_task(t) for t in tasks],
        return_when=asyncio.FIRST_COMPLETED,
    )
