# main.py

import os
import sys
import signal
import asyncio
import logging

import jinja2
import aiohttp_jinja2

from aiohttp import web
from multiprocessing import Process

from pakreq.db import init_db, close_db
from pakreq.routes import setup_routes
from pakreq.settings import get_config
from pakreq.telegram import start_bot
from pakreq.middlewares import setup_middlewares

async def init_app(argv=None):
    app = web.Application()

    app['config'] = get_config(argv)

    # Setup jinja2
    aiohttp_jinja2.setup(
        app, loader=jinja2.PackageLoader('pakreq', 'templates')
    )

    # Create DB connection on startup, shutdown on exit
    app.on_startup.append(init_db)
    app.on_cleanup.append(close_db)

    # Setup views and routes
    setup_routes(app)
    setup_middlewares(app)

    return app

def main(argv):
    # Setup logger
    logging.basicConfig(level=logging.INFO)

    config = get_config(argv)

    # Start web process
    loop = asyncio.get_event_loop()
    app = loop.run_until_complete(init_app(argv))
    web_process = Process(target=web.run_app, args=(app,), kwargs=dict(host=config['host'], port=config['port']))
    web_process.start()

    # Start telegram process
    telegram_process = Process(target=start_bot, args=(config,))
    telegram_process.start()

    try:
        web_process.join()
        telegram_process.join()
    finally:
        print("Bye-Bye!")
        os.kill(web_process.pid, signal.SIGKILL)
        os.kill(telegram_process.pid, signal.SIGKILL)
        exit(0)

if __name__ == '__main__':
    main(sys.argv[1:])