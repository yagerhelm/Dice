import aiosqlite
from telegram import Update
from telegram.ext import ContextTypes

async def load_active_chats():
    async with aiosqlite.connect('database.db') as db:
        async with db.execute("SELECT chat_id, chat_title FROM active_chats") as cursor:
            rows = await cursor.fetchall()
            return {f"{row[0]}:{row[1]}" for row in rows}

async def save_active_chat(chat_id, chat_title):
    async with aiosqlite.connect('database.db') as db:
        await db.execute("INSERT OR REPLACE INTO active_chats (chat_id, chat_title) VALUES (?, ?)", 
                         (chat_id, chat_title))
        await db.commit()

async def deactivate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = str(update.effective_chat.id)
    chat_title = update.effective_chat.title or "Без названия"
    user_id = update.effective_user.id

    chat_entry = f"{chat_id}:{chat_title}"

    async with aiosqlite.connect('database.db') as db:
        async with db.execute("SELECT level FROM users WHERE uid = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()

    if row is None:
        await update.message.reply_text("❗️ Ваш аккаунт не найден в базе данных.")
        return 

    user_level = row[0]

    if user_level >= 5:
        active_chats = await load_active_chats()
        
        if chat_entry in active_chats:
            async with aiosqlite.connect('database.db') as db:
                await db.execute("DELETE FROM active_chats WHERE chat_id = ? AND chat_title = ?", 
                                 (chat_id, chat_title))
                await db.commit()
            await update.message.reply_text("✅ Бот деактивирован в этом чате.")
        else:
            await update.message.reply_text("❗️ Бот не был активирован в этом чате.")
    else:
        await update.message.reply_text("⛔️ У вас недостаточно прав для деактивации бота.")