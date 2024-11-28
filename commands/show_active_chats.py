import aiosqlite
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from scripts.active_check import is_bot_active
from scripts.logger import log_command

router = Router()

DATABASE_FILE = 'database.db'

@router.message(Command("active"))
async def show_active_chats_handler(message: Message) -> None:
    chat_id = str(message.chat.id)
    
    if not await is_bot_active(chat_id):
        await message.reply("❗️ Бот не активирован в этом чате.")
        return
        
    user_id = message.from_user.id
    
    try:
        async with aiosqlite.connect(DATABASE_FILE) as db:
            async with db.execute("SELECT level FROM users WHERE uid = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
                
        if not row or row[0] < 5:
            await message.reply("❗️ У вас недостаточно прав для использования этой команды.")
            return
            
        async with aiosqlite.connect(DATABASE_FILE) as db:
            async with db.execute("SELECT chat_id, chat_title FROM active_chats") as cursor:
                active_chats = await cursor.fetchall()
                
        if not active_chats:
            await message.reply("ℹ️ Нет активных чатов.")
            return
            
        response = "📋 Список активных чатов:\n\n"
        for chat in active_chats:
            response += f"• {chat[1]} (ID: {chat[0]})\n"
            
        await message.reply(response)
        
    except Exception as e:
        await message.reply(f"❗️ Произошла ошибка: {str(e)}")
    
    await log_command(message, message.text)
