import json
from functools import wraps

from redis.asyncio import Redis

from configreader import config

redis = Redis(
    host=config.db_config.redis_host,
    port=config.db_config.redis_port,
    db=config.db_config.redis_db,
)


def redis_cache(expiration=3600):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Создание уникального ключа кэша на основе аргументов функции
            key = f"{func.__name__}:{args}:{kwargs}"
            # Проверяем, есть ли флаг update в kwargs
            if kwargs.get("update_cache", False):
                result = await func(*args, **kwargs)
                value_json = json.dumps(result)
                await redis.set(key, value_json, ex=expiration)
                return result
            cached_result = await redis.get(key)
            if cached_result:
                value_json = cached_result.decode("utf-8")
                value = json.loads(value_json)
                return value
            result = await func(*args, **kwargs)
            value_json = json.dumps(result)
            await redis.set(key, value_json, ex=expiration)
            return result

        return wrapper

    return decorator


async def get_user_locale(user_id: int):
    user_locale = await redis.get(f"user:{user_id}:locale")
    if user_locale:
        return user_locale.decode()
    return None

async def set_user_locale(user_id: int, locale: str):
    await redis.set(f"user:{user_id}:locale", locale)

