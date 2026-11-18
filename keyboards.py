from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="👤 Профиль"), KeyboardButton(text="📊 Статистика")],
        [KeyboardButton(text="💰 Пополнить"), KeyboardButton(text="🎁 Бонус")],
        [KeyboardButton(text="🎮 Игры")]
    ],
    resize_keyboard=True
)

games_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🎯 Дартс", callback_data="game_dart"),
     InlineKeyboardButton(text="⚽️ Футбол", callback_data="game_football")],
    [InlineKeyboardButton(text="🏀 Баскетбол", callback_data="game_basket"),
     InlineKeyboardButton(text="🎰 Слоты", callback_data="game_slots")],
    [InlineKeyboardButton(text="🎲 Кубик", callback_data="game_dice"),
     InlineKeyboardButton(text="🎳 Боулинг", callback_data="game_bowling")],
    [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_main")]
])

deposit_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="⭐ 50", callback_data="dep_50"),
     InlineKeyboardButton(text="🌟 100", callback_data="dep_100")],
    [InlineKeyboardButton(text="💫 250", callback_data="dep_250"),
     InlineKeyboardButton(text="✨ 500", callback_data="dep_500")],
    [InlineKeyboardButton(text="💎 1000", callback_data="dep_1000"),
     InlineKeyboardButton(text="👑 2000", callback_data="dep_2000")]
])


def bet_keyboard() -> InlineKeyboardMarkup:
    """Быстрый выбор ставки + своё значение"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1 ⭐", callback_data="bet_1"),
         InlineKeyboardButton(text="10 ⭐", callback_data="bet_10"),
         InlineKeyboardButton(text="50 ⭐", callback_data="bet_50")],
        [InlineKeyboardButton(text="100 ⭐", callback_data="bet_100"),
         InlineKeyboardButton(text="500 ⭐", callback_data="bet_500"),
         InlineKeyboardButton(text="1000 ⭐", callback_data="bet_1000")],
        [InlineKeyboardButton(text="2000 ⭐", callback_data="bet_2000")],
        [InlineKeyboardButton(text="✍️ Своя ставка", callback_data="bet_custom")],
    ])


def back_to_games() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 К играм", callback_data="to_games")],
        [InlineKeyboardButton(text="🏠 В меню", callback_data="back_main")]
    ])


def profile_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📥 Пополнения", callback_data="prof_deposits"),
         InlineKeyboardButton(text="🎮 Игры", callback_data="prof_games")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="prof_stats")],
    ])