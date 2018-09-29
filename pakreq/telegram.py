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
import pakreq.telegram_consts

from pakreq.utils import get_type, password_hash

logger = logging.getLogger(__name__)


def escape(text):
    """Escape string to avoid explosion"""
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


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

    async def show_help(self, message: types.Message):
        """Help message"""
        await message.reply(
            pakreq.telegram_consts.HELP_CRUFT, parse_mode='HTML')

    async def new_request(self, message: types.Message):
        """Implementation of /pakreq, /updreq, /optreq, add new request"""
        def handle_request(command):
            return {
                '/pakreq': pakreq.db.RequestType.PAKREQ,
                '/optreq': pakreq.db.RequestType.OPTREQ,
                '/updreq': pakreq.db.RequestType.UPDREQ
            }.get(command, -1)  # There should be only 3 types of requests
        splitted = message.text.split(maxsplit=2)
        logger.info('Adding new request: %s' % splitted[1])
        description = 'Unavailable'
        if len(splitted) < 2:
            await message.reply('Too few arguments')
            return
        elif len(splitted) == 3:
            description = splitted[2]
        rtype = handle_request(splitted[0])
        if rtype == -1:
            logging.error('Unexpected request type: %s' % splitted[0])
            await message.reply(pakreq.telegram_consts.error_msg(
                'Programming error'
            ))
            return
        async with self.app['db'].acquire() as conn:
            requests = await pakreq.db.get_requests(conn)
            for request in requests:
                if (request['name'] == splitted[1]) and\
                        (request['type'] == rtype):
                    await message.reply(
                        'Request %s is already in the list' %
                        splitted[1]
                    )
                    return
            id = await pakreq.db.get_max_request_id(conn) + 1
            await pakreq.db.new_request(conn, id=id, rtype=rtype,
                                        name=splitted[1],
                                        description=description)
        await message.reply(
            'Successfully added %s to the list, ID of this request is %s' %
            (splitted[1], id)
        )

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
                        another one using <code>/register <username></code>')
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

    async def link_account(self, message: types.Message):
        """Implementation of /link, link telegram account to pakreq account"""
        logger.info(
            'Received request to link telegram account: %s' %
            message.from_user.id
        )
        splitted = message.text.split()
        if len(splitted) == 3:
            success = False
            async with self.app['db'].acquire() as conn:
                users = await pakreq.db.get_users(conn)
            for user in users:
                if user['username'] == splitted[1]:
                    p_hash = password_hash(
                        user['id'],
                        splitted[2],
                        self.app['config']['salt']
                    )
                    if user['password_hash'] == p_hash:
                        async with self.app['db'].acquire() as conn:
                            await pakreq.db.update_user(
                                conn,
                                user['id'],
                                oauth_info=pakreq.db.OAuthInfo(
                                    string=user['oauth_info']
                                    ).edit(
                                        telegram_id=message.from_user.id
                                    ).output()
                            )
                        success = True
                        break
            if success:
                # Unlink this Telegram account from other pakreq accounts
                # TODO: Make this more elegant
                for user in users:
                    if user['username'] != splitted[1]:
                        if pakreq.db.OAuthInfo(string=user['oauth_info'])\
                                .info['telegram_id'] == message.from_user.id:
                                async with self.app['db'].acquire() as conn:
                                    await pakreq.db.update_user(
                                        conn,
                                        user['id'],
                                        oauth_info=pakreq.db.OAuthInfo(
                                            string=user['oauth_info']
                                        ).edit(
                                            telegram_id=None
                                        ).output()
                                    )
                await message.reply('Success.')
            else:
                await message.reply('Incorrect username or password')
        else:
            await message.reply('Invalid request')

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
            await message.reply(
                'You have to register or link your account first'
            )
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
                if count < 10:
                    result = result +\
                        'ID: %s <b>%s</b> (%s): %s\n' %\
                        (
                            request['id'], escape(request['name']),
                            get_type(request['type']),
                            escape(request['description'])
                        )
                    count += 1
                else:
                    break
            if count >= 10:
                result += '\nPlease visit %s for the complete listing' %\
                    self.app['config']['base_url']
        elif (len(splitted) > 1) and (len(splitted) <= 5):
            for id in splitted[1:]:
                async with self.app['db'].acquire() as conn:
                    try:
                        request = await pakreq.db.get_request_detail(conn, id)
                        result += pakreq.telegram_consts.REQUEST_DETAIL.format(
                            name=escape(request['name']),
                            id=request['id'],
                            type=get_type(request['type']),
                            desc=escape(request['description']),
                            req_name=escape(request['requester']['username']),
                            req_id=request['requester']['id'],
                            pak_name=escape(request['packager']['username']),
                            pak_id=request['packager']['id'],
                            date=request['pub_date'].isoformat(),
                            eta=(request['eta'] or 'Unset'))

                    except Exception:
                        result += '<b>Request ID %s not found.</b>\n' % id
        else:
            result = 'Too many arugments'
        if result == '':
            result = 'No pending requests'
        await message.reply(result, parse_mode='HTML')

    def start(self):
        """Register message handlers, and start the bot"""
        commands_mapping = [
            (['ping'], self.ping),
            (['list'], self.list_requests),
            (['register'], self.register),
            (['passwd'], self.set_password),
            (['help'], self.show_help),
            (['pakreq', 'updreq', 'optreq'], self.new_request)
        ]
        for command in commands_mapping:
            logging.info('Registering command: %s' % command[0])
            self.dp.register_message_handler(command[1], commands=command[0])
        executor.start_polling(self.dp)


def start_bot(config):
    """Start the bot"""
    bot = pakreqBot(config)
    # TODO: Make this more elegant
    loop = asyncio.get_event_loop()
    loop.run_until_complete(bot.init_db())
    bot.start()
