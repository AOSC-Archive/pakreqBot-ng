# views.py

import aiohttp_jinja2

from aiohttp import web

import pakreq.db

@aiohttp_jinja2.template('index.html')
async def index(request):
    async with request.app['db'].acquire() as conn:
        await pakreq.db.new_request(conn) # For testing purpose
        requests = await pakreq.db.get_requests(conn)
    return {'requests': requests}
