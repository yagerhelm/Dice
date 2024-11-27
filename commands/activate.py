import os
import aiosqlite
from telegram import Update
from telegram.ext import ContextTypes

DATABASE_FILE = 'database.db'

async def load_active_chats():
    active_chats = set()

    async with aiosqlite.connect(DATABASE_FILE) as db:
        async with db.execute("SELECT chat_id, chat_title FROM active_chats") as cursor:
            async for row in cursor:
                chat_id, chat_title = row
                active_chats.add(f"{chat_id}:{chat_title}")

    return active_chats


async def save_active_chat(chat_id, chat_title):
    async with aiosqlite.connect(DATABASE_FILE) as db:
        await db.execute("INSERT INTO active_chats (chat_id, chat_title) VALUES (?, ?)", (chat_id, chat_title))
        await db.commit()


async def activate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = str(update.effective_chat.id)
    chat_title = update.effective_chat.title or "Без названия"
    user_id = update.effective_user.id

    try:
        async with aiosqlite.connect(DATABASE_FILE) as db:
            async with db.execute("SELECT level FROM users WHERE uid = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
    except Exception as e:
        await update.message.reply_text(f"❗️ Ошибка доступа к базе данных: {e}")
        return

    if row is None:
        await update.message.reply_text("❗️ Ваш аккаунт не найден в базе данных.")
        return

    user_level = row[0]

    if user_level >= 5:
        active_chats = await load_active_chats()
        
        chat_entry = f"{chat_id}:{chat_title}"

        if chat_entry not in active_chats:
            await save_active_chat(chat_id, chat_title)
            await update.message.reply_text("✅ Бот активирован в этом чате.")
        else:
            await update.message.reply_text("❗️ Бот уже активирован в этом чате.")
    else:
        await update.message.reply_text("⛔️ У вас недостаточно прав для активации бота.")
        
async def init_database():
    async with aiosqlite.connect(DATABASE_FILE) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                uid INTEGER PRIMARY KEY,
                level INTEGER
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS active_chats (
                chat_id TEXT PRIMARY KEY,
                chat_title TEXT
            )
        """)
        await db.commit()
