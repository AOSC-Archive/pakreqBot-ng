# views.py

"""
Views
"""

import aiohttp_jinja2
import logging

from aiohttp import web
from aiohttp_security import (
    is_anonymous, forget, remember, check_authorized, check_permission,
    authorized_userid)

import pakreq.db

from pakreq.utils import dump_json


# HTML
@aiohttp_jinja2.template('index.html')
async def index(request):
    """Index"""
    async with request.app['db'].acquire() as conn:
        reqs = await pakreq.db.get_requests(conn)
    reqs = [req for req in reqs if req["status"] == pakreq.db.RequestStatus.OPEN]
    return {
        'requests': reqs,
        'base_url': request.app['config']['base_url']
    }


@aiohttp_jinja2.template('login.html')
async def login(request):
    return {'base_url': request.app['config']['base_url']}


async def account(request):
    if await is_anonymous(request):
        return web.HTTPFound('%s/login' % request.app['config']['base_url'])
    return aiohttp_jinja2.render_template(
        'account.html', request,
        {'base_url': request.app['config']['base_url'],
         'username': await authorized_userid(request)}
    )


async def logout(request):
    await check_authorized(request)
    resp = web.HTTPFound('/')
    await forget(request, resp)
    return resp


async def auth(request):
    cred = await request.post()
    user = cred.get('user')
    resp = web.HTTPFound('/account')
    async with request.app['db'].acquire() as conn:
        if await pakreq.db.check_password(conn, user, cred.get('pwd')):
            # TODO: remember session based on user ID instead of username
            await remember(request, resp, user)
            logging.info('%s logged in' % user)
            return resp
    return aiohttp_jinja2.render_template('login.html', request,
                                          {'msg': 'Invalid credentials'})


@aiohttp_jinja2.template('detail.html')
async def detail(request):
    """Detail"""
    ids = request.match_info['ids']
    async with request.app['db'].acquire() as conn:
        reqs = await pakreq.db.get_request_detail(conn, ids)
    return {
        'request': reqs,
        'base_url': request.app['config']['base_url']
    }


# JSON
async def requests_all(request):
    """List requests"""
    async with request.app['db'].acquire() as conn:
        result = await pakreq.db.get_requests(conn)
    return web.json_response(result, dumps=dump_json)


async def request_detail(request):
    ids = request.match_info['ids']
    async with request.app['db'].acquire() as conn:
        result = await pakreq.db.get_request_detail(conn, ids)
    return web.json_response(result, dumps=dump_json)
