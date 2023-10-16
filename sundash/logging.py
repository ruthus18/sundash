import logging
import logging.config


log_config = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'class': 'colorlog.ColoredFormatter',
            'format': (
                '%(log_color)s%(levelname)-8s%(asctime)s%(yellow)s %(name)s: '
                '%(blue)s%(message)s %(reset)s'
            ),
        }
    },
    'filters': {},
    'handlers': {
        'stdout': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'default',
        },
    },
    'loggers': {
        '': {
            'handlers': ['stdout'],
            'level': logging.DEBUG,
        },
    },
}

logging.config.dictConfig(log_config)
