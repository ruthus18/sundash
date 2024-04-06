import sys

from sundash.logging import setup as setup_logging


def run_example():
    setup_logging()
    match sys.argv[1]:
        case '01' | 'hello':
            from . import _01_hello

        case '02' | 'counter':
            from . import _02_counter

        case '03' | 'clock':
            from . import _03_clock

        case '04' | 'menu':
            from . import _04_menu

        case '05' | 'search':
            from . import _05_search

        case '06' | 'tables':
            from . import _06_tables

        case other:
            raise ValueError(f'unknown example: {other}')


if __name__ == '__main__':
    run_example()
