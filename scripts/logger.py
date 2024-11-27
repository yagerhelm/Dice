import aiosqlite
import datetime
from telegram import Update
from telegram.ext import ContextTypes

DATABASE = 'database.db'
log_enabled = True

async def log_command(update: Update, command: str):
    global log_enabled
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    timestamp = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")

    if log_enabled:
        with open('log.txt', 'a', encoding='utf-8') as log_file:
            log_file.write(f"{timestamp} - User {user_id} executed command: {command} in chat {chat_id}\n")

async def toggle_logging(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global log_enabled
    user_id = update.effective_user.id
    level = await check_user_level(user_id)

    if level is None or level < 5:
        await update.message.reply_text("⛔️ У вас нет прав для изменения логирования.")
        return

    log_enabled = not log_enabled
    status = "включено" if log_enabled else "выключено"
    await update.message.reply_text(f"📥 Логирование команд {status}.")

async def check_user_level(user_id: int) -> int:
    async with aiosqlite.connect(DATABASE, timeout=5) as db:
        cursor = await db.execute("SELECT level FROM users WHERE uid = ?", (user_id,))
        user = await cursor.fetchone()
        return user[0] if user else None