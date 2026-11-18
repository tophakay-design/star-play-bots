import asyncio
import logging
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, LabeledPrice
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import (
    init_db, get_user, create_user, add_balance, add_deposit,
    add_game, get_deposits, get_games, get_stats,
    can_claim_bonus, claim_bonus
)
from keyboards import (
    main_menu, games_menu, deposit_menu,
    bet_keyboard, back_to_games, profile_keyboard
)
from games import DICE_EMOJI, GAME_NAMES, calculate_result

BOT_TOKEN = "ТВОЙ_ТОКЕН_ЗДЕСЬ"
MIN_BET = 1
MAX_BET = 2000
BONUS_AMOUNT = 50

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


class States(StatesGroup):
    waiting_bet = State()        # ждём свою ставку
    waiting_game = State()       # ставка введена — какую игру?
    waiting_deposit = State()    # своя сумма пополнения


# ---------- /start ----------
@dp.message(CommandStart())
async def cmd_start(message: Message):
    await create_user(message.from_user.id, message.from_user.username or "anon")
    await message.answer(
        f"🎉 Привет, <b>{message.from_user.first_name}</b>!\n\n"
        "🌟 Добро пожаловать в <b>STAR PLAY</b> — игровой бот со звёздами!\n\n"
        "💡 Что умею:\n"
        "  🎮 6 игр: 🎯 ⚽️ 🏀 🎰 🎲 🎳\n"
        "  💰 Ставки от 1 до 2000 ⭐\n"
        "  🎁 Ежедневный бонус\n"
        "  📊 Подробная статистика\n\n"
        "Выбирай раздел ниже 👇",
        reply_markup=main_menu,
        parse_mode="HTML"
    )


# ---------- ПРОФИЛЬ ----------
@dp.message(F.text == "👤 Профиль")
async def show_profile(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        return await message.answer("Нажми /start для начала 😉")

    text = (
        "╔══════════════════════╗\n"
        "   👤 <b>ТВОЙ ПРОФИЛЬ</b>\n"
        "╚══════════════════════╝\n\n"
        f"🆔 ID: <code>{user['user_id']}</code>\n"
        f"📛 Ник: @{user['username'] or '—'}\n"
        f"💎 Баланс: <b>{user['balance']} ⭐</b>\n"
        f"📅 Регистрация: {user['created_at'][:10]}\n\n"
        "📂 Нажми на кнопку ниже, чтобы посмотреть детали 👇"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=profile_keyboard())


@dp.callback_query(F.data == "prof_deposits")
async def prof_deposits(callback: CallbackQuery):
    deposits = await get_deposits(callback.from_user.id, limit=15)
    text = "📥 <b>История пополнений:</b>\n\n"
    if not deposits:
        text += "<i>Пока ни одного пополнения…</i>"
    else:
        for d in deposits:
            text += f"  ➕ +{d['amount']} ⭐ <i>({d['method']})</i>\n"
            text += f"      🕐 {d['created_at'][:16]}\n"
    await callback.message.edit_text(text, parse_mode="HTML",
                                     reply_markup=profile_keyboard())
    await callback.answer()


@dp.callback_query(F.data == "prof_games")
async def prof_games(callback: CallbackQuery):
    games = await get_games(callback.from_user.id, limit=15)
    text = "🎮 <b>Последние игры:</b>\n\n"
    if not games:
        text += "<i>Ты ещё не играл 🎲</i>"
    else:
        for g in games:
            emoji = "🟢" if g['win'] > 0 else "🔴"
            sign = "+" if g['win'] > 0 else ""
            text += (
                f"{emoji} {g['game']} | ставка {g['bet']} ⭐\n"
                f"   → {sign}{g['win']} ⭐ · 🕐 {g['created_at'][:16]}\n"
            )
    await callback.message.edit_text(text, parse_mode="HTML",
                                     reply_markup=profile_keyboard())
    await callback.answer()


@dp.callback_query(F.data == "prof_stats")
async def prof_stats(callback: CallbackQuery):
    await send_stats(callback.message, callback.from_user.id, edit=True)
    await callback.answer()


# ---------- СТАТИСТИКА ----------
@dp.message(F.text == "📊 Статистика")
async def stats_handler(message: Message):
    await send_stats(message, message.from_user.id)


async def send_stats(message, user_id, edit=False):
    s = await get_stats(user_id)
    u = s["user"]
    if not u:
        return

    played = u["games_played"]
    won = u["games_won"]
    winrate = (won / played * 100) if played else 0
    profit = u["total_win"] - u["total_bet"]

    text = (
        "╔══════════════════════╗\n"
        "   📊 <b>СТАТИСТИКА</b>\n"
        "╚══════════════════════╝\n\n"
        f"💎 Баланс: <b>{u['balance']} ⭐</b>\n"
        f"🎮 Сыграно игр: <b>{played}</b>\n"
        f"🏆 Побед: <b>{won}</b>  ·  📉 Поражений: <b>{played - won}</b>\n"
        f"🎯 Winrate: <b>{winrate:.1f}%</b>\n"
        f"💵 Всего поставлено: <b>{u['total_bet']} ⭐</b>\n"
        f"💰 Всего выиграно: <b>{u['total_win']} ⭐</b>\n"
        f"{'📈' if profit >= 0 else '📉'} Профит: <b>{profit:+d} ⭐</b>\n"
        f"🔥 Максимальный выигрыш: <b>{s['max_win']} ⭐</b>\n"
        f"⭐ Любимая игра: {s['favorite'] or '—'}\n"
    )

    if edit:
        await message.edit_text(text, parse_mode="HTML",
                                reply_markup=profile_keyboard())
    else:
        await message.answer(text, parse_mode="HTML")


# ---------- БОНУС ----------
@dp.message(F.text == "🎁 Бонус")
async def bonus_handler(message: Message):
    ok, wait = await can_claim_bonus(message.from_user.id)
    if ok:
        await claim_bonus(message.from_user.id, BONUS_AMOUNT)
        await message.answer(
            f"🎉 <b>Бонус получен!</b>\n\n"
            f"➕ Тебе начислено <b>{BONUS_AMOUNT} ⭐</b>\n"
            f"🕐 Возвращайся через 24 часа за новым бонусом!",
            parse_mode="HTML"
        )
    else:
        h = wait // 3600
        m = (wait % 3600) // 60
        await message.answer(
            f"⏳ <b>Бонус ещё не готов</b>\n\n"
            f"Следующий через: <b>{h} ч {m} мин</b>\n"
            f"🎁 Размер бонуса: <b>{BONUS_AMOUNT} ⭐</b>",
            parse_mode="HTML"
        )


# ---------- ПОПОЛНЕНИЕ ----------
@dp.message(F.text == "💰 Пополнить")
async def deposit_menu_handler(message: Message):
    await message.answer(
        "💰 <b>ПОПОЛНЕНИЕ БАЛАНСА</b>\n\n"
        "Выбери сумму или введи свою 👇\n"
        "⚠️ <i>Демо-режим: звёзды начисляются сразу</i>",
        reply_markup=deposit_menu,
        parse_mode="HTML"
    )
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✍️ Своя сумма", callback_data="dep_custom")]
    ])
    await message.answer("Или введи произвольную сумму:", reply_markup=kb)


