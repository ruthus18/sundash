import os

from .logging import setup as __setup_logging

if int(os.getenv('SUNDASH_SETUP_LOGGING', 1)):
    __setup_logging()


from .core import App
from .core import on
from .layout import Component
from .layout import Var

__all__ = [
    'App',
    'on',
    'Component',
    'Var',
]
