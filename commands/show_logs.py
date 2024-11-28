import os
import aiosqlite
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from datetime import datetime

router = Router()

DATABASE_FILE = 'database.db'

async def get_user_level(user_id: int):
    async with aiosqlite.connect(DATABASE_FILE) as db:
        async with db.execute("SELECT level FROM users WHERE uid = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0

@router.message(Command("logs"))
async def logs_handler(message: Message) -> None:
    user_id = message.from_user.id
    user_level = await get_user_level(user_id)

    if user_level is None or user_level < 5:
        await message.reply("❌ У вас нет доступа к этой команде.")
        return

    if len(message.text.split()) != 2:
        await message.reply("❗️ Пожалуйста, укажите дату в формате DD-MM-YYYY, например: /logs 01-10-2023.")
        return

    date_str = message.text.split()[1]
    try:
        target_date = datetime.strptime(date_str, '%d-%m-%Y').date()
    except ValueError:
        await message.reply("❗️ Неверный формат даты. Пожалуйста, используйте формат DD-MM-YYYY.")
        return

    logs_output = f"📅 Логи за {target_date}:\n"
    log_found = False

    # Чтение файла с логами
    if os.path.exists('log.txt'):
        with open('log.txt', 'r', encoding='utf-8') as log_file:
            for line in log_file:
                if date_str in line:
                    logs_output += line
                    log_found = True

    if not log_found:
        await message.reply(f"⚠️ Логи за {target_date} не найдены.")
    else:
        max_message_length = 4096

        while len(logs_output) > max_message_length:
            split_index = logs_output.rfind('\n', 0, max_message_length)
            if split_index == -1:
                split_index = max_message_length
            
            await message.reply(logs_output[:split_index])
            logs_output = logs_output[split_index:]

        if logs_output:
            await message.reply(logs_output)