import sqlite3
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
import asyncio
from datetime import datetime

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

    def add_player(self, player_id, player_name, player_username):
        if len(self.players) < self.max_players and player_id not in [p[0] for p in self.players]:
            self.players.append((player_id, player_name, player_username))
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

def format_game_message(game):
    if not game.is_ready_check:
        return (
            f"🎲 Игра №{game.game_number}\n"
            f"👥 Участники: {len(game.players)}/{game.max_players}\n"
            f"💰 Ставка: {game.bet} GW\n"
            f"Создатель: @{game.creator_username or 'без_username'}"
        )
    else:
        players_status = ""
        for player_id, _, username in game.players:
            status = "✅" if player_id in game.ready_players else "⏳"
            dice_value = f" [🎲{game.ready_players.get(player_id, '?')}]" if player_id in game.ready_players else ""
            players_status += f"• @{username or 'без_username'} {status}{dice_value}\n"
        
        return (
            f"👥 Участники:\n{players_status}\n"
            "Отправьте 🎲 в ответ на это сообщение, чтобы бросить кубик"
        )

def format_results_message(game, winners, prize_per_winner, commission):
    results_text = ""
    for player_id, _, username in game.players:
        dice_value = game.ready_players.get(player_id, '?')
        results_text += f"@{username or 'без_username'}: 🎲{dice_value}\n"
    
    if len(winners) > 1:
        winners_text = "\n".join([f"@{w[2] or 'без_username'}" for w in winners])
        return (
            f"📊 Результат игры №{game.game_number}\n\n"
            f"💰 Общий выигрыш: {prize_per_winner + commission} GW\n"
            f"📊 Комиссия (5%): {commission} GW\n"
            f"💵 Чистый выигрыш: {prize_per_winner} GW\n\n"
            f"🌟 Игра: 🎲Кости\n\n"
            f"ℹ️ Результаты:\n{results_text}\n"
            f"🤝 Ничья! Победители:\n{winners_text}\n"
            f"💰 Каждый победитель получает: {prize_per_winner} GW"
        )
    else:
        winner_username = winners[0][2] if winners[0][2] else "без_username"
        return (
            f"📊 Результат игры №{game.game_number}\n\n"
            f"💰 Общий выигрыш: {prize_per_winner + commission} GW\n"
            f"📊 Комиссия (5%): {commission} GW\n"
            f"💵 Чистый выигрыш: {prize_per_winner} GW\n\n"
            f"🌟 Игра: 🎲Кости\n\n"
            f"ℹ️ Результаты:\n{results_text}\n"
            f"👑 Победитель: @{winner_username}"
        )

