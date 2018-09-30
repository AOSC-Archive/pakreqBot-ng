# views.py

"""
Views
"""

import aiohttp_jinja2

from aiohttp import web

import pakreq.db

from pakreq.utils import dump_json


# HTML
@aiohttp_jinja2.template('index.html')
async def index(request):
    """Index"""
    async with request.app['db'].acquire() as conn:
        requests = await pakreq.db.get_requests(conn)
    return {'requests': requests}


@aiohttp_jinja2.template('detail.html')
async def detail(request):
    """Detail"""
    ids = request.match_info['ids']
    async with request.app['db'].acquire() as conn:
        requests = await pakreq.db.get_request_detail(conn, ids)
    return {'request': requests}


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
