# web.py

import jinja2
import uvloop
import asyncio
import aiohttp_jinja2

from aiohttp import web

from pakreq.db import init_db, close_db
from pakreq.ldap import PakreqLDAP
from pakreq.middlewares import setup_middlewares
from pakreq.routes import setup_routes


def init_app(config):
    """Initialize aiohttp"""
    app = web.Application()

    app['config'] = config
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


def start_web(config):
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    app = init_app(config)
    web.run_app(app, host=app['config']['host'], port=app['config']['port'])
