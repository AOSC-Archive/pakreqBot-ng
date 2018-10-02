# routes.py

"""
Routes
"""

import pathlib
from cryptography.fernet import Fernet
import base64
from aiohttp_session import setup as setup_session
from aiohttp_security import setup as setup_security
from aiohttp_security import SessionIdentityPolicy
from aiohttp_session.cookie_storage import EncryptedCookieStorage

from pakreq.views import (
    index, requests_all, request_detail, detail, login, auth, account, logout)
from pakreq.webauth import PakreqAuth

PROJECT_ROOT = pathlib.Path(__file__).parent


def setup_routes(app):
    """Setup routes and session handlers"""
    # we could use `secret` module here but that requires Python 3.6+
    key = base64.urlsafe_b64decode(Fernet.generate_key())
    setup_session(app, EncryptedCookieStorage(key))
    setup_security(app, SessionIdentityPolicy(), PakreqAuth(app))
    app.router.add_get('/', index)
    app.router.add_get('/detail/{ids:([0-9]*)}', detail)
    app.router.add_get('/requests', requests_all)
    app.router.add_get('/request/{ids:([0-9]*)}', request_detail)
    app.router.add_get('/login', login)
    app.router.add_post('/login', auth)
    app.router.add_get('/account', account)
    app.router.add_get('/logout', logout)
    setup_static_routes(app)


def setup_static_routes(app):
    """Setup static routes"""
    app.router.add_static(
        '/static/',
        path=PROJECT_ROOT / 'static',
        name='static'
    )
