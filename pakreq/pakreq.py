# pakreq.py

import uvloop
import asyncio
import logging

from datetime import datetime
from packaging import version
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from pakreq.db import (
    OAuthType, RequestStatus, RequestType, REQUEST, USER, OAUTH
)
from pakreq.db import get_max_id, get_row, get_rows, update_row, init_db
from pakreq.packages import get_package_info, search_packages

from sqlalchemy.sql import (select, or_, and_)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def find_package(name):
    info = await get_package_info(name)
    if not info:
        return None
    if 'pkg' in info.keys():
        return info['pkg']['name']
    info = await search_packages(name)
    if not info:
        return None
    name_stripped = name.replace('-', '')
    for package in info['packages']:
        if package['name'] == name or package['name'] == name_stripped:
            return package['name']
    return None


async def new_request(
    conn, id=None, status=RequestStatus.OPEN, rtype=RequestType.PAKREQ,
    name='Unknown', description='Unknown',
    requester_id=0, packager_id=0,
    date=datetime.now(), note=None
):
    """Create new request"""
    # Initializing values
    id = id or (await get_max_id(conn, REQUEST) + 1)
    statement = REQUEST.insert(None).values(
        id=id, status=status, type=rtype, name=name,
        description=description, requester_id=requester_id,
        packager_id=packager_id, pub_date=date,
        note=note
    )
    await conn.execute(statement)
    await conn.commit()


async def get_request_detail(conn, id):
    """Not just fetch request info, but also user info"""
    result = await get_row(conn, REQUEST, id)
    # Get requester & packager information
    try:
        query = await get_row(conn, USER, result['requester_id'])
        result['requester'] = dict(id=query['id'], username=query['username'], admin=query['admin'])
    except Exception:
        result['requester'] = dict(id='0', username='Unknown')
    try:
        await get_row(conn, USER, result['packager_id'])
        result['packager'] = dict(id=query['id'], username=query['username'], admin=query['admin'])
    except Exception:
        result['packager'] = dict(id='0', username='Unknown')
    return result


async def new_user(conn, username, id=None, admin=False, password_hash=None):
    """Create new user"""
    # Initializing values
    id = id or (await get_max_id(conn, USER) + 1)
    statement = USER.insert(None).values(
        id=id, username=username, admin=admin,
        password_hash=password_hash,
    )
    await conn.execute(statement)
    await conn.commit()


async def get_users(conn):
    """List all the users (wrapper of get_rows)"""
    return await get_rows(conn, USER)


async def get_requests(conn):
    """List all the requests (wrapper of get_rows)"""
    return await get_rows(conn, REQUEST)


async def search_requests(conn, keyword):
    """Search through requests"""
    keyword = '%{}%'.format(keyword)
    query = select([REQUEST]).where(
        or_(
            REQUEST.c.name.like(keyword),
            REQUEST.c.description.like(keyword)
        )
    ).order_by(REQUEST.c.id).limit(10)
    results = await conn.execute(query, keyword=keyword)
    return await results.fetchall()


async def get_max_user_id(conn):
    """Fetch max user id (wrapper of get_max_id)"""
    return await get_max_id(conn, USER)


async def get_max_request_id(conn):
    """Fetch max request id (wrapper of get_max_id)"""
    return await get_max_id(conn, REQUEST)


async def get_user(conn, id):
    """Get user info by ID (wrapper of get_row)"""
    return await get_row(conn, USER, id)


async def get_user_by_name(conn, name):
    """Get user info by name (only the first match will be returned)"""
    query = select([USER]).where(
        or_(USER.c.id == name, USER.c.username == name)
    ).limit(1)
    query = await conn.execute(query)
    user = await query.fetchone()
    return user

# OAuth related functions


async def get_user_from_oauth_id(conn, type, oid):
    """Get user info by OAuth type and ID"""
    query = select([USER]).select_from(
        USER.join(OAUTH, OAUTH.c.uid == USER.c.id)
    ).where(
            and_(OAUTH.c.type == type, OAUTH.c.oid == oid)
        ).order_by(USER.c.id).limit(1)
    results = await conn.execute(query)
    return await results.fetchone()


