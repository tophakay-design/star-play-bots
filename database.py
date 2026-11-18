import aiosqlite
from datetime import datetime, timedelta

DB_PATH = "bot.db"


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                balance INTEGER DEFAULT 0,
                total_bet INTEGER DEFAULT 0,
                total_win INTEGER DEFAULT 0,
                games_played INTEGER DEFAULT 0,
                games_won INTEGER DEFAULT 0,
                last_bonus TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS deposits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount INTEGER,
                method TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                game TEXT,
                bet INTEGER,
                result TEXT,
                win INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()


async def get_user(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        return await cur.fetchone()


async def create_user(user_id, username):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)",
            (user_id, username)
        )
        await db.commit()


async def add_balance(user_id, amount):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET balance = balance + ? WHERE user_id = ?",
            (amount, user_id)
        )
        await db.commit()


async def add_deposit(user_id, amount, method):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO deposits (user_id, amount, method) VALUES (?, ?, ?)",
            (user_id, amount, method)
        )
        await db.commit()


async def add_game(user_id, game, bet, result, win):
    """win — чистый результат (может быть отрицательным)"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO games (user_id, game, bet, result, win) VALUES (?, ?, ?, ?, ?)",
            (user_id, game, bet, result, win)
        )
        await db.execute("""
            UPDATE users SET
                total_bet = total_bet + ?,
                total_win = total_win + ?,
                games_played = games_played + 1,
                games_won = games_won + ?
            WHERE user_id = ?
        """, (bet, max(win, 0), 1 if win > 0 else 0, user_id))
        await db.commit()


async def get_deposits(user_id, limit=10):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM deposits WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit)
        )
        return await cur.fetchall()


async def get_games(user_id, limit=10):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM games WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit)
        )
        return await cur.fetchall()


async def get_stats(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = await cur.fetchone()

        # любимая игра
        cur = await db.execute("""
            SELECT game, COUNT(*) as cnt FROM games
            WHERE user_id = ? GROUP BY game ORDER BY cnt DESC LIMIT 1
        """, (user_id,))
        fav = await cur.fetchone()

        # самая крупная победа
        cur = await db.execute(
            "SELECT MAX(win) as max_win FROM games WHERE user_id = ?", (user_id,)
        )
        max_win = await cur.fetchone()

        return {
            "user": user,
            "favorite": fav["game"] if fav else None,
            "max_win": max_win["max_win"] if max_win and max_win["max_win"] else 0,
        }


async def can_claim_bonus(user_id):
    """Возвращает (можно_ли, сколько_ждать_секунд)"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT last_bonus FROM users WHERE user_id = ?", (user_id,))
        row = await cur.fetchone()
        if not row or not row["last_bonus"]:
            return True, 0
        last = datetime.fromisoformat(row["last_bonus"])
        diff = datetime.now() - last
        if diff >= timedelta(hours=24):
            return True, 0
        return False, int((timedelta(hours=24) - diff).total_seconds())


async def claim_bonus(user_id, amount):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET balance = balance + ?, last_bonus = ? WHERE user_id = ?",
            (amount, datetime.now().isoformat(), user_id)
        )
        await db.commit()