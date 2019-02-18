# main.py

import os
import sys
import signal
import logging

import jinja2
import aiohttp_jinja2

from aiohttp import web
from multiprocessing import Process

from pakreq.db import init_db, close_db
from pakreq.pakreq import start_daemon
from pakreq.routes import setup_routes
from pakreq.settings import get_config
from pakreq.telegram import start_bot
from pakreq.middlewares import setup_middlewares
from pakreq.ldap import PakreqLDAP


def init_app(argv=None):
    """Initialize aiohttp"""
    app = web.Application()

    app['config'] = get_config(argv)
    app['ldap'] = PakreqLDAP(app['config']['ldap_url'])

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
    """Main!"""
    # Setup logger
    logging.basicConfig(level=logging.INFO)

    config = get_config(argv)

    # Start web process
    app = init_app(argv)
    web_process = Process(
        target=web.run_app, args=(app,),
        kwargs=dict(host=config['host'], port=config['port'])
    )
    web_process.start()

    # Start telegram process
    telegram_process = Process(
        target=start_bot, args=(config,)
    )
    telegram_process.start()

    # Maintenance daemon
    daemon_process = Process(
        target=start_daemon, args=(config,)
    )
    daemon_process.start()

    try:
        web_process.join()
        telegram_process.join()
        daemon_process.join()
    finally:
        print('\rBye-Bye!')
        os.kill(web_process.pid, signal.SIGINT)
        os.kill(telegram_process.pid, signal.SIGINT)
        os.kill(daemon_process.pid, signal.SIGINT)
        exit(0)


if __name__ == '__main__':
    main(sys.argv[1:])
