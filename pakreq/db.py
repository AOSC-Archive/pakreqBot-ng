# db.py

"""
Database management utils
"""
import aiosqlite3.sa

from datetime import datetime
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

async def get_rows(conn, table):
    result = await conn.execute(
        table.select()
    )
    return [dict(r) for r in await result.fetchall()]

async def get_row(conn, table, id):
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
    conn, status=0, rtype=0, name="Unknown",
    description="Unknown", requester_id=0,
    packager_id=0, date=datetime.now(),
    eta=None
):
    # Initializing values
    id = await get_max_id(conn, REQUEST) + 1
    statement = REQUEST.insert(None).values(
        id=id, status=status, type=rtype, name=name,
        description=description, requester_id=requester_id,
        packager_id=packager_id, pub_date=date,
        eta=eta
    )
    await conn.execute(statement)
    await conn.commit()

async def get_request_detail(conn, id):
    result = await get_row(conn, REQUEST, id)
    # Get requester & packager information
    try:
        result['requester'] = await get_row(conn, USER, result['requester_id'])
    except:
        result['requester'] = dict(id='0', username='Unknown')
    try:
        result['packager'] = await get_row(conn, USER, result['packager_id'])
    except:
        result['packager'] = dict(id='0', username='Unknown')
    return result

async def new_user(
    conn, username, admin=0,
    password_hash=None, telegram_id=None 
):
    # Initializing values
    id = await get_max_id(conn, USER) + 1
    print(id)
    id += 1# Larger than existing max id by 1
    statement = USER.insert(None).values(
        id=id, username=username, admin=admin,
        password_hash=password_hash, telegram_id=telegram_id
    )
    await conn.execute(statement)
    await conn.commit()

async def get_users(conn):
    return await get_rows(conn, USER)

async def get_requests(conn):
    return await get_rows(conn, REQUEST)

async def get_max_user_id(conn):
    return await get_max_id(conn, USER)

async def get_max_request_id(conn):
    return await get_max_id(conn, REQUEST)

async def get_user(conn, id):
    return await get_row(conn, USER, id)

async def get_request(conn, id):
    return await get_row(conn, REQUEST, id)

async def update_user(conn, id, **kwargs):
    await update_row(conn, USER, id, kwargs)

async def update_request(conn, id, **kwargs):
    await update_row(conn, REQUEST, id, kwargs)