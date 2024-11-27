import aiosqlite

DATABASE = 'database.db'

async def create_active_chats_table():
    """Создает таблицу active_chats в базе данных."""
    async with aiosqlite.connect(DATABASE) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS active_chats (
                chat_id TEXT PRIMARY KEY,
                chat_title TEXT NOT NULL
            )
        """)
        await db.commit()

import asyncio

async def main():
    await create_active_chats_table()
    print("Таблица 'active_chats' успешно создана.")

if __name__ == "__main__":
    asyncio.run(main())
