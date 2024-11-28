import aiosqlite
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from scripts.active_check import is_bot_active
from scripts.logger import log_command

router = Router()

DATABASE_FILE = 'database.db'

@router.message(Command("invite"))
async def invite_handler(message: Message) -> None:
    chat_id = str(message.chat.id)
    
    # Проверяем активацию бота в чате
    if not await is_bot_active(chat_id):
        await message.reply("❗️ Бот не активирован в этом чате.")
        return
        
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.full_name
    
    try:
        # Проверяем, не зарегистрирован ли уже пользователь
        async with aiosqlite.connect(DATABASE_FILE) as db:
            async with db.execute("SELECT uid FROM users WHERE uid = ?", (user_id,)) as cursor:
                user_exists = await cursor.fetchone()
                
            if user_exists:
                await message.reply("❗️ Вы уже зарегистрированы. Используйте /profile для просмотра профиля.")
                return
                
            # Создаем новый профиль пользователя
            await db.execute(
                "INSERT INTO users (uid, username, level, score) VALUES (?, ?, ?, ?)",
                (user_id, username, 1, 0)
            )
            await db.commit()
            
            user_info = (
                f"✅ Профиль успешно создан!\n\n"
                f"<b>Ваш профиль:</b>\n"
                f"<b>Имя:</b> <code>{username}</code>\n"
                f"<b>Уровень доступа:</b> <code>1</code>\n"
                f"<b>Score:</b> <code>0</code>\n"
            )
            
            await message.reply(user_info, parse_mode='HTML')
        
    except Exception as e:
        await message.reply(f"❗️ Произошла ошибка при создании профиля")
    
    await log_command(message, message.text)