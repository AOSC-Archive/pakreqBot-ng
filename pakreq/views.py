# views.py

import aiohttp_jinja2

from aiohttp import web

from pakreq.db import get_requests, new_user, new_request

@aiohttp_jinja2.template('index.html')
async def index(request):
    async with request.app['db'].acquire() as conn:
        await new_request(conn) # For testing purpose
        requests = [dict(q) for q in await get_requests(conn)]
    return {'requests': requests}
