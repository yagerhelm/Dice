import aiosqlite
import os
from typing import Optional, List, Dict, Any, Union
from datetime import datetime

class Database:
    DATABASE_FILE = 'database.db'

    @classmethod
    async def create_tables(cls):
        async with aiosqlite.connect(cls.DATABASE_FILE) as db:
            # Создание таблицы пользователей
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    uid INTEGER PRIMARY KEY,
                    username TEXT NOT NULL,
                    level INTEGER DEFAULT 1,
                    score INTEGER DEFAULT 1000,
                    bonus_score INTEGER DEFAULT 0,
                    promo_score INTEGER DEFAULT 0,
                    free_spins INTEGER DEFAULT 0
                )
            """)
            
            # Создание таблицы активных чатов
            await db.execute("""
                CREATE TABLE IF NOT EXISTS active_chats (
                    chat_id TEXT PRIMARY KEY,
                    chat_title TEXT NOT NULL
                )
            """)
            
            # Создание таблицы логов
            await db.execute("""
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    user_id INTEGER NOT NULL,
                    chat_id TEXT NOT NULL,
                    command TEXT NOT NULL
                )
            """)
            
            # Создание таблицы игр в кости
            await db.execute("""
                CREATE TABLE IF NOT EXISTS dice_games (
                    game_number INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id INTEGER,
                    creator_id INTEGER NOT NULL,
                    creator_name TEXT NOT NULL,
                    creator_username TEXT NOT NULL,
                    bet INTEGER NOT NULL,
                    max_players INTEGER NOT NULL,
                    players TEXT DEFAULT '[]',
                    ready_players TEXT DEFAULT '{}',
                    is_started INTEGER DEFAULT 0,
                    is_ready_check INTEGER DEFAULT 0,
                    total_prize INTEGER DEFAULT 0,
                    winners TEXT DEFAULT '[]',
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await db.commit()

    @classmethod
    async def initialize(cls):
        """Инициализация базы данных"""
        if not os.path.exists(cls.DATABASE_FILE):
            print(f"Database file {cls.DATABASE_FILE} not found, creating...")
            await cls.create_tables()
            print("Database initialized successfully!")
        else:
            print(f"Database file {cls.DATABASE_FILE} found")
            await cls.create_tables()

    @classmethod
    async def get_user(cls, user_id: int) -> Optional[Dict[str, Any]]:
        """Получение данных пользователя"""
        async with aiosqlite.connect(cls.DATABASE_FILE) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM users WHERE uid = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    @classmethod
    async def create_user(cls, user_id: int, username: str) -> bool:
        """Создание нового пользователя"""
        try:
            async with aiosqlite.connect(cls.DATABASE_FILE) as db:
                await db.execute(
                    "INSERT INTO users (uid, username) VALUES (?, ?)",
                    (user_id, username)
                )
                await db.commit()
                return True
        except Exception:
            return False

    @classmethod
    async def get_user_score(cls, user_id: int) -> Optional[int]:
        """Получение счета пользователя"""
        async with aiosqlite.connect(cls.DATABASE_FILE) as db:
            async with db.execute("SELECT score FROM users WHERE uid = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else None

    @classmethod
    async def update_score(cls, user_id: int, amount: int) -> bool:
        """Обновление счета пользователя"""
        try:
            async with aiosqlite.connect(cls.DATABASE_FILE) as db:
                await db.execute(
                    "UPDATE users SET score = score + ? WHERE uid = ?",
                    (amount, user_id)
                )
                await db.commit()
                return True
        except Exception:
            return False

    @classmethod
    async def create_dice_game(cls, creator_id: int, creator_name: str, 
                             creator_username: str, bet: int, max_players: int) -> int:
        """Создание новой игры в кости"""
        async with aiosqlite.connect(cls.DATABASE_FILE) as db:
            cursor = await db.execute("""
                INSERT INTO dice_games (creator_id, creator_name, creator_username, bet, max_players)
                VALUES (?, ?, ?, ?, ?)
            """, (creator_id, creator_name, creator_username, bet, max_players))
            await db.commit()
            return cursor.lastrowid

    @classmethod
    async def get_dice_game(cls, game_id: Union[int, str]) -> Optional[Dict[str, Any]]:
        """Получение данных игры"""
        async with aiosqlite.connect(cls.DATABASE_FILE) as db:
            db.row_factory = aiosqlite.Row
            query = "SELECT * FROM dice_games WHERE "
            query += "game_number = ?" if isinstance(game_id, int) else "message_id = ?"
            async with db.execute(query, (game_id,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    @classmethod
    async def update_dice_game(cls, game_number: int, **kwargs) -> bool:
        """Обновление данных игры"""
        try:
            async with aiosqlite.connect(cls.DATABASE_FILE) as db:
                set_clause = ", ".join(f"{k} = ?" for k in kwargs.keys())
                query = f"UPDATE dice_games SET {set_clause} WHERE game_number = ?"
                values = list(kwargs.values()) + [game_number]
                await db.execute(query, values)
                await db.commit()
                return True
        except Exception:
            return False

    @classmethod
    async def delete_dice_game(cls, game_number: int) -> bool:
        """Удаление игры"""
        try:
            async with aiosqlite.connect(cls.DATABASE_FILE) as db:
                await db.execute("DELETE FROM dice_games WHERE game_number = ?", (game_number,))
                await db.commit()
                return True
        except Exception:
            return False

    @classmethod
    async def get_active_chats(cls) -> List[Dict[str, Any]]:
        """Получение списка активных чатов"""
        async with aiosqlite.connect(cls.DATABASE_FILE) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM active_chats") as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    @classmethod
    async def add_active_chat(cls, chat_id: str, chat_title: str) -> bool:
        """Добавление активного чата"""
        try:
            async with aiosqlite.connect(cls.DATABASE_FILE) as db:
                await db.execute(
                    "INSERT OR REPLACE INTO active_chats (chat_id, chat_title) VALUES (?, ?)",
                    (chat_id, chat_title)
                )
                await db.commit()
                return True
        except Exception:
            return False

    @classmethod
    async def remove_active_chat(cls, chat_id: str) -> bool:
        """Удаление активного чата"""
        try:
            async with aiosqlite.connect(cls.DATABASE_FILE) as db:
                await db.execute("DELETE FROM active_chats WHERE chat_id = ?", (chat_id,))
                await db.commit()
                return True
        except Exception:
            return False

    @classmethod
    async def add_log(cls, user_id: int, chat_id: str, command: str) -> bool:
        """Добавление лога команды"""
        try:
            async with aiosqlite.connect(cls.DATABASE_FILE) as db:
                await db.execute(
                    "INSERT INTO logs (timestamp, user_id, chat_id, command) VALUES (datetime('now'), ?, ?, ?)",
                    (user_id, chat_id, command)
                )
                await db.commit()
                return True
        except Exception:
            return False
