import sqlite3
import random
from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from scripts.active_check import is_bot_active
from scripts.logger import log_command

router = Router()

active_games = {}
game_counter = 0

class DiceGame:
    def __init__(self, creator_id, bet, max_players, message_id=None, creator_name=None, creator_username=None):
        global game_counter
        game_counter += 1
        self.game_number = game_counter
        self.creator_id = creator_id
        self.creator_name = creator_name
        self.creator_username = creator_username
        self.bet = bet
        self.max_players = max_players
        self.players = [(creator_id, creator_name, creator_username)]
        self.ready_players = {}
        self.is_started = False
        self.is_ready_check = False
        self.results = {}
        self.message_id = message_id
        self.lobby_message = None
        self.confirmation_message = None

    def add_player(self, player_id, player_name, player_username):
        if len(self.players) < self.max_players and player_id not in [p[0] for p in self.players]:
            if player_id != self.creator_id:
                self.players.append((player_id, player_name, player_username))
                return True
        return False

    def remove_player(self, player_id):
        if player_id in [p[0] for p in self.players]:
            self.players = [p for p in self.players if p[0] != player_id]
            if player_id in self.ready_players:
                del self.ready_players[player_id]
            return True
        return False

    def mark_ready(self, player_id, dice_value):
        if player_id in [p[0] for p in self.players]:
            self.ready_players[player_id] = dice_value
            return True
        return False

    def is_everyone_ready(self):
        return len(self.ready_players) == len(self.players)

    def get_winner(self):
        if not self.ready_players:
            return []
        max_roll = max(self.ready_players.values())
        winners = [(pid, pname, pusername) for pid, pname, pusername in self.players 
                  if pid in self.ready_players and self.ready_players[pid] == max_roll]
        return winners

    def get_total_prize(self):
        total_bet = self.bet * len(self.players)
        fee = total_bet * 0.05  # 5% комиссия
        return total_bet - fee

    def get_lobby_text(self):
        return (f"🎲 Игра №{self.game_number}\n"
                f"👥 Участники: {len(self.players)}/{self.max_players}\n"
                f"💰 Ставка: {self.bet} GW\n"
                f"Создатель: @{self.creator_username}")

    def get_confirmation_text(self):
        text = "👥 Участники:\n"
        for player_id, _, username in self.players:
            status = f"✅ [{self.ready_players[player_id]}]" if player_id in self.ready_players else "⏳"
            text += f"• @{username} {status}\n"
        text += "\nОтправьте 🎲 в ответ на это сообщение, чтобы бросить кубик"
        return text

