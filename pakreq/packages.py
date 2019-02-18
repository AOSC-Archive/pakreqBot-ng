# packages.py

"""
Simple packages site API library
"""

from aiohttp import ClientSession


BASE_URL = 'https://packages.aosc.io'


async def make_request(url, params={}):
    session = ClientSession()
    if not params['type']:
        params['type'] = 'json'
    async with session.get(url, params=params) as resp:
        result = await resp.json()
    await session.close()
    return result


async def search_packages(name):
    return make_request('%s/search/' % BASE_URL, {'q': name})


async def get_package_info(name):
    return make_request('%s/packages/%s' % (BASE_URL, name))