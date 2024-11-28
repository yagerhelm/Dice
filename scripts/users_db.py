import aiosqlite

DATABASE = 'database.db'

async def init_db():
    async with aiosqlite.connect(DATABASE) as db:
        await db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            uid INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            level INTEGER NOT NULL,
            score INTEGER NOT NULL
        );''')
        await db.commit()

async def main():
    await init_db()
    print("Таблица 'users' успешно создана.")

import asyncio
asyncio.run(main())
