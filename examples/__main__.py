import sys

from sundash.logging import setup as setup_logging


def run_example():
    setup_logging()
    if len(sys.argv) == 1:
        from . import _00_start  # noqa
        return

    match sys.argv[1]:
        case 'counter':
            from ._01_counter import run
            run()

        case 'clock':
            from ._02_clock import run
            run()

        case 'coiny':
            from ._03_coiny import run
            run()

        case 'search':
            from ._04_search import run
            run()

        case 'tables':
            from ._05_tables import run
            run()


if __name__ == '__main__':
    run_example()
