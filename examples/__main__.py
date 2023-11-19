import sys

from sundash.logging import setup as setup_logging

if __name__ == '__main__':
    setup_logging()
    match sys.argv[1]:
        case 'counter':
            from ._01_counter import run
            run()

        case 'clock':
            from ._02_clock import run
            run()

        case _:
            raise RuntimeError('unknown example')
