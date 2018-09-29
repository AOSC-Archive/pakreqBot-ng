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

from pakreq.utils import get_type, get_status, password_hash

logger = logging.getLogger(__name__)


def escape(text):
    """Escape string to avoid explosion"""
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def find_user(users, id):
    for user in users:
        if pakreq.db.OAuthInfo(string=user['oauth_info'])\
                .info['telegram_id'] == id:
            return user['id']
    return None


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
        await message.reply('<b>pong</b>', parse_mode='HTML')

    async def show_help(self, message: types.Message):
        """Implementation of /help, show help message"""
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
            await message.reply(
                pakreq.telegram_consts.TOO_FEW_ARGUMENTS,
                parse_mode='HTML'
            )
            return
        elif len(splitted) == 3:
            description = splitted[2]
        rtype = handle_request(splitted[0])
        if rtype == -1:
            logging.error('Unexpected request type: %s' % splitted[0])
            await message.reply(pakreq.telegram_consts.error_msg(
                'Unexpected request type'
            ))
            return
        async with self.app['db'].acquire() as conn:
            users = await pakreq.db.get_users(conn)
            user_id = find_user(users, message.from_user.id)
            if user_id is None:
                await message.reply(
                    pakreq.telegram_consts.REGISTER_FIRST,
                    parse_mode='HTML'
                )
                return
            requests = await pakreq.db.get_requests(conn)
            for request in requests:
                if (request['name'] == splitted[1]) and\
                        (request['type'] == rtype):
                    await message.reply(
                        pakreq.telegram_consts.IS_ALREADY_IN_THE_LIST
                        .format(
                            rtype=escape(splitted[0][1:].capitalize()),
                            name=escape(str(splitted[1]))
                        ),
                        parse_mode='HTML'
                    )
                    return
            id = await pakreq.db.get_max_request_id(conn) + 1
            await pakreq.db.new_request(
                conn, id=id, rtype=rtype,
                name=splitted[1],
                description=description,
                requester_id=user_id
            )
        await message.reply(
            pakreq.telegram_consts.SUCCESSFULLY_ADDED.format(
                rtype=escape(splitted[0][1:]),
                name=escape(str(splitted[1])),
                id=str(id)
            )
        )

    async def claim_request(self, message: types.Message):
        splitted = message.text.split()
        if len(splitted) < 2:
            await message.reply('Too few arguments')
            return
        logger.info(
            'Received request to claim or unclaim request: %s' %
            message.text
        )
        if splitted[0] == '/claim':
            claim = True
        else:
            claim = False
        result = ''
        async with self.app['db'].acquire() as conn:
            users = await pakreq.db.get_users(conn)
            user_id = find_user(users, message.from_user.id)
            if user_id is None:
                await message.reply(
                    pakreq.telegram_consts.REGISTER_FIRST,
                    parse_mode='HTML'
                )
                return
            for id in splitted[1:]:
                new_user_id = user_id
                try:
                    request = await pakreq.db.get_request(conn, int(id))
                    if not claim:
                        if user_id != request['packager_id']:
                            result += pakreq.telegram_consts.CLAIM_FIRST\
                                .format(
                                    id=id
                                )
                            continue
                        else:
                            new_user_id = None
                    await pakreq.db.update_request(
                        conn, int(id),
                        packager_id=new_user_id
                    )
                    result += pakreq.telegram_consts.ACTION_SUCCESSFUL.format(
                        action=splitted[0][1:],
                        id=id
                    )
                except (pakreq.db.RecordNotFoundException, ValueError):
                    result += pakreq.telegram_consts.REQUEST_NOT_FOUND.format(
                        id=id
                    )
        await message.reply(
            result, parse_mode='HTML'
        )

    async def register(self, message: types.Message):
        """Implementation of /register, register new user"""
        logger.info('Registering new user: %s' % message.from_user.id)
        splitted = message.text.split(maxsplit=2)
        if len(splitted) > 2:
            username = splitted[1]
            if len(splitted) == 3:
                pw = splitted[2]
            else:
                pw = None
        else:
            username = message.from_user.username or message.from_user.id
            pw = None
        async with self.app['db'].acquire() as conn:
            users = await pakreq.db.get_users(conn)
            for user in users:
                if pakreq.db.OAuthInfo(string=user['oauth_info'])\
                        .info['telegram_id'] == message.from_user.id:
                    await message.reply(
                        pakreq.telegram_consts.ALREADY_REGISTERED,
                        parse_mode='HTML'
                    )
                    return
                if user['username'] == username:
                    await message.reply(
                        pakreq.telegram_consts.USERNAME_ALREADY_TAKEN.format(
                            username=escape(username)
                        ),
                        parse_mode='HTML'
                    )
                    return
            oauth_info = pakreq.db.OAuthInfo(telegram_id=message.from_user.id)
            id = await pakreq.db.get_max_user_id(conn)
            id += 1
            if pw is not None:
                pw = password_hash(id, pw, self.app['config']['salt'])
            try:
                await pakreq.db.new_user(
                    conn, id=id, username=username,
                    oauth_info=oauth_info, password_hash=pw
                )
                await message.reply(
                    pakreq.telegram_consts.REGISGER_SUCCESS.format(
                        username=escape(username)
                    ),
                    parse_mode='HTML'
                )
                if pw is None:
                    message.reply(
                        pakreq.telegram_consts.PASSWORD_EMPTY,
                        parse_mode='HTML'
                    )
            except Exception:
                await message.reply(
                    pakreq.telegram_consts.error_msg(
                        'Unable to register'
                    ),
                    parse_mode='HTML'
                )

    async def link_account(self, message: types.Message):
        """Implementation of /link, link telegram account to pakreq account"""
        logger.info(
            'Received request to link telegram account: %s' %
            message.from_user.id
        )
        splitted = message.text.split(maxsplit=2)
        if len(splitted) < 3:
            await message.reply(
                pakreq.telegram_consts.TOO_FEW_ARGUMENTS,
                parse_mode='HTML'
            )
            return
        success = False
        async with self.app['db'].acquire() as conn:
            users = await pakreq.db.get_users(conn)
            for user in users:
                if user['username'] == splitted[1]:
                    pw = password_hash(
                        user['id'],
                        splitted[2],
                        self.app['config']['salt']
                    )
                    if user['password_hash'] == pw:
                        oauth_info = pakreq.db.OAuthInfo(
                            string=user['oauth_info']
                        ).edit(
                            telegram_id=message.from_user.id
                        ).output()
                        try:
                            await pakreq.db.update_user(
                                conn, user['id'], oauth_info=oauth_info
                            )
                            success = True
                        except Exception:
                            await message.reply(
                                pakreq.telegram_consts.error_msg(
                                    "Unable to update user info"
                                ),
                                parse_mode='HTML'
                            )
                        break
            if success:
                # Unlink this Telegram account from other pakreq accounts
                # TODO: Make this more elegant
                for user in users:
                    if user['username'] != splitted[1]:
                        if pakreq.db.OAuthInfo(string=user['oauth_info'])\
                                .info['telegram_id'] == message.from_user.id:
                            oauth_info = pakreq.db.OAuthInfo(
                                string=user['oauth_info']
                            ).edit(
                                telegram_id=None
                            ).output()
                            try:
                                await pakreq.db.update_user(
                                    conn,
                                    user['id'],
                                    oauth_info=oauth_info
                                )
                            except Exception:
                                await message.reply(
                                    pakreq.telegram_consts.error_msg(
                                        "Unable to update user info",
                                        "Failed to unlink other accounts."
                                    ),
                                    parse_mode='HTML'
                                )
                await message.reply(
                    pakreq.telegram_consts.LINK_SUCCESS.format(
                        username=splitted[1]
                    ),
                    parse_mode='HTML'
                )
            else:
                await message.reply(
                    pakreq.telegram_consts.INCORRECT_CREDENTIALS,
                    parse_mode='HTML'
                )

    async def set_password(self, message: types.Message):
        """Implementation of /passwd, set password for user"""
        logger.info(
            'Setting new password for Telegram user: %s' % message.from_user.id
        )
        splitted = message.text.split(maxsplit=1)
        if len(splitted) == 2:
            async with self.app['db'].acquire() as conn:
                users = await pakreq.db.get_users(conn)
                user_id = find_user(users, message.from_user.id)
                if user_id is not None:
                    pw = password_hash(
                        user_id,
                        splitted[1],
                        self.app['config']['salt']
                    )
                    try:
                        await pakreq.db.update_user(
                            conn, user_id,
                            password_hash=pw
                        )
                    except Exception:
                        await message.reply(
                            pakreq.telegram_consts.error_msg(
                                "Unable to set password"
                            )
                        )
                    await message.reply(
                        pakreq.telegram_consts.PASSWORD_UPDATE_SUCCESS,
                        parse_mode='HTML'
                    )
                    return
                else:
                    await message.reply(
                        pakreq.telegram_consts.REGISTER_FIRST,
                        parse_mode='HTML'
                    )
        else:
            await message.reply(
                pakreq.telegram_consts.TOO_FEW_ARGUMENTS,
                parse_mode='HTML'
            )

    async def list_requests(self, message: types.Message):
        """Implementation of /list, list requests"""
        logger.info('Received /list: %s' % message.text)
        splitted = message.text.split()
        result = ''
        if len(splitted) == 1:
            if message.chat.id < 0:
                await message.reply(
                    pakreq.telegram_consts.FULL_LIST_PRIVATE_ONLY,
                    parse_mode='HTML'
                )
                return
            async with self.app['db'].acquire() as conn:
                requests = await pakreq.db.get_requests(conn)
            count = 0
            for request in requests:
                if count < 10:
                    if request['status'] == pakreq.db.RequestStatus.OPEN:
                        result = result +\
                            pakreq.telegram_consts.REQUEST_BRIEF_INFO.format(
                                id=request['id'], name=escape(request['name']),
                                rtype=get_type(request['type']),
                                description=escape(request['description'])
                            )
                        count += 1
                else:
                    break
            if count >= 10:
                result += pakreq.telegram_consts.FULL_LIST.format(
                    url=self.app['config']['base_url']
                )
            if result == '':
                result = pakreq.telegram_consts.NO_PENDING_REQUESTS
        elif len(splitted) <= 6:
            async with self.app['db'].acquire() as conn:
                for id in splitted[1:]:
                    try:
                        request = await pakreq.db.get_request_detail(
                            conn, int(id)
                        )
                        result += pakreq.telegram_consts.REQUEST_DETAIL.format(
                            name=escape(request['name']),
                            id=request['id'],
                            status=get_status(request['status']),
                            rtype=get_type(request['type']),
                            desc=escape(request['description']),
                            req_name=escape(request['requester']['username']),
                            req_id=request['requester']['id'],
                            pak_name=escape(request['packager']['username']),
                            pak_id=request['packager']['id'],
                            date=request['pub_date'].isoformat(),
                            eta=(request['note'] or 'Empty'))
                    except (pakreq.db.RecordNotFoundException, ValueError):
                        result +=\
                            pakreq.telegram_consts.REQUEST_NOT_FOUND.format(
                                id=id
                            )
        else:
            result = pakreq.telegram_consts.TOO_MANY_ARUGMENTS
        await message.reply(result, parse_mode='HTML')

    # TODO: Simplify the next two functions
    async def set_note(self, message: types.Message):
        splitted = message.text.split(maxsplit=2)
        note = None
        if len(splitted) == 3:
            note = splitted[2]
        async with self.app['db'].acquire() as conn:
            users = await pakreq.db.get_users(conn)
            user_id = find_user(users, message.from_user.id)
            if user_id is None:
                await message.reply(
                    pakreq.telegram_consts.REGISTER_FIRST,
                    parse_mode='HTML'
                )
                return
            try:
                request = await pakreq.db.get_request(conn, int(splitted[1]))
                if request['packager_id'] != user_id:
                    await message.reply(
                        pakreq.telegram_consts.CLAIM_FIRST.format(
                            id=int(splitted[1])
                        ),
                        parse_mode='HTML'
                    )
                await pakreq.db.update_request(
                    conn, int(splitted[1]), note=note
                )
                await message.reply(
                    pakreq.telegram_consts.PROCESS_SUCCESS.format(
                        id=splitted[1]
                    )
                )
            except (pakreq.db.RecordNotFoundException, ValueError):
                await message.reply(
                    pakreq.telegram_consts.REQUEST_NOT_FOUND.format(
                        id=splitted[1]
                    )
                )
            except Exception:
                await message.reply(
                    pakreq.telegram_consts.error_msg(
                        'Unable to edit request'
                    ),
                    parse_mode='HTML'
                )

    async def edit_desc(self, message: types.Message):
        splitted = message.text.split(maxsplit=2)
        desc = None
        if len(splitted) == 3:
            desc = splitted[2]
        async with self.app['db'].acquire() as conn:
            users = await pakreq.db.get_users(conn)
            user_id = find_user(users, message.from_user.id)
            if user_id is None:
                await message.reply(
                    pakreq.telegram_consts.REGISTER_FIRST,
                    parse_mode='HTML'
                )
                return
            try:
                request = await pakreq.db.get_request(conn, int(splitted[1]))
                if request['requester_id'] != user_id:
                    await message.reply(
                        pakreq.telegram_consts.ONLY_REQUESTER_CAN_EDIT.format(
                            id=int(splitted[1])
                        ),
                        parse_mode='HTML'
                    )
                await pakreq.db.update_request(
                    conn, int(splitted[1]), description=desc
                )
                await message.reply(
                    pakreq.telegram_consts.PROCESS_SUCCESS.format(
                        id=splitted[1]
                    )
                )
            except (pakreq.db.RecordNotFoundException, ValueError):
                await message.reply(
                    pakreq.telegram_consts.REQUEST_NOT_FOUND.format(
                        id=splitted[1]
                    )
                )
            except Exception:
                await message.reply(
                    pakreq.telegram_consts.error_msg(
                        'Unable to edit request'
                    ),
                    parse_mode='HTML'
                )

    async def set_status(self, message: types.Message):
        def handle_request(command):
            return {
                '/done': pakreq.db.RequestStatus.DONE,
                '/reject': pakreq.db.RequestStatus.REJECTED
            }.get(command, -1)  # There should be only 2 types of requests
        splitted = message.text.split()
        logger.info(
            'Received request to mark request(s) as %sed: %s' %
            (splitted[0][1:], message.text)
        )
        result = ''
        rtype = handle_request(splitted[0])
        if rtype == -1:
            logging.error('Unexpected request type: %s' % splitted[0])
            await message.reply(pakreq.telegram_consts.error_msg(
                'Unknown command'
            ))
            return
        async with self.app['db'].acquire() as conn:
            users = await pakreq.db.get_users(conn)
            user_id = find_user(users, message.from_user.id)
            if user_id is None:
                await message.reply(
                    pakreq.telegram_consts.REGISTER_FIRST,
                    parse_mode='HTML'
                )
                return
            for id in splitted[1:]:
                try:
                    request = await pakreq.db.get_request(conn, int(id))
                    if (splitted[0] == '/done') and\
                            (request['packager_id'] != user_id):
                        result +=\
                            pakreq.telegram_consts.CLAIM_FIRST.format(
                                id=id
                            )
                        continue
                    await pakreq.db.update_request(conn, int(id), status=rtype)
                    result += pakreq.telegram_consts.PROCESS_SUCCESS.format(
                        id=id
                    )
                except (pakreq.db.RecordNotFoundException, ValueError):
                    result += pakreq.telegram_consts.REQUEST_NOT_FOUND.format(
                        id=id
                    )
        await message.reply(result, parse_mode='HTML')

    def start(self):
        """Register message handlers, and start the bot"""
        commands_mapping = [
            (['ping'], self.ping),
            (['list'], self.list_requests),
            (['register'], self.register),
            (['link'], self.link_account),
            (['passwd'], self.set_password),
            (['help'], self.show_help),
            (['note'], self.set_note),
            (['edit_desc'], self.edit_desc),
            (['done', 'reject'], self.set_status),
            (['claim', 'unclaim'], self.claim_request),
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