def get_game_keyboard(is_creator: bool = False) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="👥 Присоединиться", callback_data="join")],
        [
            InlineKeyboardButton(text="▶️ Начать игру", callback_data="start_game"),
            InlineKeyboardButton(text="❌ Покинуть", callback_data="leave")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

async def check_score(user_id: int, amount: int) -> bool:
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT score FROM users WHERE uid = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result and result[0] >= amount

async def update_score(user_id: int, amount: int):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET score = score + ? WHERE uid = ?', (amount, user_id))
    conn.commit()
    conn.close()

async def get_user_name(user_id: int) -> str:
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT username FROM users WHERE uid = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else "Unknown"

async def check_user_exists(user_id: int) -> bool:
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT uid FROM users WHERE uid = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

@router.message(Command("dice"))
async def dice_command_handler(message: Message) -> None:
    chat_id = str(message.chat.id)
    
    if not await is_bot_active(chat_id):
        await message.reply("❗️ Бот не активирован в этом чате.")
        return

    args = message.text.split()[1:] if message.text else []
    if len(args) != 2:
        await message.reply("❗️ Использование: /dice [максимум игроков] [ставка]")
        return

    try:
        max_players = int(args[0])
        bet = int(args[1])

        if max_players < 2:
            await message.reply("❗️ Минимальное количество игроков: 2")
            return
        
        if bet < 1:
            await message.reply("❗️ Минимальная ставка: 1 GW")
            return

        if not await check_score(message.from_user.id, bet):
            await message.reply("❗️ У вас недостаточно GW для такой ставки!")
            return

        # Списываем ставку у создателя
        await update_score(message.from_user.id, -bet)

        game = DiceGame(
            creator_id=message.from_user.id,
            bet=bet,
            max_players=max_players,
            creator_name=message.from_user.full_name,
            creator_username=message.from_user.username
        )

        keyboard = get_game_keyboard(is_creator=True)
        game_msg = await message.reply(
            game.get_lobby_text(),
            reply_markup=keyboard
        )
        
        game.lobby_message = game_msg.message_id
        active_games[game.game_number] = game
        await log_command(message, message.text)

    except ValueError:
        await message.reply("❗️ Ставка и максимум игроков должны быть числами!")
        return

@router.callback_query(F.data == "ready")
async def ready_callback(callback: CallbackQuery):
    game_msg = callback.message
    for game_number, game in active_games.items():
        if game.lobby_message == game_msg.message_id:
            if not game.is_ready_check:
                game.is_ready_check = True
                dice_value = random.randint(1, 6)
                game.mark_ready(callback.from_user.id, dice_value)
                
                player_name = callback.from_user.full_name
                await callback.message.edit_text(
                    game.get_confirmation_text(),
                    reply_markup=game_msg.reply_markup
                )
                
                if game.is_everyone_ready():
                    winners = game.get_winner()
                    prize_per_winner = game.get_total_prize() // len(winners)
                    commission = game.get_total_prize() % len(winners)
                    
                    for winner_id, _, _ in winners:
                        await update_score(winner_id, prize_per_winner)
                    
                    result_text = (
                        f"{game_msg.text}\n\n"
                        f"🏆 Победители:\n"
                    )
                    for winner_id, winner_name, _ in winners:
                        result_text += f"• {winner_name} (выигрыш: {prize_per_winner})\n"
                    
                    await callback.message.edit_text(
                        result_text,
                        reply_markup=None
                    )
                    
                    del active_games[game_number]
            break
    await callback.answer()

@router.callback_query(F.data == "cancel")
async def cancel_callback(callback: CallbackQuery):
    game_msg = callback.message
    for game_number, game in active_games.items():
        if game.lobby_message == game_msg.message_id:
            if callback.from_user.id == game.creator_id:
                await callback.message.edit_text(
                    f"{game_msg.text}\n\n❌ Игра отменена создателем.",
                    reply_markup=None
                )
                del active_games[game_number]
            break
    await callback.answer()

@router.callback_query(F.data == "join")
async def join_callback(callback: CallbackQuery):
    game_msg = callback.message
    
    # Проверяем наличие аккаунта
    if not await check_user_exists(callback.from_user.id):
        await callback.answer("❗️ У вас нет аккаунта! Создайте аккаунт командой /invite", show_alert=True)
        return
        
    # Проверяем достаточно ли GW для ставки
    for game_number, game in active_games.items():
        if game.lobby_message == game_msg.message_id:
            if not await check_score(callback.from_user.id, game.bet):
                await callback.answer(f"❗️ У вас недостаточно GW для ставки {game.bet}!", show_alert=True)
                return
                
            if game.add_player(callback.from_user.id, callback.from_user.full_name, callback.from_user.username):
                # Списываем ставку у игрока
                await update_score(callback.from_user.id, -game.bet)
                
                await callback.message.edit_text(
                    game.get_lobby_text(),
                    reply_markup=game_msg.reply_markup
                )
                
                # Если достигнуто максимальное количество игроков, запускаем игру
                if len(game.players) >= game.max_players:
                    confirmation_msg = await callback.message.reply(
                        game.get_confirmation_text(),
                        reply_markup=None
                    )
                    game.confirmation_message = confirmation_msg.message_id
                    await callback.answer("Игра автоматически запущена - набрано максимальное количество игроков!")
                else:
                    await callback.answer("Вы успешно присоединились к игре!")
            else:
                await callback.answer("Вы не можете присоединиться к этой игре.")
            break
    if not game_msg:
        await callback.answer("Игра не найдена.")

@router.callback_query(F.data == "leave")
async def leave_callback(callback: CallbackQuery):
    game_msg = callback.message
    for game_number, game in active_games.items():
        if game.lobby_message == game_msg.message_id:
            if game.remove_player(callback.from_user.id):
                await callback.message.edit_text(
                    game.get_lobby_text(),
                    reply_markup=game_msg.reply_markup
                )
            else:
                await callback.answer("Вы не можете покинуть игру, которую вы создали.")
            break
    await callback.answer()

@router.callback_query(F.data == "start_game")
async def start_game_callback(callback: CallbackQuery):
    game_msg = callback.message
    for game_number, game in active_games.items():
        if game.lobby_message == game_msg.message_id:
            if callback.from_user.id == game.creator_id:
                confirmation_msg = await callback.message.reply(
                    game.get_confirmation_text(),
                    reply_markup=None
                )
                game.confirmation_message = confirmation_msg.message_id
            else:
                await callback.answer("Только создатель игры может начать игру.")
            break
    await callback.answer()

@router.message(F.dice)
async def handle_dice(message: Message):
    if not message.reply_to_message:
        return

    for game_number, game in active_games.items():
        if game.confirmation_message == message.reply_to_message.message_id:
            if message.from_user.id in [p[0] for p in game.players]:
                if message.from_user.id not in game.ready_players:
                    game.mark_ready(message.from_user.id, message.dice.value)
                    
                    await message.reply_to_message.edit_text(
                        game.get_confirmation_text()
                    )

                    if game.is_everyone_ready():
                        winners = game.get_winner()
                        prize_per_winner = game.get_total_prize() // len(winners)

                        # Формируем текст с результатами
                        result_text = "🎲 Результаты игры:\n\n"
                        for player_id, _, username in game.players:
                            result_text += f"@{username}: {game.ready_players[player_id]}\n"
                        
                        if len(winners) > 1:
                            result_text += f"\n🏆 Ничья! Победители:\n"
                            for _, _, username in winners:
                                result_text += f"@{username}\n"
                        else:
                            _, _, winner_username = winners[0]
                            result_text += f"\n🏆 Победитель: @{winner_username}"
                        
                        result_text += f"\n💰 Выигрыш: {prize_per_winner} GW"

                        await message.reply_to_message.reply(result_text)

                        # Выдаем награду победителям
                        for winner_id, _, _ in winners:
                            await update_score(winner_id, prize_per_winner)

                        # Удаляем игру
                        del active_games[game_number]
                else:
                    await message.reply("❗️ Вы уже бросили кубик!")
            else:
                await message.reply("❗️ Вы не участвуете в этой игре!")
            break

async def init_game_history_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
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
    ''')
    conn.commit()
    conn.close()

async def log_game(game_number, creator_id, creator_name, bet, max_players, players, results, winners, prize_per_winner):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO game_history (
            game_number, creator_id, creator_name, bet, max_players,
            players, results, winners, prize_per_winner
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        game_number, creator_id, creator_name, bet, max_players,
        str(players), str(results), str(winners), prize_per_winner
    ))
    conn.commit()
    conn.close()
