import logging
import re
from typing import Sequence

# import backoff
import langchain
import openai
from langchain.agents import (
    AgentExecutor,
    create_openai_functions_agent,
)
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableWithMessageHistory, RunnableConfig
from langchain_core.tools import BaseTool
from redis.asyncio import Redis

from bot.services.ai_agent.utils.redis_chat_history import RedisChatMessageHistory
from bot.services.log_service import LogService

langchain.debug = False  # Еще более детальный вывод
logger = logging.getLogger(__name__)


class AIAgent:
    def __init__(
        self,
        model: BaseChatModel,
        prompt: ChatPromptTemplate,
        log_service: LogService,
        tools: Sequence[BaseTool],
        chat_id: int | None = None,
        redis_client: Redis | None = None,
    ):
        self.log_service = log_service
        self.redis_client = redis_client
        self.chat_id = chat_id
        self.model = model
        self._chat_history = (
            RedisChatMessageHistory(
                session_id=f"chat_{self.chat_id}", redis_client=redis_client
            )
            if redis_client
            else InMemoryChatMessageHistory()
        )
        self._agent = create_openai_functions_agent(
            model,
            tools=tools,
            prompt=prompt,
        )
        self._agent_executor = AgentExecutor(
            agent=self._agent,
            tools=tools,
            verbose=True,
            handle_parsing_errors=True,
            return_intermediate_steps=True,
            # max_iterations=3,
        )
        self._agent_with_history = RunnableWithMessageHistory(
            runnable=self._agent_executor,
            history_messages_key="chat_history",
            get_session_history=lambda session_id: self._chat_history,
            input_messages_key="input",
        )

    async def clear_history(self):
        """Очистить историю сообщений."""
        await self._chat_history.aclear()

    @staticmethod
    def replace_unallowed_characters(content: str) -> str:
        """
        Заміна небажаних символів на пробіли.
        :param content: Вхідний текст.
        :return: Текст з заміненими символами.
        """
        # Список небажаних символів
        ALLOWED_TAGS = ["b", "i", "u", "code", "blockquote"]
        allowed_tags_pattern = r"</?(" + "|".join(ALLOWED_TAGS) + r")\b[^>]*>"

        def replacer(match):
            tag = match.group(0)
            if re.fullmatch(allowed_tags_pattern, tag):
                return tag
            else:
                return ""  # удаляем неразрешённый тег

        # Находим все HTML-теги и заменяем неразрешённые на ''
        return re.sub(r"</?[\w\d]+[^>]*>", replacer, content)

    async def invoke(
        self, content: str, with_history: bool = True, without_user_id: bool = False
    ):
        config = RunnableConfig(
            configurable={"session_id": str(self.chat_id or "default")}
        )
        if not without_user_id:
            content += f"\n\nМій user_id: {self.chat_id} (ID в базі данних)"
        log_text = "<b>Запит до AI агента</b>"
        await self.log_service.info(
            log_text, extra_info={"Контент": content, "Chat ID": self.chat_id}
        )
        if with_history:
            result = await self._agent_with_history.ainvoke(
                input={"input": content}, config=config
            )
        else:
            result = await self._agent_executor.ainvoke(
                input={"input": content}, config=config
            )
        result_text = self.replace_unallowed_characters(result["output"])
        await self.log_service.info(
            log_text,
            extra_info={
                "Відповідь": result_text,
                "Chat ID": self.chat_id,
            },
        )
        return result_text

    # @backoff.on_exception(backoff.expo, openai.RateLimitError)
    async def stream_response(self, content: str):
        config = RunnableConfig(
            configurable={"session_id": str(self.chat_id or "default")}
        )
        content += f"\n\nМій user_id: {self.chat_id} (ID в базі данних)"

        log_text = "<b>Запит до AI агента</b>"
        await self.log_service.info(
            log_text, extra_info={"Контент": content, "Chat ID": self.chat_id}
        )

        response_text = ""
        async for chunk in self._agent_with_history.astream(
            input={"input": content}, config=config
        ):
            if "output" in chunk:
                response_text += self.replace_unallowed_characters(chunk["output"])
                log_text = "<b>Відповідь AI агента</b>"
                await self.log_service.info(
                    log_text,
                    extra_info={
                        "Відповідь": response_text,
                        "Chat ID": self.chat_id,
                    },
                )
                yield response_text
            # if "messages" in chunk:
            #     messages = chunk["messages"]
            #     for message in messages:
            #         if not isinstance(message, AIMessage):
            #             continue
            #         if hasattr(message, "content") and len(message.content) > 0:
            #             text = self.replace_unallowed_characters(message.content)
            #             text += "\n\nОпрацьовуємо запит..."
            #             yield response_text, text
            #         yield None, None
            #     continue

            yield None
