import aiosqlite
from telegram import Update
from telegram.ext import ContextTypes

async def is_bot_active(chat_id: str) -> bool:
    return await load_active_chats(chat_id)

async def load_active_chats(chat_id: str) -> bool:
    async with aiosqlite.connect('database.db') as db:
        async with db.execute("SELECT 1 FROM active_chats WHERE chat_id = ?", (chat_id,)) as cursor:
            row = await cursor.fetchone()
            return row is not None

async def activate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = str(update.effective_chat.id)
    chat_title = update.effective_chat.title or "Без названия"
    user_id = update.effective_user.id

    async with aiosqlite.connect('database.db') as db:
        async with db.execute("SELECT level FROM users WHERE uid = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
    
    if row is None:
        await update.message.reply_text("❗️ Ваш аккаунт не найден в базе данных.")
        return

    user_level = row[0]

    if user_level >= 5:
        if await is_bot_active(chat_id):
            await update.message.reply_text("❗️ Бот уже активирован в этом чате.")
        else:
            async with aiosqlite.connect('database.db') as db:
                await db.execute("INSERT INTO active_chats (chat_id, chat_title) VALUES (?, ?)", (chat_id, chat_title))
                await db.commit()
            await update.message.reply_text("✅ Бот активирован в этом чате.")
    else:
        await update.message.reply_text("⛔️ У вас недостаточно прав для активации бота.")