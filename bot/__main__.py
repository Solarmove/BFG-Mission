import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.base import DefaultKeyBuilder
from aiogram.fsm.storage.redis import RedisEventIsolation, RedisStorage
from aiogram_dialog import setup_dialogs
from aiogram_i18n.cores import FluentRuntimeCore

from bot.dialogs import dialog_routers
from bot.db.base import create_all
from bot.db.redis import redis
from bot.handlers import routers_list
from bot.middleware.db import DbSessionMiddleware
from bot.middleware.i18n_dialog import RedisI18nMiddleware
from bot.utils.i18n_utils.i18n_format import make_i18n_middleware
from bot.utils.set_bot_commands import set_default_commands
from configreader import config

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
path_to_locales = os.path.join("bot", 'src', "locales", "{locale}", "LC_MESSAGES")
core = FluentRuntimeCore(path=path_to_locales)
i18n_middleware = RedisI18nMiddleware(
    core=core,
    redis=redis,
)
i18n_dialog_middleware = make_i18n_middleware(path_to_locales)


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await set_default_commands(bot)
    dp.update.middleware(DbSessionMiddleware())
    router.include_routers(*routers_list)
    router.include_routers(*dialog_routers)
    bg_manager = setup_dialogs(dp)
    dp.include_router(router)
    await create_all()
    await dp.start_polling(
        bot, allowed_updates=[
            "message", "callback_query", "chat_member", "chat_member_updated",
            'my_chat_member', 'chat_join_request']
    )


if __name__ == "__main__":
    asyncio.run(main())
