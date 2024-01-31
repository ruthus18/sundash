import asyncio
import typing as t

from .core import HTML
from .layout import Component
from .layout import Layout
from .server import Server


class App:
    Layout = Layout
    Server = Server

    def run(self, **params: dict) -> None:
        try:
            asyncio.run(self._run(**params))
        except KeyboardInterrupt:
            pass

    async def _run(self, layout: t.Iterable[Component | HTML] = []) -> None:
        self.layout = self.Layout()
        for comp in layout: self.layout.append(comp)

        self.server = self.Server()
        await self.server.run()
