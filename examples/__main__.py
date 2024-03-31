import sys

from sundash.logging import setup as setup_logging


def run_example():
    setup_logging()
    if len(sys.argv) == 1:
        from ._00_hello import run
        run()
        return

    match sys.argv[1]:
        case 'hello':
            from ._00_hello import run
            run()

        case 'buttons':
            from ._01_buttons import run
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

        case other:
            raise ValueError(f'unknown example: {other}')


if __name__ == '__main__':
    run_example()
