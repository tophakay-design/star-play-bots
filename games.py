DICE_EMOJI = {
    "dart": "🎯",
    "football": "⚽️",
    "basket": "🏀",
    "slots": "🎰",
    "dice": "🎲",
    "bowling": "🎳",
}

GAME_NAMES = {
    "dart": "🎯 Дартс",
    "football": "⚽️ Футбол",
    "basket": "🏀 Баскетбол",
    "slots": "🎰 Слоты",
    "dice": "🎲 Кубик",
    "bowling": "🎳 Боулинг",
}


def calculate_result(game: str, value: int, bet: int):
    """
    Возвращает (текст, чистый_выигрыш, множитель)
    Чистый выигрыш: положительный = прибыль, отрицательный = проигрыш ставки.
    """

    if game == "dart":
        if value == 6:
            return "🎯 В яблочко! Идеально!", bet * 3, 3
        if value == 5:
            return "🎯 Почти в центр!", bet * 2, 2
        if value in (3, 4):
            return "🎯 Хороший бросок", bet, 1
        return "🎯 Мимо мишени", -bet, -1

    if game == "football":
        if value in (4, 5):
            return "⚽️ КРАСИВЫЙ ГОЛ!", bet * 3, 3
        if value == 3:
            return "⚽️ ГОЛ!", bet * 2, 2
        return "⚽️ Вратарь поймал", -bet, -1

    if game == "basket":
        if value == 5:
            return "🏀 Чистый трёхочковый!", bet * 3, 3
        if value == 4:
            return "🏀 Попал в кольцо!", bet * 2, 2
        return "🏀 Промах", -bet, -1

    if game == "slots":
        if value == 64:
            return "🎰 💥💥💥 ДЖЕКПОТ 777! 💥💥💥", bet * 10, 10
        if value in (1, 22, 43):
            return "🎰 🍒 Три в ряд!", bet * 3, 3
        return "🎰 Не повезло…", -bet, -1

    if game == "dice":
        if value == 6:
            return "🎲 Шестёрка! Отлично!", bet * 3, 3
        if value in (4, 5):
            return "🎲 Удачный бросок", bet * 2, 2
        return "🎲 Неудача", -bet, -1

    if game == "bowling":
        if value == 6:
            return "🎳 🎯 СТРАЙК! Все сбито!", bet * 3, 3
        if value in (4, 5):
            return "🎳 Хороший бросок", bet * 2, 2
        return "🎳 Мимо дорожки", -bet, -1

    return "❓ Ошибка", 0, 0