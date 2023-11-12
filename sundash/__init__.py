import os

from .logging import setup as __setup_logging

if int(os.getenv('SUNDASH_SETUP_LOGGING', 1)):
    __setup_logging()


from .core import App
from .core import Component
from .core import Var

__all__ = [
    'App',
    'Component',
    'Var',
]
