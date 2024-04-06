import asyncio
import logging

from . import App
from .core import EVENT
from .core import MessageContext
from .server import Session

logger = logging.getLogger(__name__)


class EVERY_SECOND(EVENT): ...


_scheduled_sessions: dict[Session.ID, Session] = {}


class SchedulerMixin:

    async def _on_session_open(self, session: Session) -> None:
        await super()._on_session_open(session)
        _scheduled_sessions[session.id] = session

    async def _on_session_close(self, session: Session) -> None:
        await super()._on_session_close(session)
        _scheduled_sessions.pop(session.id)

    async def scheduler(self):
        try:
            while True:
                for session in _scheduled_sessions.values():
                    event = EVERY_SECOND()
                    event._ctx = MessageContext(session=session)
                    await self._on_event(event)

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
