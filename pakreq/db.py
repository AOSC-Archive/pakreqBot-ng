# db.py

"""
Database management utils
"""

import enum
import json
import aiosqlite3.sa

from datetime import datetime
from sqlalchemy import (
    MetaData, Table, Column, ForeignKey,
    Integer, String, Date, Boolean, Enum
)

__all__ = ['USER', 'REQUEST']


class RequestType(enum.Enum):
    """Types of requests"""
    PAKREQ = 0
    UPDREQ = 1
    OPTREQ = 2


class RequestStatus(enum.Enum):
    """Statuses of requests"""
    OPEN = 0
    DONE = 1
    REJECTED = 2


class OAuthInfo():
    """OAuth info"""
    # TODO: Make this more elegant
    def __init__(
        self, string=None, github_id=None,
        telegram_id=None, aosc_id=None
    ):
        self.info = dict()
        if string is None:
            self.info['github_id'] = github_id
            self.info['telegram_id'] = telegram_id
            self.info['aosc_id'] = aosc_id
        else:
            loaded = json.loads(string)
            self.info['github_id'] = loaded['github_id'] or None
            self.info['telegram_id'] = loaded['telegram_id'] or None
            self.info['aosc_id'] = loaded['aosc_id'] or None

    def edit(self, **kwargs):
        """Edit OAuthInfo"""
        for key in self.info.keys():
            if key in kwargs:
                self.info[key] = kwargs.get(key)
        return self

    def output(self):
        """Output OAuthInfo in JSON format"""
        output = self.info
        if output is not None:
            output = json.dumps(output)
        return output


META = MetaData()


# Users table
USER = Table(
    'user', META,

    Column('id', Integer, primary_key=True, unique=True),
    Column('username', String, nullable=False, unique=True),
    Column('admin', Boolean, nullable=False),  # 0 -> non-admin, 1 -> admin
    Column('password_hash', String, nullable=True),
    Column('oauth_info', String, nullable=True),
    sqlite_autoincrement=True
)


# Request table
REQUEST = Table(
    'request', META,

    Column('id', Integer, primary_key=True, unique=True),
    Column('status', Enum(RequestStatus), nullable=False),
    Column('type', Enum(RequestType), nullable=False),
    Column('name', String, nullable=False),
    Column('description', String, nullable=True),
    Column('requester_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('packager_id', Integer, ForeignKey('user.id')),
    Column('pub_date', Date, nullable=False),
    Column('note', String, nullable=True),
    sqlite_autoincrement=True
)


class RecordNotFoundException(Exception):
    """Requested record in database was not found"""


async def init_db(app):
    """Initialize database connection"""
    conf = app['config']['db']
    engine = await aiosqlite3.sa.create_engine(
        conf['location']
    )
    app['db'] = engine


async def close_db(app):
    """Close database connection"""
    app['db'].close()
    await app['db'].wait_closed()


async def get_rows(conn, table):
    """Fetch all the rows"""
    result = await conn.execute(
        table.select()
    )
    return [dict(r) for r in await result.fetchall()]


async def get_row(conn, table, id):
    """Find row by ID"""
    result = await conn.execute(
        table.select()
        .where(table.c.id == id)
    )
    result = await result.fetchone()
    if result is None:
        msg = "Row with id: {} does not exists"
        raise RecordNotFoundException(msg.format(id))
    return dict(zip(result.keys(), result.values()))


async def get_max_id(conn, table):
    """Get max id of a table"""
    # TODO: Make this more elegant
    if table is REQUEST:
        max_id = await conn.execute("SELECT MAX(id) FROM request")
    elif table is USER:
        max_id = await conn.execute("SELECT MAX(id) FROM user")
    else:
        raise ValueError
    max_id = await max_id.fetchone()
    if max_id:
        return max_id[0] or 0
    else:
        return 0


async def update_row(conn, table, id, kwargs):
    """Update row by ID"""
    if kwargs is not None:
        orig_values = await get_row(conn, table, id)
        new_values = dict()
        for key, value in orig_values.items():
            if key in kwargs:
                new_values[key] = kwargs.get(key)
            else:
                new_values[key] = value
        await conn.execute(
            table.update(None)
            .where(table.c.id == id)
            .values(
                new_values
            )
        )
        await conn.commit()


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
        result['requester'] = await get_row(conn, USER, result['requester_id'])
    except Exception:
        result['requester'] = dict(id='0', username='Unknown')
    try:
        result['packager'] = await get_row(conn, USER, result['packager_id'])
    except Exception:
        result['packager'] = dict(id='0', username='Unknown')
    return result


async def new_user(
    conn, username, id=None, admin=False,
    password_hash=None, oauth_info=OAuthInfo()
):
    """Create new user"""
    # Initializing values
    id = id or (await get_max_id(conn, USER) + 1)
    statement = USER.insert(None).values(
        id=id, username=username, admin=admin,
        password_hash=password_hash,
        oauth_info=oauth_info.output()
    )
    await conn.execute(statement)
    await conn.commit()


async def get_users(conn):
    """List all the users (wrapper of get_rows)"""
    return await get_rows(conn, USER)


async def get_requests(conn):
    """List all the requests (wrapper of get_rows)"""
    return await get_rows(conn, REQUEST)


async def get_max_user_id(conn):
    """Fetch max user id (wrapper of get_max_id)"""
    return await get_max_id(conn, USER)


async def get_max_request_id(conn):
    """Fetch max request id (wrapper of get_max_id)"""
    return await get_max_id(conn, REQUEST)


async def get_user(conn, id):
    """Get user info by ID (wrapper of get_row)"""
    return await get_row(conn, USER, id)


async def get_request(conn, id):
    """Get request info by ID (wrapper of get_row)"""
    return await get_row(conn, REQUEST, id)


async def update_user(conn, id, **kwargs):
    """Update user by ID (wrapper of update_row)"""
    await update_row(conn, USER, id, kwargs)


async def update_request(conn, id, **kwargs):
    """Update request by ID (wrapper of update_row)"""
    await update_row(conn, REQUEST, id, kwargs)
