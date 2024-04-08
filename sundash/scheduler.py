import asyncio
import logging

from . import App
from .messages import Event
from .sessions import Session

logger = logging.getLogger(__name__)


class EverySecond(Event): ...


_scheduled_sessions: dict[Session.ID, Session] = {}


class SchedulerMixin:

    async def on_session_open(self) -> None:
        await super().on_session_open()
        _scheduled_sessions[self.session.id] = self.session

    async def on_session_close(self) -> None:
        await super().on_session_close()
        _scheduled_sessions.pop(self.session.id)

    async def scheduler(self):
        event = EverySecond()
        try:
            while True:
                for session in _scheduled_sessions.values():
                    with session:
                        await self.on_event(event)

                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.exception(e)

    async def run(self, *args, **kwargs) -> None:
        scheduler_task = asyncio.create_task(self.scheduler())
        try:
            await super().run(*args, **kwargs)
        finally:
            scheduler_task.cancel()


class SchedulerApp(SchedulerMixin, App): ...
