import aiosqlite
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from scripts.logger import log_command

router = Router()

DATABASE_FILE = 'database.db'

async def remove_active_chat(chat_id):
    async with aiosqlite.connect(DATABASE_FILE) as db:
        await db.execute("DELETE FROM active_chats WHERE chat_id = ?", (chat_id,))
        await db.commit()

@router.message(Command("deactivate"))
async def deactivate_handler(message: Message) -> None:
    chat_id = str(message.chat.id)
    user_id = message.from_user.id

    try:
        async with aiosqlite.connect(DATABASE_FILE) as db:
            async with db.execute("SELECT level FROM users WHERE uid = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
    except Exception as e:
        await message.reply(f"❗️ Ошибка доступа к базе данных: {e}")
        return

    if row is None:
        await message.reply("❗️ Ваш аккаунт не найден в базе данных.")
        return

    user_level = row[0]

    if user_level >= 5:
        try:
            async with aiosqlite.connect(DATABASE_FILE) as db:
                async with db.execute("SELECT chat_id FROM active_chats WHERE chat_id = ?", (chat_id,)) as cursor:
                    row = await cursor.fetchone()

                if row:
                    await remove_active_chat(chat_id)
                    await message.reply("✅ Бот деактивирован в этом чате.")
                else:
                    await message.reply("❗️ Бот не был активирован в этом чате.")
        except Exception as e:
            await message.reply(f"❗️ Ошибка при деактивации бота: {e}")
    else:
        await message.reply("⛔️ У вас недостаточно прав для деактивации бота.")
    
    await log_command(message, message.text)