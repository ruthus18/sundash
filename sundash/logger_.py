import sys

from loguru import logger

logger.remove()
logger.add(
    sys.stdout,
    format="[{time:HH:mm:ss.SSS}] <lvl>{message}</lvl>",
    colorize=True,
)

logger = logger.opt(colors=True)
