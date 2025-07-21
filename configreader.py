from __future__ import annotations


from arq.connections import RedisSettings
from pydantic import PostgresDsn, ConfigDict
from pydantic_settings import BaseSettings


class BotConfig(BaseSettings):
    """Bot configuration"""

    token: str
    parse_mode: str


class DBConfig(BaseSettings):
    """Database configuration"""

    host: str
    port: int
    user: str
    password: str
    database: str
    postgres_dsn: PostgresDsn
    redis_host: str
    redis_port: int
    redis_db: int


class Config(BaseSettings):
    """Main configuration"""

    bot_config: BotConfig
    db_config: DBConfig
    admins: list[int]
    i18n_format_key: str

    model_config = ConfigDict(
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
    )
