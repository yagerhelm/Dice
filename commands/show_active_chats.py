from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from scripts.active_check import check_bot_active
from scripts.logger import log_command
from scripts.database import Database

router = Router()

@router.message(Command("active"))
@check_bot_active
async def show_active_chats_handler(message: Message) -> None:
    user_id = message.from_user.id
    
    try:
        # Проверяем уровень доступа пользователя
        user_data = await Database.get_user(user_id)
        if not user_data or user_data['level'] < 5:
            await message.reply("❗️ У вас недостаточно прав для использования этой команды.")
            return
        
        # Получаем список активных чатов
        active_chats = await Database.get_active_chats()
        
        if not active_chats:
            await message.reply("ℹ️ Нет активных чатов.")
            return
            
        response = "📋 Список активных чатов:\n\n"
        for chat in active_chats:
            response += f"• {chat['chat_title']} (ID: {chat['chat_id']})\n"
            
        await message.reply(response)
        
    except Exception as e:
        await message.reply(f"❗️ Произошла ошибка: {str(e)}")
    
    await log_command(message, message.text)
