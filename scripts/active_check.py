from functools import wraps
from aiogram.types import Message
from scripts.database import Database

DATABASE_FILE = 'database.db'

async def is_bot_active(chat_id: str) -> bool:
    try:
        active_chats = await Database.get_active_chats()
        return any(chat['chat_id'] == chat_id for chat in active_chats)
    except Exception:
        return False

def check_bot_active(func):
    @wraps(func)
    async def wrapper(message: Message, *args, **kwargs):
        chat_id = str(message.chat.id)
        if not await is_bot_active(chat_id):
            await message.reply("❗️ Бот не активирован в этом чате.")
            return
        return await func(message, *args, **kwargs)
    return wrapper

async def load_active_chats() -> set:
    active_chats = set()
    chats = await Database.get_active_chats()
    for chat in chats:
        active_chats.add(f"{chat['chat_id']}:{chat['chat_title']}")
    return active_chats

async def save_active_chat(chat_id: str, chat_title: str) -> None:
    await Database.add_active_chat(chat_id, chat_title)

async def remove_active_chat(chat_id: str) -> None:
    await Database.remove_active_chat(chat_id)