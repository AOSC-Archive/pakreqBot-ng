# views.py

import aiohttp_jinja2

from aiohttp import web
from datetime import datetime

import pakreq.db

from pakreq.utils import dump_json


@aiohttp_jinja2.template('index.html')
async def index(request):
    async with request.app['db'].acquire() as conn:
        requests = await pakreq.db.get_requests(conn)
    return {'requests': requests}


async def requests_all(request):
    async with request.app['db'].acquire() as conn:
        result = await pakreq.db.get_requests(conn)
    return web.json_response(result, dumps=dump_json)


async def request_detail(request):
    ids = request.match_info['ids']
    async with request.app['db'].acquire() as conn:
        result = await pakreq.db.get_request_detail(conn, ids)
    return web.json_response(result, dumps=dump_json)
