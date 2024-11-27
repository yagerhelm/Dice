import aiosqlite

DATABASE = 'database.db'

async def create_user(uid: int, name: str):
    level = 0
    score = 0

    async with aiosqlite.connect(DATABASE) as db:
        await db.execute('''
        INSERT INTO users (uid, name, level, score) 
        VALUES (?, ?, ?, ?)
        ''', 
        (uid, name, level, score))
        await db.commit()

async def get_user_profile(name: str = None):
    if name is not None:
        print("No name or name provided")
        return None

    async with aiosqlite.connect(DATABASE) as db:
        if name is not None:
            async with db.execute("SELECT * FROM users WHERE name = ?", (name,)) as cursor:
                user = await cursor.fetchone()
                return user

async def get_user_by_uid(uid: int):
    if uid is not None:
        async with aiosqlite.connect(DATABASE) as db:
            if uid is not None:
                async with db.execute("SELECT * FROM users WHERE uid = ?", (uid,)) as cursor:
                    user = await cursor.fetchone()
                    return user

async def get_user_score(uid):
        with aiosqlite.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT score FROM users WHERE uid = ?', (uid,))
            result = cursor.fetchone()
            return result[0] if result else 0

async def update_user_score(uid, score):
        with aiosqlite.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (uid, score) 
                VALUES (?, ?) 
                ON CONFLICT(uid) DO UPDATE SET score = score + ?
            ''', (uid, score, score))
            conn.commit()