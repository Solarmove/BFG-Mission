import logging

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram_i18n.cores import FluentRuntimeCore
from arq import cron

from bot.utils.unitofwork import UnitOfWork
from configreader import config, RedisConfig
from scheduler.func import send_notification, create_task_from_regular

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s (%(asctime)s) (Line: %(lineno)d) [%(filename)s] : %(message)s ",
    datefmt="%d/%m/%Y %I:%M:%S",
    encoding="utf-8",
    filemode="w",
)

logger = logging.getLogger(__name__)


async def startup(ctx):
    ctx["uow"] = UnitOfWork
    ctx["bot"] = Bot(
        token=config.bot_config.token,
        default=DefaultBotProperties(parse_mode=config.bot_config.parse_mode),
    )
    core = FluentRuntimeCore(path=config.path_to_locales)
    ctx["core"] = core
    await core.startup()


async def shutdown(ctx):
    bot: Bot = ctx["bot"]
    await bot.session.close()


class WorkerSettings:
    redis_settings = RedisConfig.pool_settings
    on_startup = startup
    on_shutdown = shutdown
    functions = [send_notification, create_task_from_regular]
    cron_jobs = [
        cron(
            "scheduler.func.create_task_from_regular",
            hour=0,
            minute=0,
            run_at_startup=True,
        )
    ]
    allow_abort_jobs = True
