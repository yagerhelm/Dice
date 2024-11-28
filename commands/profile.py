from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
import aiosqlite
from scripts.active_check import is_bot_active
from scripts.logger import log_command

router = Router()

DATABASE_FILE = 'database.db'

@router.message(Command("profile"))
async def profile_handler(message: Message) -> None:
    chat_id = str(message.chat.id)
    
    if not await is_bot_active(chat_id):
        await message.reply("❗️ Бот не активирован в этом чате.")
        return

    user_id = message.from_user.id
    command_args = message.text.split()[1:] if message.text else []

    try:
        async with aiosqlite.connect(DATABASE_FILE) as db:
            if command_args:
                # Поиск профиля другого пользователя по имени
                user_name = command_args[0]
                if user_name.startswith('@'):
                    user_name = user_name[1:]
                
                async with db.execute(
                    "SELECT uid, username, level, score FROM users WHERE username LIKE ?",
                    (f"%{user_name}%",)
                ) as cursor:
                    user_data = await cursor.fetchone()

                if user_data:
                    uid, name, level, score = user_data
                    user_info = (
                        f"<b>Профиль пользователя</b>\n\n"
                        f"<b>Имя:</b> <code>{name}</code>\n"
                        f"<b>Уровень доступа:</b> <code>{level}</code>\n"
                        f"<b>Score:</b> <code>{score}</code>\n"
                    )
                    await message.reply(user_info, parse_mode='HTML')
                else:
                    await message.reply("❗️ Профиль не найден.")
            else:
                # Поиск своего профиля
                async with db.execute(
                    "SELECT uid, username, level, score FROM users WHERE uid = ?",
                    (user_id,)
                ) as cursor:
                    user_data = await cursor.fetchone()

                if user_data:
                    uid, name, level, score = user_data
                    user_info = (
                        f"<b>Ваш профиль</b>\n\n"
                        f"<b>Имя:</b> <code>{name}</code>\n"
                        f"<b>Уровень доступа:</b> <code>{level}</code>\n"
                        f"<b>Score:</b> <code>{score}</code>\n"
                    )
                    await message.reply(user_info, parse_mode='HTML')
                else:
                    await message.reply("❗️ Профиль не найден. Используйте /invite для создания профиля.")
    
    except Exception as e:
        await message.reply("❗️ Произошла ошибка при получении профиля")
    
    await log_command(message, message.text)
