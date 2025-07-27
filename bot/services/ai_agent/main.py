import asyncio
import logging
from pprint import pprint
from typing import Sequence

import langchain
from langchain.agents import (
    AgentExecutor,
    create_openai_functions_agent,
)
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableWithMessageHistory, RunnableConfig
from langchain_core.tools import BaseTool
from openai import RateLimitError
from redis.asyncio import Redis

from bot.services.ai_agent.utils.redis_chat_history import RedisChatMessageHistory

# example of using OpenAI's GPT-4o model
# llm = ChatOpenAI(model="gpt-4o", temperature=0.2, max_tokens=4096)

langchain.debug = False  # Еще более детальный вывод
logger = logging.getLogger(__name__)


class AIAgent:
    def __init__(
        self,
        model: BaseChatModel,
        tools: Sequence[BaseTool],
        prompt: ChatPromptTemplate,
        chat_id: int | None = None,
        redis_client: Redis | None = None,
    ):
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

    async def invoke(self, content: str):
        config = RunnableConfig(
            configurable={"session_id": str(self.chat_id or "default")}
        )
        content += f"\n\nMy id: {self.chat_id}"
        result = await self._agent_with_history.ainvoke(
            input={"input": content}, config=config
        )
        return result["output"]

    async def stream_response(self, content: str):
        config = RunnableConfig(
            configurable={"session_id": str(self.chat_id or "default")}
        )
        content += f"\n\nМій user_id: {self.chat_id} (ID в базі данних)"
        response_text = ""
        have_response = False
        # while not have_response:
        #     try:
        async for chunk in self._agent_with_history.astream(
            input={"input": content}, config=config
        ):
            pprint(chunk)

            if "output" in chunk:
                have_response = True
                response_text += chunk["output"]
                yield response_text
            else:
                yield None
            # except RateLimitError as e:
            #     print(e)
            #     logger.info(f"Rate limit exceeded: {e}")
            #     await asyncio.sleep(3)
                    # yield
            # return response_text
