import asyncio
import logging

from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.base import DefaultKeyBuilder
from aiogram.fsm.storage.redis import RedisEventIsolation, RedisStorage
from aiogram_dialog import setup_dialogs
from aiogram_i18n.cores import FluentRuntimeCore
from arq import create_pool
from langchain_openai import ChatOpenAI

from bot.dialogs import dialog_routers
from bot.db.base import create_all
from bot.db.redis import redis
from bot.handlers import routers_list
from bot.i18n.utils.i18n_format import make_i18n_middleware
from bot.middleware.db import DbSessionMiddleware
from bot.middleware.i18n_dialog import RedisI18nMiddleware
from bot.middleware.log_middleware import LogMiddleware
from bot.services.startup import on_startup

from bot.utils.set_bot_commands import set_default_commands
from configreader import config, RedisConfig


# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s (%(asctime)s) (Line: %(lineno)d) [%(filename)s] : %(message)s ",
    datefmt="%d/%m/%Y %I:%M:%S",
    encoding="utf-8",
    filemode="w",
)
logger = logging.getLogger(__name__)


# Bot settings
bot = Bot(
    token=config.bot_config.token,
    default=DefaultBotProperties(
        parse_mode=config.bot_config.parse_mode,
    ),
)
key_builder = DefaultKeyBuilder(with_destiny=True, with_bot_id=True)
storage = RedisStorage(redis=redis, key_builder=key_builder)
event_isolation = RedisEventIsolation(redis, key_builder=key_builder)
dp = Dispatcher(storage=storage, events_isolation=event_isolation)
router = Router(name=__name__)

# I18n Settings
core = FluentRuntimeCore(path=config.path_to_locales)
i18n_middleware = RedisI18nMiddleware(core=core, redis=redis)
i18n_dialog_middleware = make_i18n_middleware(config.path_to_locales)

llm = ChatOpenAI(
    # model="gpt-3.5-turbo",
    model="gpt-4.1-2025-04-14",
    temperature=0.1,
    max_tokens=1000,
    api_key=config.openai_api_key,
    max_retries=3,
    streaming=True
)


def include_middlewares():
    dp.update.middleware(i18n_middleware)
    dp.update.middleware(i18n_dialog_middleware)
    dp.update.middleware(RedisI18nMiddleware(core=core, redis=redis))
    dp.update.middleware(DbSessionMiddleware())
    dp.update.middleware(LogMiddleware())


async def main():
    redis_pool = await create_pool(RedisConfig.pool_settings)

    await bot.delete_webhook(drop_pending_updates=True)
    await set_default_commands(bot)
    include_middlewares()
    await core.startup()
    router.include_routers(*routers_list)
    router.include_routers(*dialog_routers)
    setup_dialogs(dp)
    dp.include_router(router)
    dp["redis"] = redis
    dp["arq"] = redis_pool
    dp["llm"] = llm
    await create_all()
    await on_startup()
    await dp.start_polling(bot, allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    asyncio.run(main())
