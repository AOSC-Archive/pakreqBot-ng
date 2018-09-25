# telegram.py

import asyncio
import logging

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor

import pakreq.db

from pakreq.utils import get_type

logger = logging.getLogger(__name__)

class pakreqBot():
    def __init__(self, config):
        self.app = dict()
        self.app['config'] = config
        self.bot = Bot(token=self.app['config']['telegram']['token'])
        self.dp = Dispatcher(self.bot)

    async def init_db(self):
        await pakreq.db.init_db(self.app)

    async def ping(self, message: types.Message):
        logger.info('Received /ping: {}'.format(message.text))
        await message.reply('pong')

    async def list_requests(self, message: types.Message):
        logger.info('Received /list: {}'.format(message.text))
        splitted = message.text.split()
        result = ''
        if len(splitted) == 1:
            if message.chat.id < 0:
                await message.reply('Listing all requests is only allowed in private chat')
                return
            async with self.app['db'].acquire() as conn:
                requests = await pakreq.db.get_requests(conn)
            count = 0
            for request in requests:
                if count <= 10:
                    result = result + 'ID: ' + str(request['id']) + ' <b>' + str(request['name']) + '</b> (' + str(get_type(request['type'])) + '): ' + str(request['description']) + '\n'
                    count += 1
                else:
                    break
            if count > 10:
                result = result + '\nPlease visit ' + self.app['config']['base_url'] + ' for the complete listing'
        elif (len(splitted) > 1) and (len(splitted) <= 5):
            for id in splitted[1:]:
                async with self.app['db'].acquire() as conn:
                    try:
                        request = await pakreq.db.get_request_detail(conn, id)
                        result = result + '<b>' + str(request['name']) + '</b>:\n'
                        result = result + '  <b>Type</b>: ' + str(get_type(request['type'])) + '\n'
                        result = result + '  <b>Description</b>: ' + str(request['description']) + '\n'
                        result = result + '  <b>Requester</b>: ' + str(request['requester']['username']) + '(' + str(request['requester']['id']) + ')' + '\n'
                        result = result + '  <b>Packager</b>: ' + str(request['packager']['username']) + '(' + str(request['packager']['id']) + ')' + '\n'
                        result = result + '  <b>Pub date</b>: ' + str(request['pub_date'].isoformat()) + '\n'
                        result = result + '  <b>ETA</b>: ' + str(request['eta'] or 'Unset') + '\n'
                        result = result + '\n'
                    except:
                        result = result + '<b>Request ID ' + id + ' not found.</b>' + '\n'
        else:
            result = 'Too many arugments'
        if result == '':
            result = "No pending requests"
        await message.reply(result, parse_mode='HTML')

    def start(self):
        self.dp.register_message_handler(self.ping, commands=['ping'])
        self.dp.register_message_handler(self.list_requests, commands=['list'])
        executor.start_polling(self.dp)

def start_bot(config):
    bot = pakreqBot(config)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(bot.init_db())
    bot.start()