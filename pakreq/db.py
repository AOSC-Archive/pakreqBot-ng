# db.py

import aiosqlite

async def init_db(app):
    conf = app['config']['db']
    app['db'] = aiosqlite.connect(conf['location'])

async def close_db(app):
    await app['db'].close()
