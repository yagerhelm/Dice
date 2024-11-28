import aiosqlite

DATABASE_FILE = 'database.db'

async def create_user(uid: int, username: str, level: int = 1, score: int = 0):
    async with aiosqlite.connect(DATABASE_FILE) as db:
        await db.execute("""
            INSERT INTO users (uid, username, level, score)
            VALUES (?, ?, ?, ?)
        """, (uid, username, level, score))
        await db.commit()

async def get_user_profile(username: str):
    async with aiosqlite.connect(DATABASE_FILE) as db:
        async with db.execute("""
            SELECT uid, username, level, score 
            FROM users 
            WHERE username = ?
        """, (username,)) as cursor:
            return await cursor.fetchone()

async def get_user_by_uid(uid: int):
    async with aiosqlite.connect(DATABASE_FILE) as db:
        async with db.execute("""
            SELECT uid, username, level, score 
            FROM users 
            WHERE uid = ?
        """, (uid,)) as cursor:
            return await cursor.fetchone()

async def update_user_score(uid: int, new_score: int):
    async with aiosqlite.connect(DATABASE_FILE) as db:
        await db.execute("""
            UPDATE users 
            SET score = ?
            WHERE uid = ?
        """, (new_score, uid))
        await db.commit()

async def init_user_table():
    async with aiosqlite.connect(DATABASE_FILE) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                uid INTEGER PRIMARY KEY,
                username TEXT NOT NULL,
                level INTEGER DEFAULT 1,
                score INTEGER DEFAULT 0
            )
        """)
        await db.commit()