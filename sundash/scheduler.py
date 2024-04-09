import asyncio
import logging
from contextvars import ContextVar

from .app import App
from .app import AppInterface
from .messages import Event
from .sessions import Session

logger = logging.getLogger(__name__)


class EverySecond(Event): ...


_scheduler_task: ContextVar[asyncio.Task] = ContextVar('_scheduler_task')


class SchedulerMixin(AppInterface):

    async def on_session_open(self) -> None:
        await super().on_session_open()
        task = asyncio.create_task(self.scheduler())
        _scheduler_task.set(task)

    async def on_session_close(self) -> None:
        await super().on_session_close()
        _scheduler_task.get().cancel()
        _scheduler_task.set(None)

    async def scheduler(self):
        event = EverySecond()
        session = Session.get()
        try:
            with session:
                while True:
                    await self.on_event(event)
                    await asyncio.sleep(1)

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.exception(e)


class SchedulerApp(SchedulerMixin, App): ...
