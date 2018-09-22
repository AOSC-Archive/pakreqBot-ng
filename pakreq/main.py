# main.py

import sys
import logging

import jinja2
import aiohttp_jinja2

from aiohttp import web

from pakreq.db import init_db, close_db
from pakreq.routes import setup_routes
from pakreq.settings import get_config
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

    app = init_app(argv)

    config = get_config(argv)

    web.run_app(app,
        host=config['host'],
        port=config['port']
    )

if __name__ == '__main__':
    main(sys.argv[1:])