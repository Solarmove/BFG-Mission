from aiogram.types import (
    BotCommand,
    BotCommandScopeAllPrivateChats,
)


async def set_default_commands(bot):
    commands = [
        BotCommand(command="start", description="Bot Restart"),
    ]
    await bot.set_my_commands(commands=commands, scope=BotCommandScopeAllPrivateChats())
