import logging
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String, Float, BIGINT, update, delete
import os
import asyncio
import json


DATABASE_URL = 'sqlite+aiosqlite:///database/database.db'


engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False)
    balance = Column(Float, default=0.0)
    bonus_balance = Column(Float, default=0.0)
    promo_code = Column(String, default=None)
    free_spins = Column(Integer, default=0)



class Payments(Base):
    __tablename__ = 'payments'
    id = Column(Integer, primary_key=True)
    payment_id = Column(BIGINT)
    summa = Column(Float)



class DiceGame(Base):
    __tablename__ = 'dice_games'
    
    game_number = Column(Integer, primary_key=True)
    creator_id = Column(Integer, nullable=False)
    creator_name = Column(String)
    creator_username = Column(String)
    bet = Column(Float, nullable=False)
    max_players = Column(Integer, nullable=False)
    players = Column(String)
    ready_players = Column(String)
    is_started = Column(Integer, default=0)
    is_ready_check = Column(Integer, default=0)
    results = Column(String)
    message_id = Column(Integer)
    total_prize = Column(Float)
    winners = Column(String)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        



if not os.path.exists('database/database.db'):
    os.makedirs(os.path.dirname('database/database.db'), exist_ok=True)


class Database:
    def __init__(self):
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(init_db())
        except RuntimeError:
            asyncio.run(init_db())


    async def add_new_payment(self, payment_id: int, summa: float):
        async with AsyncSessionLocal() as session:
            async with session.begin():
                payment = Payments(payment_id=payment_id, summa=summa)
                session.add(payment)

    async def select_payment(self, payment_id: int):
        async with AsyncSessionLocal() as session:
            payment = await session.execute(select(Payments).where(Payments.payment_id == payment_id))
            return payment.scalar()

    async def delete_payment(self, payment_id: int):
        async with AsyncSessionLocal() as session:
            payment = delete(Payments).where(Payments.payment_id == payment_id)
            await session.execute(payment)
            await session.commit()

    async def add_new_user(self, user_id, username):
        async with AsyncSessionLocal() as session:
            async with session.begin():
                user = User(user_id=user_id, username=username)
                session.add(user)

    async def user_exists(self, user_id):
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).filter_by(user_id=user_id))
            user = result.scalars().first()
            return user is not None


    async def get_user_balance(self, user_id):
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(select(User).filter_by(user_id=user_id))
                user = result.scalars().first()
                return user.balance if user else None
        except Exception as e:
            logging.error(f"Ошибка при получении баланса пользователя: {e}")
            return None

    async def add_user_balance(self, user_id, amount):
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).filter_by(user_id=user_id))
            user = result.scalars().first()
            if user:
                user.balance += amount
                await session.commit()

    async def get_user_promo_code(self, user_id):
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).filter_by(user_id=user_id))
            user = result.scalars().first()
            return user.promo_code if user else None

    async def set_user_promo_code(self, user_id, promo_code):
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).filter_by(user_id=user_id))
            user = result.scalars().first()
            if user:
                user.promo_code = promo_code
                await session.commit()
    async def reduce_free_spins(self, user_id, count):
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).filter_by(user_id=user_id))
            user = result.scalars().first()
            if user and user.free_spins >= count:
                user.free_spins -= count
                await session.commit()

    async def get_free_spins(self, user_id):
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).filter_by(user_id=user_id))
            user = result.scalars().first()
            return user.free_spins if user else 0

    async def add_free_spins(self, user_id, amount):
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).filter_by(user_id=user_id))
            user = result.scalars().first()
            if user:
                user.free_spins += amount
                await session.commit()

    async def get_all_user_ids(self):
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User))
            users = result.scalars().all()
            return [user.user_id for user in users]

    async def create_user_if_not_exists(self, user_id, username):
        if not await self.user_exists(user_id):
            await self.add_new_user(user_id, username)

    async def update_balance(self, user_id: int, balance: float):
        async with AsyncSessionLocal() as session:
            user = (
                update(User)
                .where(User.user_id == user_id)
                .values({User.balance: User.balance + balance})
            )
            await session.execute(user)
            await session.commit()

    async def get_user_bonus_balance(self, user_id):
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).filter_by(user_id=user_id))
            user = result.scalars().first()
            return user.bonus_balance if user else None

    async def add_user_bonus_balance(self, user_id, amount):
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).filter_by(user_id=user_id))
            user = result.scalars().first()
            if user:
                user.bonus_balance += amount
                await session.commit()
            
    async def get_user_by_id(self, user_id: int):
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).filter_by(user_id=user_id))
            user = result.scalars().first()
            return user

    async def get_user_by_username(self, username: str):
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).filter_by(username=username))
            user = result.scalars().first()
            return user

    async def create_dice_game(self, creator_id: int, bet: float, max_players: int, 
                             message_id: int = None, creator_name: str = None, 
                             creator_username: str = None):
        async with AsyncSessionLocal() as session:
            async with session.begin():
                game = DiceGame(
                    creator_id=creator_id,
                    creator_name=creator_name,
                    creator_username=creator_username,
                    bet=bet,
                    max_players=max_players,
                    message_id=message_id,
                    players=json.dumps([{"id": creator_id, "name": creator_name, "username": creator_username}]),
                    ready_players=json.dumps({})
                )
                session.add(game)
                await session.flush()
                return game.game_number

    async def get_dice_game(self, game_number: int):
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(DiceGame).filter_by(game_number=game_number))
            return result.scalars().first()

    async def update_dice_game(self, game_number: int, **kwargs):
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(DiceGame).filter_by(game_number=game_number))
            game = result.scalars().first()
            if game:
                for key, value in kwargs.items():
                    setattr(game, key, value)
                await session.commit()
                return True
            return False

    async def delete_dice_game(self, game_number: int):
        async with AsyncSessionLocal() as session:
            await session.execute(delete(DiceGame).where(DiceGame.game_number == game_number))
            await session.commit()