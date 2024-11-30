from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from scripts.active_check import check_bot_active
from scripts.logger import log_command
from scripts.database import Database

router = Router()

@router.message(Command("invite"))
@check_bot_active
async def invite_handler(message: Message) -> None:
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.full_name
    
    try:
        # Проверяем, не зарегистрирован ли уже пользователь
        user_data = await Database.get_user(user_id)
        if user_data:
            await message.reply("❗️ Вы уже зарегистрированы. Используйте /profile для просмотра профиля.")
            return
            
        # Создаем новый профиль пользователя
        if await Database.create_user(user_id, username):
            user_info = (
                f"✅ Профиль успешно создан!\n\n"
                f"<b>Ваш профиль:</b>\n"
                f"<b>Имя:</b> <code>{username}</code>\n"
                f"<b>Уровень доступа:</b> <code>1</code>\n"
                f"<b>Score:</b> <code>0</code>\n"
            )
            await message.reply(user_info, parse_mode='HTML')
        else:
            await message.reply("❗️ Произошла ошибка при создании профиля")
    
    except Exception as e:
        await message.reply(f"❗️ Произошла ошибка при создании профиля: {str(e)}")
    
    await log_command(message, message.text)