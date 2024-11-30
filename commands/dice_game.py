import sqlite3
import random
import json
from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from scripts.active_check import check_bot_active
from scripts.logger import log_command
from scripts.database import Database

router = Router()

def get_game_keyboard(is_creator: bool = False) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="👥 Присоединиться", callback_data="join")],
        [
            InlineKeyboardButton(text="▶️ Начать игру", callback_data="start_game"),
            InlineKeyboardButton(text="❌ Покинуть", callback_data="leave")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

async def get_lobby_text(game):
    return (f"🎲 Игра №{game.game_number}\n"
            f"👥 Участники: {len(json.loads(game.players))}/{game.max_players}\n"
            f"💰 Ставка: {game.bet} GW\n"
            f"Создатель: @{game.creator_username}")

async def get_confirmation_text(game):
    players = json.loads(game.players)
    ready_players = json.loads(game.ready_players)
    text = "👥 Участники:\n"
    for player in players:
        status = f"✅ [{ready_players.get(str(player['id']), '?')}]" if str(player['id']) in ready_players else "⏳"
        text += f"• @{player['username']} {status}\n"
    text += "\nОтправьте 🎲 в ответ на это сообщение, чтобы бросить кубик"
    return text

@router.message(Command("dice"))
@check_bot_active
async def dice_command_handler(message: Message):
    try:
        args = message.text.split()[1:]
        if len(args) != 2:
            await message.reply("❌ Использование: /dice <ставка> <макс. игроков>")
            return

        bet = float(args[0])
        max_players = int(args[1])

        if bet <= 0 or max_players < 2:
            await message.reply("❌ Некорректные параметры игры")
            return

        user_score = await Database.get_user_score(message.from_user.id)
        if user_score is None or user_score < bet:
            await message.reply("❌ Недостаточно средств")
            return

        game_number = await Database.create_dice_game(
            creator_id=message.from_user.id,
            creator_name=message.from_user.full_name,
            creator_username=message.from_user.username,
            bet=bet,
            max_players=max_players
        )

        lobby_message = await message.reply(
            await get_lobby_text(await Database.get_dice_game(game_number)),
            reply_markup=get_game_keyboard()
        )

        await Database.update_dice_game(game_number, message_id=lobby_message.message_id)
        await Database.update_score(message.from_user.id, -bet)

    except ValueError:
        await message.reply("❌ Некорректные параметры игры")
    except Exception as e:
        print(f"Error in dice_command_handler: {e}")
        await message.reply("❌ Произошла ошибка при создании игры")

@router.callback_query(F.data == "join")
async def join_callback(callback: CallbackQuery):
    try:
        game = await Database.get_dice_game(callback.message.message_id)
        if not game:
            await callback.answer("❌ Игра не найдена")
            return

        if game.is_started:
            await callback.answer("❌ Игра уже началась")
            return

        players = json.loads(game.players)
        if len(players) >= game.max_players:
            await callback.answer("❌ Достигнуто максимальное количество игроков")
            return

        player = next((p for p in players if p['id'] == callback.from_user.id), None)
        if player:
            await callback.answer("❌ Вы уже в игре")
            return

        user_score = await Database.get_user_score(callback.from_user.id)
        if user_score is None or user_score < game.bet:
            await callback.answer("❌ Недостаточно средств")
            return

        players.append({
            "id": callback.from_user.id,
            "username": callback.from_user.username
        })

        await Database.update_dice_game(game.game_number, players=json.dumps(players))
        await Database.update_score(callback.from_user.id, -game.bet)

        await callback.message.edit_text(
            await get_lobby_text(await Database.get_dice_game(game.game_number)),
            reply_markup=get_game_keyboard()
        )
        await callback.answer()

    except Exception as e:
        print(f"Error in join_callback: {e}")
        await callback.answer("❌ Произошла ошибка")

@router.callback_query(F.data == "leave")
async def leave_callback(callback: CallbackQuery):
    try:
        game = await Database.get_dice_game(callback.message.message_id)
        if not game or game.is_started:
            await callback.answer("❌ Невозможно покинуть игру")
            return

        players = json.loads(game.players)
        player = next((p for p in players if p['id'] == callback.from_user.id), None)
        if not player:
            await callback.answer("❌ Вы не участвуете в игре")
            return

        players.remove(player)
        if not players:
            await Database.delete_dice_game(game.game_number)
            await callback.message.delete()
        else:
            await Database.update_dice_game(game.game_number, players=json.dumps(players))
            await callback.message.edit_text(
                await get_lobby_text(await Database.get_dice_game(game.game_number)),
                reply_markup=get_game_keyboard()
            )

        await Database.update_score(callback.from_user.id, game.bet)
        await callback.answer()

    except Exception as e:
        print(f"Error in leave_callback: {e}")
        await callback.answer("❌ Произошла ошибка")

@router.callback_query(F.data == "start_game")
async def start_game_callback(callback: CallbackQuery):
    try:
        game = await Database.get_dice_game(callback.message.message_id)
        if not game or game.is_started:
            await callback.answer("❌ Невозможно начать игру")
            return

        if callback.from_user.id != game.creator_id:
            await callback.answer("❌ Только создатель может начать игру")
            return

        players = json.loads(game.players)
        if len(players) < 2:
            await callback.answer("❌ Недостаточно игроков")
            return

        await Database.update_dice_game(game.game_number, 
                                is_started=1,
                                is_ready_check=1)

        confirmation_message = await callback.message.reply(
            await get_confirmation_text(await Database.get_dice_game(game.game_number))
        )
        await callback.answer()

    except Exception as e:
        print(f"Error in start_game_callback: {e}")
        await callback.answer("❌ Произошла ошибка")

@router.message(F.dice)
async def handle_dice(message: Message):
    try:
        if not message.reply_to_message:
            return

        game = await Database.get_dice_game(message.reply_to_message.message_id)
        if not game or not game.is_ready_check:
            return

        players = json.loads(game.players)
        if not any(p['id'] == message.from_user.id for p in players):
            await message.reply("❌ Вы не участвуете в этой игре")
            return

        ready_players = json.loads(game.ready_players)
        if str(message.from_user.id) in ready_players:
            await message.reply("❌ Вы уже бросили кубик")
            return

        ready_players[str(message.from_user.id)] = message.dice.value
        await Database.update_dice_game(game.game_number, ready_players=json.dumps(ready_players))

        if len(ready_players) == len(players):
            max_roll = max(ready_players.values())
            winners = [p for p in players if ready_players[str(p['id'])] == max_roll]
            
            total_prize = game.bet * len(players)
            fee = total_prize * 0.05
            prize_pool = total_prize - fee
            prize_per_winner = prize_pool / len(winners)

            for winner in winners:
                await Database.update_score(winner['id'], prize_per_winner)

            await Database.update_dice_game(
                game.game_number,
                is_ready_check=0,
                total_prize=prize_pool,
                winners=json.dumps(winners)
            )

            winners_text = "\n".join(f"• @{w['username']} (🎲{ready_players[str(w['id'])]})" for w in winners)
            result_text = (
                f"🎲 Игра №{game.game_number} завершена!\n\n"
                f"💰 Призовой фонд: {prize_pool}\n"
                f"👑 Победители:\n{winners_text}\n"
                f"💎 Выигрыш каждого: {prize_per_winner}"
            )
            await message.reply(result_text)

        else:
            await message.reply_to_message.edit_text(
                await get_confirmation_text(await Database.get_dice_game(game.game_number))
            )

    except Exception as e:
        print(f"Error in handle_dice: {e}")
        await message.reply("❌ Произошла ошибка")

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
