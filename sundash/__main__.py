import subprocess
import argparse

import uvicorn

from .logger import logger


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['runserver'])
    args = parser.parse_args()

    if args.command == 'runserver':
        logger.info('Building web UI...')
        subprocess.run(['npm', 'run', 'build'])

        logger.info('Starting server...')
        uvicorn.run('sundash.server:app', port=5000, log_level='info')
