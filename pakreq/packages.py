# packages.py

"""
Simple packages site API library
"""

import logging

from aiohttp import ClientSession, client_exceptions

BASE_URL = 'https://packages.aosc.io'
logger = logging.getLogger(__name__)


async def make_request(url, params={}):
    """Make request to packages site"""
    session = ClientSession()
    if 'type' not in params.keys():
        params['type'] = 'json'
    async with session.get(url, params=params) as resp:
        try:
            result = await resp.json()
        except client_exceptions.ContentTypeError as e:
            logger.error(
                'Request failed: url (%s) params (%s) exception (%s)' % (url, params, e)
            )
            await session.close()
            return None
    await session.close()
    return result


async def search_packages(name):
    """Search packages on packages site"""
    return await make_request('%s/search/' % BASE_URL, {'q': name})


async def get_package_info(name):
    """Get detailed info of a package from packages site"""
    return await make_request('%s/packages/%s' % (BASE_URL, name))
