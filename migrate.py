#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import sys
import asyncio
import aiosqlite3

from datetime import datetime

import pakreq.pakreq
from pakreq import db, settings
from pakreq.utils import get_type
from pakreq.telegram import find_user


OLD_DB = 'old.db'


async def migrate_user(conn, telegram_id, username=None):
    username = username or telegram_id
    print('>>> Adding user %s(%s)' % (username, telegram_id))
    users = await pakreq.pakreq.get_users(conn)
    if not find_user(users, telegram_id):
        await pakreq.pakreq.new_user(
            conn, username,
            oauth_info=db.OAuthInfo(telegram_id=telegram_id)
        )


async def process_requester(conn, telegram_id, username):
    users = await pakreq.pakreq.get_users(conn)
    if telegram_id is not None:
        packager = find_user(users, telegram_id)
        if not packager:
            await migrate_user(conn, telegram_id, username)
            users = await pakreq.pakreq.get_users(conn)
            return find_user(users, telegram_id)
        else:
            return packager
    else:
        return {'id': 0}


async def main(event_loop):
    print('Migration start\n===============')
    # Prepare for DB utility
    app = dict()
    app['config'] = settings.get_config(sys.argv[1:])
    await db.init_db(app)
    # Connect the old DB
    conn_old = await aiosqlite3.connect(OLD_DB, loop=event_loop)
    cur = await conn_old.cursor()
    # Fetch users from old DB
    await cur.execute('SELECT * FROM users')
    users_old = await cur.fetchall()
    async with app['db'].acquire() as conn:
        for user in users_old:
            await migrate_user(conn, user[0], user[1])
    await cur.close()
    # Fetch requests from old DB
    cur = await conn_old.cursor()
    await cur.execute('SELECT * FROM pakreq')
    requests = await cur.fetchall()
    async with app['db'].acquire() as conn:
        for request in requests:
            name = request[0]
            desc = request[1]
            if desc == '<No description> ':
                desc = 'Unavailable'
            rtype = db.RequestType(int(request[2]) - 1)
            packager = await process_requester(conn, request[4], request[3])
            requester = await process_requester(conn, request[6], request[5])
            date = datetime.strptime(request[7], '%Y-%m-%d %H:%M:%S %Z')
            note = request[8]
            print('>>> Adding request %s(%s): %s' % (name, get_type(rtype), desc))
            await pakreq.pakreq.new_request(
                conn, rtype=rtype, name=name,
                description=desc, requester_id=requester['id'],
                packager_id=packager['id'], date=date,
                note=note
            )
    # Close connections, clean up.
    print('Cleaning up...')
    await cur.close()
    await conn_old.close()
    await db.close_db(app)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
    print('Done!')
