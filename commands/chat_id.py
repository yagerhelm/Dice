from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from scripts.active_check import check_bot_active
from scripts.logger import log_command

router = Router()

@router.message(Command("id"))
@check_bot_active
async def chat_id_handler(message: Message) -> None:
    await message.reply(f"ID этого чата: <code>{message.chat.id}</code>")
    await log_command(message, message.text)