@dp.callback_query(F.data.startswith("dep_") & ~F.data.contains("custom"))
async def process_deposit(callback: CallbackQuery):
    amount = int(callback.data.split("_")[1])
    await add_balance(callback.from_user.id, amount)
    await add_deposit(callback.from_user.id, amount, "Telegram Stars")
    await callback.answer(f"✅ +{amount} ⭐")
    await callback.message.answer(
        f"✅ <b>Баланс пополнен!</b>\n\n"
        f"➕ Зачислено: <b>{amount} ⭐</b>",
        parse_mode="HTML"
    )


@dp.callback_query(F.data == "dep_custom")
async def dep_custom(callback: CallbackQuery, state: FSMContext):
    await state.set_state(States.waiting_deposit)
    await callback.message.answer("✍️ Введи сумму пополнения (целое число ⭐):")
    await callback.answer()


@dp.message(States.waiting_deposit)
async def dep_custom_amount(message: Message, state: FSMContext):
    try:
        amount = int(message.text.strip())
        if amount <= 0 or amount > 100000:
            raise ValueError
    except ValueError:
        return await message.answer("❌ Введи корректное число от 1 до 100000")
    await add_balance(message.from_user.id, amount)
    await add_deposit(message.from_user.id, amount, "Telegram Stars")
    await state.clear()
    await message.answer(
        f"✅ <b>Баланс пополнен!</b>\n\n➕ Зачислено: <b>{amount} ⭐</b>",
        parse_mode="HTML"
    )


