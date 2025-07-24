import datetime
import json
from functools import wraps

from redis.asyncio import Redis

from configreader import config

redis = Redis(
    host=config.db_config.redis_host,
    port=config.db_config.redis_port,
    db=config.db_config.redis_db,
    # password=config.db_config.redis_password,
)


def _make_cache_key(func, args, kwargs):
    # Формируем ключ только по простым типам (int, str, float)
    key_parts = [func.__name__]
    for arg in args:
        if isinstance(arg, (int, str, float)):
            key_parts.append(str(arg))
        else:
            key_parts.append(str(type(arg)))
    for k, v in kwargs.items():
        if isinstance(v, (int, str, float)):
            key_parts.append(f"{k}={v}")
        else:
            key_parts.append(f"{k}={type(v)}")
    return ":".join(key_parts)


def redis_cache(expiration=3600):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            key = _make_cache_key(func, args, kwargs)
            if kwargs.get("update_cache", False):
                result = await func(*args, **kwargs)
                try:
                    value_json = json.dumps(result, default=lambda o: o.__dict__)
                except Exception:
                    value_json = str(result)
                await redis.set(key, value_json, ex=expiration)
                return result
            cached_result = await redis.get(key)
            if cached_result:
                value_json = cached_result.decode("utf-8")
                try:
                    value = json.loads(value_json)
                except Exception:
                    value = value_json
                return value
            result = await func(*args, **kwargs)
            try:
                value_json = json.dumps(result, default=lambda o: o.__dict__)
            except Exception:
                value_json = str(result)
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


async def save_ai_agent_memory(redis: Redis, key: str, data: list[dict | str]):
    """
    Save AI agent memory to Redis.
    :param redis: Redis instance.
    :param key: Unique key for the memory.
    :param data: List of messages or data to save.
    """
    value_json = json.dumps(data)
    await redis.set(key, value_json, ex=datetime.timedelta(days=1))


async def get_ai_agent_memory(redis: Redis, key: str) -> list[dict | str]:
    """
    Retrieve AI agent memory from Redis.
    :param redis: Redis instance.
    :param key: Unique key for the memory.
    :return: List of messages or data.
    """
    cached_data = await redis.get(key)
    if cached_data:
        value_json = cached_data.decode("utf-8")
        try:
            return json.loads(value_json)
        except json.JSONDecodeError:
            return []
    return []