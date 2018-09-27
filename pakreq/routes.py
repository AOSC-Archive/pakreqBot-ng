# routes.py

"""
Routes
"""

import pathlib

from pakreq.views import index, requests_all, request_detail

PROJECT_ROOT = pathlib.Path(__file__).parent


def setup_routes(app):
    """Setup routes"""
    app.router.add_get('/', index)
    app.router.add_get('/requests', requests_all)
    app.router.add_get('/request/{ids:([0-9]*)}', request_detail)
    setup_static_routes(app)


def setup_static_routes(app):
    """Setup static routes"""
    app.router.add_static(
        '/static/',
        path=PROJECT_ROOT / 'static',
        name='static'
    )