async def handle_ready_emoji(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.reply_to_message:
        return
        
    try:
        message_id = update.message.reply_to_message.message_id
        game = active_games.get(message_id)
        
        if not game or not game.is_ready_check:
            return
            
        user_id = update.message.from_user.id
        
        if user_id not in [p[0] for p in game.players]:
            return
            
        if user_id in game.ready_players:
            return
            
        dice_value = update.message.dice.value
        
        if game.mark_ready(user_id, dice_value):
            try:
                await asyncio.sleep(4)
                
                await update.message.reply_to_message.edit_text(
                    text=format_game_message(game),
                    reply_markup=get_game_keyboard()
                )
                
                if game.is_everyone_ready():
                    winners = game.get_winner()
                    prize_pool = game.bet * len(game.players)
                    commission = int(prize_pool * 0.05)
                    prize_per_winner = (prize_pool - commission) // len(winners)
                    
                    log_game(
                        game.game_number,
                        game.creator_id,
                        game.creator_name,
                        game.bet,
                        game.max_players,
                        game.players,
                        game.ready_players,
                        winners,
                        prize_per_winner
                    )
                    
                    for player_id, _, _ in game.players:
                        update_score(player_id, -game.bet)
                    
                    for winner_id, _, _ in winners:
                        update_score(winner_id, prize_per_winner)
                    
                    await update.message.reply_text(
                        format_results_message(game, winners, prize_per_winner, commission)
                    )
                    
                    del active_games[message_id]
                    
            except Exception as e:
                print(f"Error updating game state: {e}")
    
    except Exception as e:
        print(f"Error in handle_ready_emoji: {e}")

async def start_ready_check(game, query):
    game.is_ready_check = True
    await query.edit_message_text(
        format_game_message(game)
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        data = query.data
        message_id = query.message.message_id
        user_id = query.from_user.id
        game = active_games.get(message_id)
        
        if not game:
            await query.message.reply_text("❌ Игра не найдена!")
            return
            
        if data == "join":
            if user_id in [p[0] for p in game.players]:
                await query.message.reply_text("❌ Вы уже в игре!")
                return
                
            if len(game.players) >= game.max_players:
                await query.message.reply_text("❌ Игра уже заполнена!")
                return
                
            if game.is_started or game.is_ready_check:
                await query.message.reply_text("❌ Игра уже началась!")
                return
                
            if game.add_player(user_id, query.from_user.first_name, query.from_user.username):
                await query.edit_message_text(
                    text=format_game_message(game),
                    reply_markup=get_game_keyboard()
                )
                
                if len(game.players) >= game.max_players:
                    await start_ready_check(game, query)
                
            else:
                await query.message.reply_text("❌ Не удалось присоединиться к игре!")
                
        elif data == "leave":
            if user_id == game.creator_id:
                await query.message.reply_text("👋 Создатель покинул игру. Игра отменена!")
                del active_games[message_id]
                return
                
            if user_id not in [p[0] for p in game.players]:
                await query.message.reply_text("❌ Вы не в игре!")
                return
                
            game.players = [p for p in game.players if p[0] != user_id]
            await query.message.reply_text("👋 Вы покинули игру!")
            
            await query.edit_message_text(
                text=format_game_message(game),
                reply_markup=get_game_keyboard()
            )
                
        elif data == "start":
            if user_id != game.creator_id:
                await query.message.reply_text("❌ Только создатель может начать игру!")
                return
                
            if game.is_started or game.is_ready_check:
                await query.message.reply_text("❌ Игра уже началась!")
                return
                
            if len(game.players) < 2:  
                await query.message.reply_text("❌ Для начала игры нужно минимум 2 игрока!")
                return
                
            await start_ready_check(game, query)
            
    except Exception as e:
        await query.message.reply_text(f"❌ Произошла ошибка: {str(e)}")

def setup_handlers(app):
    init_game_history_db()
    app.add_handler(CommandHandler("dice", dice_command))
    app.add_handler(CommandHandler("history", history_command))
    app.add_handler(CommandHandler("all_games", all_games_command))  
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.Dice.DICE, handle_ready_emoji))

def get_game_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Присоединиться ", callback_data="join"),
            InlineKeyboardButton("Начать игру ", callback_data="start"),
        ],
        [InlineKeyboardButton("Покинуть ", callback_data="leave")]
    ])

def check_score(user_id, amount):
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT score FROM users WHERE uid = ?", (user_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0] >= amount:
            return True
        return False
    except sqlite3.Error:
        return False

def update_score(user_id, amount):
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET score = score + ? WHERE uid = ?", (amount, user_id))
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error:
        return False

def get_user_name(user_id):
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM users WHERE uid = ?", (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    except sqlite3.Error:
        return None

