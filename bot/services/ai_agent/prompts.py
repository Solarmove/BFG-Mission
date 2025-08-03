from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
)


LLM_AGENT_FORMATER_PROMPT = """
Твоя задача:
1. відформатувати текст, який надіслав користувач,з Markdown формата у HTML-формат.
2. Додати емодзі (якщо їх немає) там де це доречно
3. повернути відформатовану відповідь.

## Приклад форматування
### ✅ ПРАВИЛЬНО (використовуй HTML):
- <b>Важливий текст</b>
- <i>Виділений текст</i>
- <u>Підкреслений текст</u>
- <code>print("код")</code>
- <b><i>Комбінований текст</i></b>
Перелік данних ЗАВЖДИ обгортай в <blockquote></blockquote> але не зловживай:
Приклад:
"Ось список категорій, які зараз є в базі даних:

<blockquote>🌱 Догляд за рослинами
📝 test1
📝 test2
📝 test3
🧹 прибирання
🍽️ кейтеринг</blockquote>

Якщо потрібно додати, змінити або видалити якусь категорію — дай знати!
"

### ❌ НЕПРАВИЛЬНО (НЕ використовуй Markdown):
- **текст** або __текст__
- *текст* або _текст_
- `код`
- ***текст***
НЕ ВИКОРИСТОВУЙ  <br>, <hr>, <p>, <div>, <span>, <strong>, <em>, <code>, <pre>, <ul>, <ol>, <li>.
"""


def generate_prompt(user_prompt: str):
    prompt = user_prompt
    global_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )
    return global_prompt


def generate_prompt_without_history(user_prompt: str):
    prompt = user_prompt
    global_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", prompt),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )
    return global_prompt