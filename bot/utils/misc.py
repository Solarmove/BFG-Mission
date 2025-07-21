from aiogram.utils.link import create_tg_link


async def get_user_url(username: str | None, user_id: int, full_name: str):
    """Получает ссылку на пользователя"""
    if username:
        return f"@{username}"
    user_url = create_tg_link("user", id=user_id)
    return f"<a href='{user_url}'>{full_name}</a>"