async def dice_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        args = context.args
        if len(args) != 2:
            await update.message.reply_text(
                "❌ Использование: /dice [количество игроков] [ставка]\n"
                "Пример: /dice 2 100"
            )
            return

        try:
            players = int(args[0])
            bet = int(args[1])
        except ValueError:
            await update.message.reply_text("❌ Количество игроков и ставка должны быть числами")
            return

        if players < 2:
            await update.message.reply_text("❌ Минимальное количество игроков: 2")
            return

        if bet <= 0:
            await update.message.reply_text("❌ Ставка должна быть положительным числом")
            return

        user = update.effective_user
        user_id = user.id
        username = user.username
        
        db_name = get_user_name(user_id)
        if not db_name:
            await update.message.reply_text("❌ Вы не зарегистрированы в системе!")
            return
        
        if not check_score(user_id, bet):
            await update.message.reply_text("❌ У вас недостаточно очков для такой ставки!")
            return

        if user_id in [game.creator_id for game in active_games.values()]:
            await update.message.reply_text("❌ Вы уже создали игру!")
            return

        message = await update.message.reply_text(
            "🎲 Создание игры...",
            reply_markup=get_game_keyboard()
        )

        game = DiceGame(user_id, bet, players, message.message_id, db_name, username)
        active_games[message.message_id] = game

        await message.edit_text(
            format_game_message(game),
            reply_markup=get_game_keyboard()
        )

    except Exception as e:
        await update.message.reply_text(f"❌ Произошла ошибка: {str(e)}")

async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT * FROM game_history 
        ORDER BY game_id DESC 
        LIMIT 5
        ''')
        
        games = cursor.fetchall()
        conn.close()
        
        if not games:
            await update.message.reply_text("📜 История игр пуста")
            return
            
        response = "📜 Последние 5 игр:\n\n"
        
        for game in games:
            (game_id, game_number, creator_id, creator_name, bet, max_players,
             start_time, end_time, players, results, winners, prize_per_winner) = game
            
            response += f"🎲 Игра №{game_number}\n"
            response += f"👤 Создатель: {creator_name}\n"
            response += f"💰 Ставка: {bet} GW\n"
            response += f"👥 Игроков: {max_players}\n"
            response += f"🕒 Время: {start_time}\n"
            response += f"💎 Приз: {prize_per_winner} GW\n"
            response += f"🏆 Победители: {winners}\n"
            response += "➖➖➖➖➖➖➖➖➖➖\n\n"
        
        await update.message.reply_text(response)
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при получении истории: {str(e)}")

async def all_games_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает список всех активных игр"""
    try:
        if not active_games:
            await update.message.reply_text("🎲 Нет активных игр")
            return

        games_list = []
        chat_id = update.effective_chat.id
        
        for message_id, game in active_games.items():
            if not game.is_ready_check:
                creator_username = game.creator_username or "без_username"
                message_link = f"https://t.me/c/{str(chat_id)[4:]}/{message_id}"
                games_list.append(
                    f"🎲 №{game.game_number} | {game.bet} GW @{creator_username} [*тык*]({message_link})"
                )

        if games_list:
            await update.message.reply_text(
                "\n".join(games_list),
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
        else:
            await update.message.reply_text("🎲 Нет активных игр в режиме ожидания")
            
    except Exception as e:
        print(f"Error in all_games_command: {e}")
        await update.message.reply_text("❌ Произошла ошибка при получении списка игр")

def init_game_history_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS game_history (
        game_id INTEGER PRIMARY KEY,
        game_number INTEGER,
        creator_id INTEGER,
        creator_name TEXT,
        bet INTEGER,
        max_players INTEGER,
        start_time TEXT,
        end_time TEXT,
        players TEXT,
        results TEXT,
        winners TEXT,
        prize_per_winner INTEGER
    )
    ''')
    
    conn.commit()
    conn.close()

def log_game(game_number, creator_id, creator_name, bet, max_players, players, results, winners, prize_per_winner):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    players_str = str([(p[0], p[1], p[2] if p[2] else "None") for p in players])
    results_str = str(results)
    winners_str = str([(w[0], w[1], w[2] if w[2] else "None") for w in winners])
    
    cursor.execute('''
    INSERT INTO game_history (
        game_number, creator_id, creator_name, bet, max_players,
        start_time, end_time, players, results, winners, prize_per_winner
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        game_number, creator_id, creator_name, bet, max_players,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        players_str, results_str, winners_str, prize_per_winner
    ))
    
    conn.commit()
    conn.close()
