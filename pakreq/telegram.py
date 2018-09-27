# telegram.py

"""
Telegram bot
"""

import asyncio
import logging

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor

import pakreq.db

from pakreq.utils import get_type, password_hash

logger = logging.getLogger(__name__)


class pakreqBot(object):
    """pakreqBot main object"""
    def __init__(self, config):
        self.app = dict()
        self.app['config'] = config
        self.bot = Bot(token=self.app['config']['telegram']['token'])
        self.dp = Dispatcher(self.bot)

    async def init_db(self):
        """Init databse connection"""
        await pakreq.db.init_db(self.app)

    async def ping(self, message: types.Message):
        """Implementation of /ping, pong"""
        logger.info(
            'Received ping from Telegram user: %s' % message.from_user.id
        )
        await message.reply('pong')

    async def register(self, message: types.Message):
        """Implementation of /register, register new user"""
        logger.info('Registering new user: %s' % message.chat.id)
        splitted = message.text.split()
        if len(splitted) == 2:
            username = splitted[1]
        elif len(splitted) > 2:
            await message.reply('Too many arguments')
            return
        else:
            username = message.from_user.username or message.from_user.id
        async with self.app['db'].acquire() as conn:
            users = await pakreq.db.get_users(conn)
        if users is not None:
            for user in users:
                if pakreq.db.OAuthInfo(string=user['oauth_info'])\
                        .info['telegram_id'] == message.from_user.id:
                    await message.reply('You\'ve already registered')
                    return
                if user['username'] == username:
                    await message.reply('Username already taken, please choose \
                        another one by <code>/register <username></code>')
        try:
            oauth_info = pakreq.db.OAuthInfo(telegram_id=message.from_user.id)
            async with self.app['db'].acquire() as conn:
                await pakreq.db.new_user(
                    conn, username=username, oauth_info=oauth_info
                )
            await message.reply(
                'Registeration successful, your username is %s' % username
            )
        except Exception:
            await message.reply('Unable to register, please contact admin')

    async def set_password(self, message: types.Message):
        """Implementation of /set_pw, set password for user"""
        logger.info(
            'Setting new password for Telegram user: %s' % message.from_user.id
        )
        splitted = message.text.split()
        if len(splitted) == 2:
            async with self.app['db'].acquire() as conn:
                users = await pakreq.db.get_users(conn)
            for user in users:
                if pakreq.db.OAuthInfo(string=user['oauth_info'])\
                        .info['telegram_id'] == message.from_user.id:
                    async with self.app['db'].acquire() as conn:
                        await pakreq.db.update_user(
                            conn, user['id'],
                            password_hash=password_hash(
                                user['id'],
                                splitted[1],
                                self.app['config']['salt']
                            )
                        )
                    await message.reply('Success.')
                    return
            await message.reply('You have to register or login first')
        else:
            await message.reply('Invalid request')

    async def list_requests(self, message: types.Message):
        """Implementation of /list, list requests"""
        logger.info('Received /list: %s' % message.text)
        splitted = message.text.split()
        result = ''
        if len(splitted) == 1:
            if message.chat.id < 0:
                await message.reply(
                    'Listing all requests is only allowed in private chat'
                )
                return
            async with self.app['db'].acquire() as conn:
                requests = await pakreq.db.get_requests(conn)
            count = 0
            for request in requests:
                if count <= 10:
                    result = result +\
                        'ID: %s <b>%s</b>(%s): %s\n' %\
                        (
                            request['id'], request['name'],
                            get_type(request['type']), request['description']
                        )
                    count += 1
                else:
                    break
            if count > 10:
                result = result +\
                    '\nPlease visit %s for the complete listing' %\
                    self.app['config']['base_url']
        elif (len(splitted) > 1) and (len(splitted) <= 5):
            for id in splitted[1:]:
                async with self.app['db'].acquire() as conn:
                    try:
                        request = await pakreq.db.get_request_detail(conn, id)
                        result = result + '<b>%s</b>:\n' % request['name']
                        result = result +\
                            '  <b>Type</b>: %s\n' %\
                            get_type(request['type'])
                        result = result +\
                            '  <b>Description</b>: %s\n' %\
                            request['description']
                        result = result +\
                            '  <b>Requester</b>: %s(%s)\n' %\
                            (
                                request['requester']['username'],
                                request['requester']['id']
                            )
                        result = result +\
                            '  <b>Packager</b>: %s(%s)\n' %\
                            (
                                request['packager']['username'],
                                request['packager']['id']
                            )
                        result = result +\
                            '  <b>Pub date</b>: %s\n' %\
                            request['pub_date'].isoformat()
                        result = result +\
                            '  <b>ETA</b>: %s\n' %\
                            (request['eta'] or 'Unset')
                        result = result + '\n'
                    except Exception:
                        result = result +\
                            '<b>Request ID %s not found.</b>\n' %\
                            id
        else:
            result = 'Too many arugments'
        if result == '':
            result = 'No pending requests'
        await message.reply(result, parse_mode='HTML')

    def start(self):
        """Register message handlers, and start the bot"""
        self.dp.register_message_handler(
            self.ping, commands=['ping']
        )
        self.dp.register_message_handler(
            self.list_requests, commands=['list']
        )
        self.dp.register_message_handler(
            self.register, commands=['register']
        )
        self.dp.register_message_handler(
            self.set_password, commands=['set_pw']
        )
        executor.start_polling(self.dp)


def start_bot(config):
    """Start the bot"""
    bot = pakreqBot(config)
    # TODO: Make this more elegant
    loop = asyncio.get_event_loop()
    loop.run_until_complete(bot.init_db())
    bot.start()
