import logging
import logging.config

log_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "class": "colorlog.ColoredFormatter",
            "format": ("{green}[{asctime}]{reset} {bg_green}{levelname}{reset} {blue}{name}:{reset} {message}"),
            "style": "{",
        },
    },
    "filters": {},
    "handlers": {
        "stdout": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "default",
        },
        "null": {
            "level": "DEBUG",
            "class": "logging.NullHandler",
        },
    },
    "loggers": {
        "": {
            "handlers": ["stdout"],
            "level": logging.DEBUG,
        },
        "uvicorn": {
            "handlers": ["null"],
            "propagate": False,
        },
        "asyncio": {
            "handlers": ["null"],
            "propagate": False,
        },
    },
}


def setup():
    logging.config.dictConfig(log_config)
