# telegram.py

"""
Telegram bot
"""

import asyncio
import logging

from aiogram import Bot, types
from aiogram.utils import executor
from aiogram.dispatcher import Dispatcher

import pakreq.db
import pakreq.pakreq
import pakreq.telegram_consts

from pakreq.utils import get_type, get_status, password_hash, password_verify, escape
from pakreq.db import OAuthType

logger = logging.getLogger(__name__)


class PakreqBot(object):
    """pakreqBot main object"""

    def __init__(self, config):
        self.app = dict()
        self.app['config'] = config
        self.bot = Bot(token=self.app['config']['telegram']['token'])
        self.dp = Dispatcher(self.bot)

    async def init_db(self):
        """Init database connection"""
        await pakreq.db.init_db(self.app)

    # Helper functions
    @staticmethod
    async def check_arguments(message, splitted, condition, notification):
        if condition(len(splitted)):
            logger.info('Invalid request received')
            await message.reply(
                notification, parse_mode='HTML'
            )
            return False
        return True

    # Command handler
    async def link_account(self, message: types.Message):
        """Implementation of /link, link telegram account to pakreq account"""
        async def reply_invalid_cred():
            await message.reply(
                pakreq.telegram_consts.INCORRECT_CREDENTIALS,
                parse_mode='HTML'
            )

        logger.info(
            'Received request to link telegram account: %s' %
            message.from_user.id
        )
        splitted = message.text.split(maxsplit=2)
        if not await self.check_arguments(
                message, splitted, lambda x: x < 3,
                pakreq.telegram_consts.TOO_FEW_ARGUMENTS
        ):
            return
        async with self.app['db'].acquire() as conn:
            user = await pakreq.pakreq.get_user_by_name(conn, splitted[1])
            if not user:
                await reply_invalid_cred()
                return
            if not password_verify(
                    user['id'], splitted[2], user['password_hash']):
                await reply_invalid_cred()
                return

            # Unlink this Telegram account from other pakreq accounts
            try:
                await pakreq.pakreq.delete_oauth(conn, OAuthType.Telegram,
                                                 message.from_user.id)
            except Exception:
                await message.reply(
                    pakreq.telegram_consts.error_msg(
                        "Unable to update user info",
                        "Failed to unlink other accounts."
                    ),
                    parse_mode='HTML'
                )

            # insert new information to the table
            try:
                await pakreq.pakreq.new_oauth_from_user_id(
                    conn, user['id'], OAuthType.Telegram,
                    oid=message.from_user.id
                )
            except Exception as ex:
                await message.reply(
                    pakreq.telegram_consts.error_msg(
                        "Unable to update user info", ex
                    ),
                    parse_mode='HTML'
                )
            await message.reply(
                pakreq.telegram_consts.LINK_SUCCESS.format(
                    username=splitted[1]
                ),
                parse_mode='HTML'
            )

    async def unlink_account(self, message: types.Message):
        """Implementation of /unlink"""
        logger.info(
            'Received request to unlink telegram account: %s' %
            message.from_user.id
        )
        async with self.app['db'].acquire() as conn:
            if not await \
                pakreq.pakreq.get_user_from_oauth_id(conn,
                                                     OAuthType.Telegram,
                                                     message.from_user.id):
                await message.reply(
                                pakreq.telegram_consts.UNLINK_NOTHING_TO_UNLINK
                                )
                return
            # Unlink this Telegram account from other pakreq accounts
            try:
                await pakreq.pakreq.delete_oauth(conn, OAuthType.Telegram,
                                                 message.from_user.id)
                await message.reply(pakreq.telegram_consts.UNLINK_SUCCESS)
            except Exception:
                await message.reply(
                    pakreq.telegram_consts.error_msg(
                        "Unable to update user info",
                        "Failed to unlink accounts."
                    ),
                    parse_mode='HTML'
                )

    async def list_requests(self, message: types.Message):
        """Implementation of /list, list requests"""
        logger.info('Received request to list requests: %s' % message.text)
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
                requests = await pakreq.pakreq.get_open_requests(conn)
            for request in requests[:10]:
                if request['status'] == pakreq.db.RequestStatus.OPEN:
                    result = result + \
                        pakreq.telegram_consts.REQUEST_BRIEF_INFO.format(
                            id=request['id'], name=escape(
                                request['name']),
                            rtype=get_type(request['type']),
                            description=escape(request['description'])
                        )
            if len(requests) >= 10:
                result += pakreq.telegram_consts.FULL_LIST.format(
                    url=self.app['config']['base_url']
                )
            if result == '':
                result = pakreq.telegram_consts.NO_PENDING_REQUESTS
        elif len(splitted) <= 6:
            async with self.app['db'].acquire() as conn:
                for id in splitted[1:]:
                    try:
                        request = await pakreq.pakreq.get_request_detail(
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
                        result += \
                            pakreq.telegram_consts.REQUEST_NOT_FOUND.format(
                                id=id
                            )
        else:
            result = pakreq.telegram_consts.TOO_MANY_ARUGMENTS
        await message.reply(result, parse_mode='HTML')

    # TODO: Simplify set_note and edit_desc
    async def set_note(self, message: types.Message):
        """Implementation of /note, set note for a request"""
        logger.info('Received request to set note: %s' % message.text)
        splitted = message.text.split(maxsplit=2)
        if not await self.check_arguments(
                message, splitted, lambda x: x < 2,
                pakreq.telegram_consts.TOO_FEW_ARGUMENTS
        ):
            return
        note = None
        if len(splitted) == 3:
            note = splitted[2]
        async with self.app['db'].acquire() as conn:
            user = await pakreq.pakreq.get_user_from_oauth_id(
                conn, OAuthType.Telegram, message.from_user.id)
            user_id = user['id']
            if user_id is None:
                await message.reply(
                    pakreq.telegram_consts.REGISTER_FIRST,
                    parse_mode='HTML'
                )
                return
            try:
                request = await pakreq.pakreq.get_request(conn, int(splitted[1]))
                if request['packager_id'] != user_id:
                    await message.reply(
                        pakreq.telegram_consts.CLAIM_FIRST.format(
                            id=int(splitted[1])
                        ),
                        parse_mode='HTML'
                    )
                    return
                await pakreq.pakreq.update_request(
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

    @staticmethod
    async def ping(message: types.Message):
        """Implementation of /ping, pong"""
        logger.info(
            'Received ping from Telegram user: %s' % message.from_user.id
        )
        await message.reply('<b>Pong</b>', parse_mode='HTML')

    async def set_password(self, message: types.Message):
        """Implementation of /passwd, set password for user"""
        logger.info(
            'Setting new password for Telegram user: %s' % message.from_user.id
        )
        splitted = message.text.split(maxsplit=1)
        if not await self.check_arguments(
                message, splitted, lambda x: x < 2,
                pakreq.telegram_consts.TOO_FEW_ARGUMENTS
        ):
            return
        async with self.app['db'].acquire() as conn:
            user = await pakreq.pakreq.get_user_from_oauth_id(
                conn, OAuthType.Telegram, message.from_user.id)
            user_id = user['id']
            if user_id is not None:
                pw = password_hash(
                    user_id,
                    splitted[1]
                )
                try:
                    await pakreq.pakreq.update_user(
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

    async def search_requests(self, message: types.Message):
        """Implementation of /search, search requests"""
        logger.info('Received request to search requrest: %s' % message.text)
        splitted = message.text.split(maxsplit=1)
        if not await self.check_arguments(
                message, splitted, lambda x: x != 2,
                pakreq.telegram_consts.INVALID_REQUEST
        ):
            return
        async with self.app['db'].acquire() as conn:
            requests = await pakreq.pakreq.search_requests(conn, splitted[1])
        results = ''
        for request in requests:
            results += pakreq.telegram_consts.REQUEST_BRIEF_INFO.format(
                id=request['id'], name=escape(request['name']),
                rtype=get_type(request['type']),
                description=escape(request['description']).replace(
                    escape(splitted[1]), '<b>%s</b>' % escape(splitted[1])
                )
            )
        results = results or \
            pakreq.telegram_consts.NO_MATCH_FOUND.format(keyword=splitted[1])
        await message.reply(
            pakreq.telegram_consts.SEARCH_RESULT.format(
                matches=results
            ),
            parse_mode='HTML'
        )

    async def whoami(self, message: types.Message):
        """Implementation of /whoami, get user info"""
        logger.info('Received request to show who that is: %s' % message.text)
        async with self.app['db'].acquire() as conn:
            user = await pakreq.pakreq.get_user_from_oauth_id(
                conn, OAuthType.Telegram, message.from_user.id)
        if user:
            await message.reply(
                pakreq.telegram_consts.WHOAMI.format(
                    username=user['username'],
                    id=user['id']
                ),
                parse_mode='HTML'
            )
        else:
            await message.reply(
                pakreq.telegram_consts.REGISTER_FIRST,
                parse_mode='HTML'
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
            users = await pakreq.pakreq.get_users(conn)
            for user in users:
                if await pakreq.pakreq.get_oauth_from_oid(
                        conn, OAuthType.Telegram, message.from_user.id):
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

            user_id = await pakreq.pakreq.get_max_user_id(conn)
            user_id += 1
            if pw is not None:
                pw = password_hash(user_id, pw)
            try:
                await pakreq.pakreq.new_user(
                    conn, username=username,
                    password_hash=pw
                )
                await pakreq.pakreq.new_oauth_from_user_id(
                    conn, uid=user_id, type=OAuthType.Telegram,
                    oid=message.from_user.id
                )
                await message.reply(
                    pakreq.telegram_consts.REGISGER_SUCCESS.format(
                        username=escape(username)
                    ),
                    parse_mode='HTML'
                )
                if pw is None:
                    await message.reply(
                        pakreq.telegram_consts.PASSWORD_EMPTY,
                        parse_mode='HTML'
                    )
            except Exception as e:
                await message.reply(
                    pakreq.telegram_consts.error_msg(
                        'Unable to register', e
                    ),
                    parse_mode='HTML'
                )

    async def edit_desc(self, message: types.Message):
        """Implementation of /edit_desc, edit description"""
        logger.info('Received request to edit description: %s' % message.text)
        splitted = message.text.split(maxsplit=2)
        if not await self.check_arguments(
                message, splitted, lambda x: x < 2,
                pakreq.telegram_consts.TOO_FEW_ARGUMENTS
        ):
            return
        desc = None
        if len(splitted) == 3:
            desc = splitted[2]
        async with self.app['db'].acquire() as conn:
            user = await pakreq.pakreq.get_user_from_oauth_id(
                conn, OAuthType.Telegram, message.from_user.id)
            user_id = user['id']
            if user_id is None:
                await message.reply(
                    pakreq.telegram_consts.REGISTER_FIRST,
                    parse_mode='HTML'
                )
                return
            try:
                request = await pakreq.pakreq.get_request(conn, int(splitted[1]))
                if request['requester_id'] != user_id:
                    await message.reply(
                        pakreq.telegram_consts.ONLY_REQUESTER_CAN_EDIT.format(
                            id=int(splitted[1])
                        ),
                        parse_mode='HTML'
                    )
                await pakreq.pakreq.update_request(
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

    async def claim_request(self, message: types.Message):
        """Implementation of /claim and /unclaim, claim/unclaim request"""
        logger.info(
            'Received request to claim or unclaim request(s): %s' %
            message.text
        )
        splitted = message.text.split()
        if splitted[0].startswith('/claim'):
            claim = True
        else:
            claim = False
        result = ''
        ids = None
        async with self.app['db'].acquire() as conn:
            if len(splitted) < 2:
                requests = await pakreq.pakreq.get_open_requests(conn)
                for request in requests:
                    if (request['packager_id'] == 0):
                        ids = [request['id']]
                        break
                if ids is None:
                    await message.reply(
                        pakreq.telegram_consts.NO_PENDING_REQUESTS,
                        parse_mode='HTML'
                    )
                    return
            else:
                ids = splitted[1:]
            user = await pakreq.pakreq.get_user_from_oauth_id(
                conn, OAuthType.Telegram, message.from_user.id)
            user_id = user['id']
            if user_id is None:
                await message.reply(
                    pakreq.telegram_consts.REGISTER_FIRST,
                    parse_mode='HTML'
                )
                return
            for request_id in ids:
                new_user_id = user_id
                try:
                    request = await pakreq.pakreq.get_request(conn, int(request_id))
                    if not claim:
                        if user_id != request['packager_id']:
                            result += pakreq.telegram_consts.CLAIM_FIRST \
                                .format(
                                    id=id
                                )
                            continue
                        else:
                            new_user_id = None
                    await pakreq.pakreq.update_request(
                        conn, int(request_id),
                        packager_id=new_user_id
                    )
                    result += pakreq.telegram_consts.ACTION_SUCCESSFUL.format(
                        action=splitted[0].split('@')[0][1:],
                        id=request_id
                    )
                except (pakreq.db.RecordNotFoundException, ValueError):
                    result += pakreq.telegram_consts.REQUEST_NOT_FOUND.format(
                        id=request_id
                    )
        await message.reply(
            result, parse_mode='HTML'
        )

    async def show_help(self, message: types.Message):
        """Implementation of /help, show help message"""
        logger.info('Received request to show help: %s' % message.text)
        await message.reply(
            pakreq.telegram_consts.HELP_CRUFT, parse_mode='HTML')

    async def set_status(self, message: types.Message):
        """Implementation of /done and /reject, set status for requests."""
        def handle_request(command):
            if command.startswith('/done'):
                return pakreq.db.RequestStatus.DONE
            elif command.startswith('/reject'):
                return pakreq.db.RequestStatus.REJECTED
            elif command.startswith('/reopen'):
                return pakreq.db.RequestStatus.OPEN
            else:
                return int(-1)  # There should be only 2 types of requests
        splitted = message.text.split()
        logger.info(
            'Received request to mark request(s) as %sed: %s' %
            (splitted[0][1:], message.text)
        )
        if not await self.check_arguments(
                message, splitted, lambda x: x < 2,
                pakreq.telegram_consts.TOO_FEW_ARGUMENTS
        ):
            return
        result = ''
        rtype = handle_request(splitted[0])
        if rtype == -1:
            logging.error('Unexpected request type: %s' % splitted[0])
            await message.reply(pakreq.telegram_consts.error_msg(
                'Unknown command'
            ))
            return
        async with self.app['db'].acquire() as conn:
            user = await pakreq.pakreq.get_user_from_oauth_id(
                conn, OAuthType.Telegram, message.from_user.id)
            user_id = user['id']
            if user_id is None:
                await message.reply(
                    pakreq.telegram_consts.REGISTER_FIRST,
                    parse_mode='HTML'
                )
                return
            for id in splitted[1:]:
                try:
                    request = await pakreq.pakreq.get_request(conn, int(id))
                    if (rtype == pakreq.db.RequestStatus.REJECTED) or \
                            (rtype == pakreq.db.RequestStatus.DONE):
                        packager_id = user_id
                        if (request['status'] == pakreq.db.RequestStatus.DONE) or \
                                (request['status'] == pakreq.db.RequestStatus.REJECTED):
                            result += \
                                pakreq.telegram_consts.REOPEN_FIRST.format(
                                    id=id
                                )
                            continue
                    else:
                        packager_id = request['packager_id']
                    await pakreq.pakreq.update_request(
                        conn, int(id), status=rtype, packager_id=packager_id
                    )
                    result += pakreq.telegram_consts.PROCESS_SUCCESS.format(
                        id=id
                    )
                except (pakreq.db.RecordNotFoundException, ValueError):
                    result += pakreq.telegram_consts.REQUEST_NOT_FOUND.format(
                        id=id
                    )
        await message.reply(result, parse_mode='HTML')

    async def new_request(self, message: types.Message):
        """Implementation of /pakreq, /updreq, /optreq, add new request"""
        def handle_request(command):
            if command.startswith('/pakreq'):
                return pakreq.db.RequestType.PAKREQ
            elif command.startswith('/updreq'):
                return pakreq.db.RequestType.UPDREQ
            elif command.startswith('/optreq'):
                return pakreq.db.RequestType.OPTREQ
            else:
                return int(-1)  # There should be only 3 types of requests
        logger.info('Received request to add a new request: %s' % message.text)
        splitted = message.text.split(maxsplit=2)
        if not await self.check_arguments(
                message, splitted, lambda x: x < 2,
                pakreq.telegram_consts.TOO_FEW_ARGUMENTS
        ):
            return
        logger.info('Adding new request: %s' % splitted[1])
        description = 'N/A'
        if len(splitted) == 3:
            description = splitted[2]
        rtype = handle_request(splitted[0])
        if rtype == -1:
            logging.error('Unexpected request type: %s' % splitted[0])
            await message.reply(
                pakreq.telegram_consts.error_msg(
                    'Unexpected request type',
                    detail=splitted[0]
                ),
                parse_mode='HTML'
            )
            return
        async with self.app['db'].acquire() as conn:
            user = await pakreq.pakreq.get_user_from_oauth_id(
                conn, OAuthType.Telegram, message.from_user.id)
            if user is None:
                await message.reply(
                    pakreq.telegram_consts.REGISTER_FIRST,
                    parse_mode='HTML'
                )
                return
            user_id = user['id']
            requests = await pakreq.pakreq.get_open_requests(conn)
            for request in requests:
                if (request['name'] == splitted[1]) and\
                        (request['type'] == rtype):
                    await message.reply(
                        pakreq.telegram_consts.IS_ALREADY_IN_THE_LIST
                        .format(
                            rtype=escape(splitted[0].split(
                                '@')[0][1:].capitalize()),
                            name=escape(str(splitted[1]))
                        ),
                        parse_mode='HTML'
                    )
                    return
            id = await pakreq.pakreq.get_max_request_id(conn) + 1
            await pakreq.pakreq.new_request(
                conn, id=id, rtype=rtype,
                name=splitted[1],
                description=description,
                requester_id=user_id
            )
        await message.reply(
            pakreq.telegram_consts.SUCCESSFULLY_ADDED.format(
                rtype=escape(splitted[0].split('@')[0][1:]),
                name=escape(str(splitted[1])),
                id=str(id)
            )
        )

    def start(self):
        """Register message handlers, and start the bot"""
        commands_mapping = [
            (['link'], self.link_account),
            (['list'], self.list_requests),
            (['note'], self.set_note),
            (['ping'], self.ping),
            (['passwd'], self.set_password),
            (['search'], self.search_requests),
            (['whoami'], self.whoami),
            (['register'], self.register),
            (['edit_desc'], self.edit_desc),
            (['claim', 'unclaim'], self.claim_request),
            (['start', 'help'], self.show_help),
            (['done', 'reject', 'reopen'], self.set_status),
            (['pakreq', 'updreq', 'optreq'], self.new_request),
            (['unlink'], self.unlink_account)
        ]
        for command in commands_mapping:
            logging.info('Registering command: %s' % command[0])
            self.dp.register_message_handler(command[1], commands=command[0])
        executor.start_polling(self.dp)


def start_bot(config):
    """Start the bot"""
    bot = PakreqBot(config)
    # TODO: Make this more elegant
    loop = asyncio.get_event_loop()
    loop.run_until_complete(bot.init_db())
    bot.start()
