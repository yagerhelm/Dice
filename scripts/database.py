import aiosqlite
import os

DATABASE_FILE = 'database.db'

async def check_tables(db):
    tables = {
        'users': False,
        'active_chats': False,
        'logs': False,
        'game_history': False
    }
    
    async with db.execute("SELECT name FROM sqlite_master WHERE type='table'") as cursor:
        existing_tables = await cursor.fetchall()
        for table in existing_tables:
            if table[0] in tables:
                tables[table[0]] = True
    
    return tables

async def init_database():
    async with aiosqlite.connect(DATABASE_FILE) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                uid INTEGER PRIMARY KEY,
                username TEXT NOT NULL,
                level INTEGER DEFAULT 1,
                score INTEGER DEFAULT 0
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS active_chats (
                chat_id TEXT PRIMARY KEY,
                chat_title TEXT NOT NULL
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                chat_id TEXT NOT NULL,
                command TEXT NOT NULL
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS game_history (
                game_number INTEGER PRIMARY KEY,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                creator_id INTEGER,
                creator_name TEXT,
                bet INTEGER,
                max_players INTEGER,
                players TEXT,
                results TEXT,
                winners TEXT,
                prize_per_winner INTEGER
            )
        """)
        
        await db.commit()

async def check_database():
    """Check if database exists and initialize if needed"""
    try:
        if not os.path.exists(DATABASE_FILE):
            print(f"Database file {DATABASE_FILE} not found, creating...")
            await init_database()
            print("Database initialized successfully!")
        else:
            print(f"Database file {DATABASE_FILE} found, checking tables...")
            async with aiosqlite.connect(DATABASE_FILE) as db:
                tables = await check_tables(db)
                missing_tables = [table for table, exists in tables.items() if not exists]
                
                if missing_tables:
                    print(f"Missing tables found: {', '.join(missing_tables)}")
                    print("Creating missing tables...")
                    await init_database()
                    print("Tables created successfully!")
                else:
                    print("All required tables exist!")
    except Exception as e:
        print(f"Error during database check: {str(e)}")
        print("Attempting to recreate the database...")
        await init_database()
        print("Database recreated successfully!")
