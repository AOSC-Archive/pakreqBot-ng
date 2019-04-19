# main.py

import os
import sys
import signal
import logging

from multiprocessing import Process

from pakreq.pakreq import start_daemon
from pakreq.settings import get_config
from pakreq.telegram import start_bot
from pakreq.web import start_web


def main(argv):
    """Main!"""
    # Setup logger
    logging.basicConfig(level=logging.INFO)

    config = get_config(argv)

    # Start web process
    web_process = Process(
        target=start_web, args=(config,)
    )
    web_process.start()

    # Start telegram process
    telegram_process = Process(
        target=start_bot, args=(config,)
    )
    telegram_process.start()

    # Maintenance daemon
    # daemon_process = Process(
    #     target=start_daemon, args=(config,)
    # )
    # daemon_process.start()

    try:
        web_process.join()
        telegram_process.join()
        # daemon_process.join()
    finally:
        print('\rBye-Bye!')
        os.kill(web_process.pid, signal.SIGINT)
        os.kill(telegram_process.pid, signal.SIGINT)
        # os.kill(daemon_process.pid, signal.SIGINT)
        exit(0)


if __name__ == '__main__':
    main(sys.argv[1:])
