from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, messages_from_dict, messages_to_dict
from typing import List
import json
import redis.asyncio as redis


class RedisChatMessageHistory(BaseChatMessageHistory):
    def __init__(self, session_id: str, redis_client: redis.Redis):
        self.session_id = session_id
        self.redis_client = redis_client
        self.key = f"chat_history:{session_id}"

    async def aget_messages(self) -> List[BaseMessage]:
        """Асинхронно получить сообщения"""
        data = await self.redis_client.get(self.key)
        if data:
            messages_data = json.loads(data)
            return messages_from_dict(messages_data)
        return []

    async def aadd_messages(self, messages: List[BaseMessage]) -> None:
        """Асинхронно добавить сообщения"""
        existing = await self.aget_messages()
        existing.extend(messages)
        data = messages_to_dict(existing)
        await self.redis_client.set(self.key, json.dumps(data))

    async def aclear(self) -> None:
        """Асинхронно очистить историю"""
        await self.redis_client.delete(self.key)

    # Синхронные версии (обязательны для интерфейса)
    @property
    def messages(self) -> List[BaseMessage]:
        # Для синхронного доступа используем пустой список
        return []

    def add_messages(self, messages: List[BaseMessage]) -> None:
        pass

    def clear(self) -> None:
        pass
