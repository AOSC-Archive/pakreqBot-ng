# telegram.py

import logging

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor

logger = logging.getLogger(__name__)

async def ping(message: types.Message):
    logger.info("Received /ping: {}".format(message.text))
    await message.reply("pong")

def start_bot(config):
    bot = Bot(token=config['telegram']['token'])
    dp = Dispatcher(bot)
    dp.register_message_handler(ping, commands=['ping'])
    executor.start_polling(dp)