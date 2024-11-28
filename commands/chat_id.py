from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from scripts.active_check import is_bot_active
from scripts.logger import log_command

router = Router()

@router.message(Command("id"))
async def chat_id_handler(message: Message) -> None:
    chat_id = str(message.chat.id)
    
    if not await is_bot_active(chat_id):
        await message.reply("❗️ Бот не активирован в этом чате.")
        return
        
    await message.reply(f"ID этого чата: <code>{chat_id}</code>")
    await log_command(message, message.text)