async def get_oauth_from_user_id(conn, uid, type):
    """Get OAuth info by user id"""
    query = select([OAUTH]).where(
            and_(OAUTH.c.uid == uid, OAUTH.c.type == type)
        ).limit(1)
    results = await conn.execute(query)
    results = await results.fetchone()
    return results


async def new_oauth_from_user_id(conn, uid, type, oid=None, token=None):
    results = await get_oauth_from_user_id(conn, uid, type)
    if results is None:
        query = OAUTH.insert().values(
            uid=uid, type=type, oid=oid, token=token
        )
        await conn.execute(query)
        await conn.commit()
    return


async def delete_oauth(conn, type, oid):
    action = OAUTH.delete().where(
            and_(OAUTH.c.type == type, OAUTH.c.oid == oid)
        )
    await conn.execute(action)
    await conn.commit()


async def get_oauth_from_oid(conn, type, oid=None):
    query = select([OAUTH]).where(
            and_(OAUTH.c.type == type, OAUTH.c.oid == oid)
        )
    results = await conn.execute(query)
    return await results.fetchall()


async def get_request(conn, id):
    """Get request info by ID (wrapper of get_row)"""
    return await get_row(conn, REQUEST, id)


async def get_requests_by_user(conn, id):
    """Fetch all the requests that are requested by user"""
    query = select([REQUEST]).where(REQUEST.c.requester_id == id)
    results = await conn.execute(query)
    return await results.fetchall()


async def update_user(conn, id, **kwargs):
    """Update user by ID (wrapper of update_row)"""
    await update_row(conn, USER, id, kwargs)


async def update_request(conn, id, **kwargs):
    """Update request by ID (wrapper of update_row)"""
    await update_row(conn, REQUEST, id, kwargs)


async def get_open_requests(conn):
    """Gets all the open requests"""
    query = select([REQUEST]).where(REQUEST.c.status == RequestStatus.OPEN)
    results = await conn.execute(query)
    return await results.fetchall()


# Daemon part
class Daemon(object):
    """Maintenance daemon"""

    def __init__(self, config):
        self.app = dict()
        self.app['config'] = config

    async def init_db(self):
        """Initialize database connection"""
        await init_db(self.app)

    async def clean(self):
        """Cleanup finished requests"""
        logger.info('Start cleaning...')
        async with self.app['db'].acquire() as conn:
            requests = await get_open_requests(conn)
            for request in requests:
                logger.debug('Processing %s (ID: %s)...' %
                             (request['name'], request['id']))
                if request['type'] == RequestType.PAKREQ:
                    if await find_package(request['name']):
                        logger.info('%s has been packaged, closing' %
                                    request['name'])
                        await update_request(
                            conn, request['id'], status=RequestStatus.DONE,
                            note='(BOT) This package has been packaged.'
                        )
                elif request['type'] == RequestType.UPDREQ:
                    if await find_package(request['name']):
                        info = await get_package_info(request['name'])
                        if version.parse(info['pkg']['version']) >= version.parse(request['description']):
                            logger.info(
                                '%s has been upgraded, closing...' % request['name'])
                            await update_request(
                                conn, request['id'], status=RequestStatus.DONE,
                                note='(BOT) This package has been updated to: %s' % info[
                                    'pkg']['version']
                            )
                    else:
                        await update_request(
                            conn, request['id'], status=RequestStatus.REJECTED,
                            note='404 Package not found'
                        )

    def start(self):
        scheduler = AsyncIOScheduler()
        scheduler.add_job(self.clean, 'interval', seconds=1800,
                          next_run_time=datetime.now())
        scheduler.start()


def start_daemon(config):
    daemon = Daemon(config)
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    loop = asyncio.get_event_loop()
    loop.run_until_complete(daemon.init_db())
    daemon.start()
    try:
        loop.run_forever()
    except (KeyboardInterrupt, SystemExit):
        pass
