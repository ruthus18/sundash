import sys

from .logging import setup as __setup_logging

if 'test.py' in sys.argv[0]:
    __setup_logging()
