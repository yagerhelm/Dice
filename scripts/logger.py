import aiosqlite
from datetime import datetime
from aiogram.types import Message

DATABASE_FILE = 'database.db'

async def log_command(message: Message, command_text: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user_id = message.from_user.id
    chat_id = str(message.chat.id)
    
    try:
        async with aiosqlite.connect(DATABASE_FILE) as db:
            await db.execute("""
                INSERT INTO logs (timestamp, user_id, chat_id, command)
                VALUES (?, ?, ?, ?)
            """, (timestamp, user_id, chat_id, command_text))
            await db.commit()
    except Exception as e:
        print(f"Error logging command: {e}")

async def init_log_table():
    try:
        async with aiosqlite.connect(DATABASE_FILE) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    user_id INTEGER NOT NULL,
                    chat_id TEXT NOT NULL,
                    command TEXT NOT NULL
                )
            """)
            await db.commit()
    except Exception as e:
        print(f"Error initializing log table: {e}")