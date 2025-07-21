from __future__ import annotations

from pathlib import Path

from arq.connections import RedisSettings
from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_PATH = Path(__file__)


class BotConfig(BaseSettings):
    """Bot configuration"""

    token: str
    parse_mode: str


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
    path_to_locales: Path = (
        BASE_PATH / "bot" / "i18n" / "locales" / "{locale}" / "LC_MESSAGES"
    )

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
        password=config.db_config.redis_password,
    )
