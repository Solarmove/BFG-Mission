from __future__ import annotations

import os.path
from pathlib import Path

from arq.connections import RedisSettings
from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_PATH = Path(__file__).parent


class BotConfig(BaseSettings):
    """Bot configuration"""

    token: str
    parse_mode: str
    bot_channel_id: int
    info_logs_channel_thread_id: int
    error_logs_channel_thread_id: int
    debug_logs_channel_thread_id: int
    warning_logs_channel_thread_id: int
    critical_logs_channel_thread_id: int


class DBConfig(BaseSettings):
    """Database configuration"""

    postgres_dsn: PostgresDsn
    redis_host: str
    redis_port: int
    redis_db: int
    redis_password: str


class Config(BaseSettings):
    """Main configuration"""

    bot_config: BotConfig
    db_config: DBConfig
    admins: list[int]
    i18n_format_key: str
    path_to_locales: str = os.path.join(
        "bot", "i18n", "locales", "{locale}", "LC_MESSAGES"
    )
    openai_api_key: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
    )


config = Config()


class RedisConfig:
    pool_settings = RedisSettings(
        host=config.db_config.redis_host,
        port=config.db_config.redis_port,
        database=config.db_config.redis_db,
        # password=config.db_config.redis_password,
    )