# ---------- ИГРЫ ----------
@dp.message(F.text == "🎮 Игры")
async def games_menu_handler(message: Message):
    user = await get_user(message.from_user.id)
    await message.answer(
        "🎮 <b>ИГРОВОЕ МЕНЮ</b>\n\n"
        f"💎 Баланс: <b>{user['balance']} ⭐</b>\n"
        f"🎯 Ставки: от <b>{MIN_BET}</b> до <b>{MAX_BET}</b> ⭐\n\n"
        "Выбери игру 👇",
        reply_markup=games_menu,
        parse_mode="HTML"
    )


@dp.callback_query(F.data == "to_games")
async def to_games(callback: CallbackQuery):
    user = await get_user(callback.from_user.id)
    await callback.message.edit_text(
        "🎮 <b>ИГРОВОЕ МЕНЮ</b>\n\n"
        f"💎 Баланс: <b>{user['balance']} ⭐</b>\n"
        f"🎯 Ставки: от <b>{MIN_BET}</b> до <b>{MAX_BET}</b> ⭐\n\n"
        "Выбери игру 👇",
        reply_markup=games_menu, parse_mode="HTML"
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("game_"))
async def choose_bet(callback: CallbackQuery, state: FSMContext):
    game = callback.data.replace("game_", "")
    user = await get_user(callback.from_user.id)

    if user['balance'] < MIN_BET:
        return await callback.answer("❌ Недостаточно звёзд!", show_alert=True)

    await state.update_data(game=game)
    await state.set_state(States.waiting_bet)

    await callback.message.edit_text(
        f"{GAME_NAMES[game]}\n\n"
        f"💎 Баланс: <b>{user['balance']} ⭐</b>\n\n"
        f"🎯 Выбери ставку (от {MIN_BET} до {MAX_BET} ⭐):",
        parse_mode="HTML",
        reply_markup=bet_keyboard()
    )
    await callback.answer()


@dp.callback_query(F.data == "bet_custom", States.waiting_bet)
async def custom_bet(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        f"✍️ Введи ставку целым числом (от {MIN_BET} до {MAX_BET} ⭐):"
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("bet_") & ~F.data.contains("custom"), States.waiting_bet)
async def start_game_cb(callback: CallbackQuery, state: FSMContext):
    bet = int(callback.data.split("_")[1])
    data = await state.get_data()
    game = data.get("game")
    await state.clear()
    await callback.message.delete()
    await run_game(callback.message, callback.from_user.id, game, bet)


@dp.message(States.waiting_bet, F.text)
async def custom_bet_message(message: Message, state: FSMContext):
    try:
        bet = int(message.text.strip())
        if not (MIN_BET <= bet <= MAX_BET):
            raise ValueError
    except ValueError:
        return await message.answer(f"❌ Ставка должна быть от {MIN_BET} до {MAX_BET} ⭐")
    data = await state.get_data()
    game = data.get("game")
    await state.clear()
    await run_game(message, message.from_user.id, game, bet)


async def run_game(message: Message, user_id: int, game: str, bet: int):
    user = await get_user(user_id)
    if user['balance'] < bet:
        return await message.answer(f"❌ Недостаточно звёзд! Нужно {bet} ⭐")

    # списываем ставку
    await add_balance(user_id, -bet)

    await message.answer(
        f"{GAME_NAMES[game]}\n💵 Ставка: <b>{bet} ⭐</b>\n\n🎲 Бросаем…",
        parse_mode="HTML"
    )

    dice_msg = await bot.send_dice(chat_id=message.chat.id, emoji=DICE_EMOJI[game])
    await asyncio.sleep(4)

    value = dice_msg.dice.value
    result_text, win, mult = calculate_result(game, value, bet)

    # начисляем чистый выигрыш обратно
    if win > 0:
        await add_balance(user_id, win + bet)  # возврат ставки + прибыль
    # win < 0 — ставка уже списана и не возвращается

    await add_game(user_id, GAME_NAMES[game], bet, result_text, win)

    user = await get_user(user_id)
    footer = (
        f"\n\n{'🎉' if win > 0 else '😢'} "
        f"Итог: <b>{win:+d} ⭐</b>\n"
        f"💎 Баланс: <b>{user['balance']} ⭐</b>"
    )
    await message.answer(result_text + footer, parse_mode="HTML",
                         reply_markup=back_to_games())


# ---------- НАЗАД ----------
@dp.callback_query(F.data == "back_main")
async def back_main(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.message.answer("🏠 Главное меню 👇", reply_markup=main_menu)
    await callback.answer()


# ---------- ЗАПУСК ----------
async def main():
    logging.basicConfig(level=logging.INFO)
    await init_db()
    print("🚀 Бот STAR PLAY запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())