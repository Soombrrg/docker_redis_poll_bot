import asyncio
import logging

from aiogram import Dispatcher, Bot
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis

from config.config import load_config
from handlers.handler import register_handlers

logger = logging.getLogger(__name__)


async def main():
    logging.basicConfig(level=logging.INFO)

    config = load_config()

    redis = Redis(host="redis", port=6379, db=0)
    storage = RedisStorage(redis=redis)

    bot = Bot(config.tg_bot.token)
    dp = Dispatcher(storage=storage)

    register_handlers(dp)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
