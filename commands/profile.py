from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from scripts.active_check import check_bot_active
from scripts.logger import log_command
from scripts.database import Database

router = Router()

@router.message(Command("profile"))
@check_bot_active
async def profile_handler(message: Message) -> None:
    user_id = message.from_user.id
    command_args = message.text.split()[1:] if message.text else []

    try:
        if command_args:
            # Поиск профиля другого пользователя по имени
            user_name = command_args[0]
            if user_name.startswith('@'):
                user_name = user_name[1:]
            
            async with aiosqlite.connect(Database.DATABASE_FILE) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT uid, username, level, score FROM users WHERE username LIKE ?",
                    (f"%{user_name}%",)
                ) as cursor:
                    user_data = await cursor.fetchone()

            if user_data:
                user_info = (
                    f"<b>Профиль пользователя</b>\n\n"
                    f"<b>Имя:</b> <code>{user_data['username']}</code>\n"
                    f"<b>Уровень доступа:</b> <code>{user_data['level']}</code>\n"
                    f"<b>Score:</b> <code>{user_data['score']}</code>\n"
                )
                await message.reply(user_info, parse_mode='HTML')
            else:
                await message.reply("❗️ Профиль не найден.")
        else:
            # Поиск своего профиля
            user_data = await Database.get_user(user_id)
            
            if user_data:
                user_info = (
                    f"<b>Ваш профиль</b>\n\n"
                    f"<b>Имя:</b> <code>{user_data['username']}</code>\n"
                    f"<b>Уровень доступа:</b> <code>{user_data['level']}</code>\n"
                    f"<b>Score:</b> <code>{user_data['score']}</code>\n"
                    f"<b>Бонусный счет:</b> <code>{user_data['bonus_score']}</code>\n"
                    f"<b>Промо счет:</b> <code>{user_data['promo_score']}</code>\n"
                    f"<b>Бесплатные вращения:</b> <code>{user_data['free_spins']}</code>\n"
                )
                await message.reply(user_info, parse_mode='HTML')
            else:
                await message.reply("❗️ Профиль не найден. Используйте /invite для регистрации.")

    except Exception as e:
        await message.reply(f"❗️ Произошла ошибка при получении профиля: {str(e)}")
    
    await log_command(message, message.text)
