# routes.py

import pathlib

from pakreq.views import index

PROJECT_ROOT = pathlib.Path(__file__).parent

def setup_routes(app):
    app.router.add_get('/', index)
    setup_static_routes(app)


def setup_static_routes(app):
    app.router.add_static('/static/',
                          path=PROJECT_ROOT / 'static',
                          name='static')