# db.py

"""
Database management utils
"""

import enum
import aiosqlite3.sa
from argon2 import PasswordHasher

from sqlalchemy import (
    MetaData, Table, Column, ForeignKey,
    Integer, String, Date, Boolean, Enum
)


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


class OAuthType(enum.Enum):
    """OAuth Type"""
    Telegram = 0
    GitHub = 1
    AOSC = 2


META = MetaData()


# Users table
USER = Table(
    'user', META,

    Column('id', Integer, primary_key=True, unique=True),
    Column('username', String, nullable=False, unique=True),
    Column('admin', Boolean, nullable=False),  # 0 -> non-admin, 1 -> admin
    Column('password_hash', String, nullable=True),
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

# OAuth
OAUTH = Table(
    'oauth', META,

    Column('uid', Integer, ForeignKey('user.id'), primary_key=True),
    Column('type', Enum(OAuthType), nullable=False, primary_key=True),
    Column('oid', String),
    Column('token', String)
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


async def check_password(conn, name, password):
    """Check password and rotate cleartext password if needed"""
    from pakreq.pakreq import update_user, get_user_by_name
    from pakreq.utils import password_hash, password_verify
    user = await get_user_by_name(conn, name)
    status = False
    hash = user['password_hash']
    if password_verify(user['id'], password, hash):
        status = True
        hasher = PasswordHasher()
        if hasher.check_needs_rehash(hash):
            hash = password_hash(user['id'], password)
            await update_user(conn, user['id'], password_hash=hash)

    return status
