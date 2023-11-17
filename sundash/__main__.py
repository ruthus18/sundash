import asyncio

from .server import Server
from .server import build_ui

if __name__ == '__main__':
    server = Server()

    build_ui()
    asyncio.run(server.task())
