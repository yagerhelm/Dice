import os
import aiosqlite
from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime

async def get_user_level(user_id: int):
    async with aiosqlite.connect('database.db') as db:
        async with db.execute("SELECT level FROM users WHERE uid = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0

async def logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_level = await get_user_level(user_id)

    if user_level is None or user_level < 5:
        await update.message.reply_text("❌ У вас нет доступа к этой команде.")
        return

    if len(context.args) != 1:
        await update.message.reply_text("❗️ Пожалуйста, укажите дату в формате DD-MM-YYYY, например: /logs 01-10-2023.")
        return

    date_str = context.args[0]
    try:
        target_date = datetime.strptime(date_str, '%d-%m-%Y').date()
    except ValueError:
        await update.message.reply_text("❗️ Неверный формат даты. Пожалуйста, используйте формат DD-MM-YYYY.")
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
        await update.message.reply_text(f"⚠️ Логи за {target_date} не найдены.")
    else:
        max_message_length = 4096

        while len(logs_output) > max_message_length:
            split_index = logs_output.rfind('\n', 0, max_message_length)
            if split_index == -1:
                split_index = max_message_length
            
            await update.message.reply_text(logs_output[:split_index])
            logs_output = logs_output[split_index:]

        if logs_output:
            await update.message.reply_text(logs_output)