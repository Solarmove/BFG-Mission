from arq import create_pool
from langchain_openai import ChatOpenAI

from bot.db.redis import redis
from bot.services.ai_agent.main import AIAgent
from bot.services.ai_agent.prompts import GLOBAL_PROMPT
from bot.services.ai_agent.tools_manager import Tools

from bot.utils.unitofwork import UnitOfWork

# from bot.services.task_services import create_task
from configreader import RedisConfig, config


async def main():
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.0,
        # max_tokens=1000,
        api_key=config.openai_api_key,
    )
    # agent = AIAgent(
    #     model=llm,
    #     tools=[get_all_users_from_db],
    #     prompt=GET_ALL_USERS_PROMPT,
    #     redis_client=redis,
    # )
    redis_pool = await create_pool(RedisConfig.pool_settings)

    task_tools = Tools(uow=UnitOfWork(), arq=redis_pool)

    agent = AIAgent(
        model=llm,
        tools=task_tools.get_tools(),
        prompt=GLOBAL_PROMPT,
        redis_client=redis,
        chat_id=387375605,
    )
    await agent.clear_history()
    while True:
        text = input("Введіть запит: ")
        llm_response = await agent.invoke(str(text))
        print(f"LLM: {llm_response}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
