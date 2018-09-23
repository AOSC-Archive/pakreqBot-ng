# db.py

"""
Database management utils
"""
import datetime
import aiosqlite3.sa

from sqlalchemy import (
    MetaData, Table, Column, ForeignKey,
    Integer, String, Date
)
from sqlalchemy.sql.expression import func

__all__ = ['USER', 'REQUEST']

META = MetaData()

USER = Table(
    'user', META,

    Column('id', Integer, primary_key=True, unique=True),
    Column('username', String, nullable=False, unique=True),
    Column('admin', Integer, nullable=False), # 0 -> non-admin, 1 -> admin
    Column('password_hash', String, nullable=True),
    Column('telegram_id', Integer, nullable=True),
    sqlite_autoincrement=True
)

REQUEST = Table(
    'request', META,

    Column('id', Integer, primary_key=True, unique=True),
    Column('status', Integer, nullable=False), # 0 -> open, 1 -> done, 2 -> rejected
    Column('type', Integer, nullable=False), # 0 -> pakreq, 1 -> updreq, 2 -> optreq
    Column('name', String, nullable=False),
    Column('description', String, nullable=True),
    Column('requester_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('packager_id', Integer, ForeignKey('user.id')),
    Column('pub_date', Date, nullable=False),
    Column('eta', String, nullable=True),
    sqlite_autoincrement=True
)

class RecordNotFoundException(Exception):
    """Requested record in database was not found"""

async def init_db(app):
    conf = app['config']['db']
    engine = await aiosqlite3.sa.create_engine(
        conf['location']
    )
    app['db'] = engine

async def close_db(app):
    app['db'].close()
    await app['db'].wait_closed()

async def get_max_user_id(conn):
    max_id = await conn.execute("SELECT MAX(id) FROM user")
    max_id = await max_id.fetchone()
    if max_id:
        return max_id[0]
    else:
        return None

async def get_max_request_id(conn):
    max_id = await conn.execute("SELECT MAX(id) FROM request")
    max_id = await max_id.fetchone()
    if max_id:
        return max_id[0]
    else:
        return None

async def new_request(
    conn, status=0, rtype=0, name="Unknown",
    description="Unknown", requester_id=0,
    packager_id=0, date=datetime.datetime.now(),
    eta=None
):
    # Initializing values
    id = await get_max_request_id(conn) or 0
    id += 1 # Larger than existing max id by 1
    statement = REQUEST.insert().values(
        id=id, status=status, type=rtype, name=name,
        description=description, requester_id=requester_id,
        packager_id=packager_id, pub_date=date,
        eta=eta
    )
    await conn.execute(statement)
    await conn.commit()

async def get_requests(conn):
    result = await conn.execute(
        REQUEST.select()
    )
    return await result.fetchall()

async def get_request_detail(conn, request_id):
    result = await conn.execute(
        REQUEST.select()
        .where(REQUEST.c.id == request_id)
    )
    request_record = await result.fetchone()
    if not result:
        msg = "Request with id: {} does not exists"
        raise RecordNotFoundException(msg.format(request_id))
    # Get requester & packager information
    result = await conn.execute(
        USER.select()
        .where(USER.c.id == request_record['requester_id'])
    )
    requester_record = await result.fetchone()
    result = await conn.execute(
        USER.select()
        .where(USER.c.id == request_record['packager_id'])
    )
    packager_record = await result.fetchone()
    return request_record, requester_record, packager_record

async def new_user(
    conn, username, admin=0,
    password_hash=None, telegram_id=None 
):
    # Initializing values
    id = await get_max_user_id(conn) or 0
    print(id)
    id += 1# Larger than existing max id by 1
    statement = USER.insert().values(
        id=id, username=username, admin=admin,
        password_hash=password_hash, telegram_id=telegram_id
    )
    await conn.execute(statement)
    await conn.commit()

async def get_user(conn, id):
    result = await conn.execute(
        USER.select()
        .where(USER.c.id == id)
    )
    return await result.fetchone()

async def get_users(conn):
    result = await conn.execute(
        USER.select()
    )
    return result.fetchall()