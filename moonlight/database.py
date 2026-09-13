import sqlite3
import os
import time

START_BALANCE = 1000

# Persistent volume on Railway — falls back to local for dev
DB_PATH = "/data/moonlight.db" if os.path.isdir("/data") else "moonlight.db"
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
print(f"📦 Database: {os.path.abspath(DB_PATH)}")


# ---------- SCHEMA SETUP ----------

def _setup():
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id     INTEGER PRIMARY KEY,
        balance     INTEGER DEFAULT 1000,
        last_daily  INTEGER DEFAULT 0
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS clans (
        id        INTEGER PRIMARY KEY AUTOINCREMENT,
        name      TEXT UNIQUE,
        leader_id INTEGER,
        balance   INTEGER DEFAULT 0,
        level     INTEGER DEFAULT 1
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS clan_members (
        user_id INTEGER UNIQUE,
        clan_id INTEGER,
        role    TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_messages (
        user_id      INTEGER PRIMARY KEY,
        count        INTEGER DEFAULT 0
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_voice (
        user_id INTEGER PRIMARY KEY,
        seconds INTEGER DEFAULT 0
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS mod_actions (
        user_id INTEGER PRIMARY KEY,
        kicks   INTEGER DEFAULT 0,
        bans    INTEGER DEFAULT 0
    )
    """)

    # Tracks when the message leaderboard was last wiped
    cur.execute("""
    CREATE TABLE IF NOT EXISTS meta (
        key   TEXT PRIMARY KEY,
        value TEXT
    )
    """)

    # Seed the last_reset time if it doesn't exist yet
    cur.execute(
        "INSERT OR IGNORE INTO meta (key, value) VALUES ('last_reset', ?)",
        (str(int(time.time())),)
    )

    conn.commit()

_setup()


# ---------- HELPERS ----------

def _ensure_user(cur: sqlite3.Cursor, user_id: int) -> None:
    """Insert a user row with defaults if they don't exist yet."""
    cur.execute(
        "INSERT OR IGNORE INTO users (user_id, balance, last_daily) VALUES (?, ?, 0)",
        (user_id, START_BALANCE)
    )


# ---------- BALANCE ----------

def get_balance(user_id: int) -> int:
    cur = conn.cursor()
    _ensure_user(cur, user_id)
    conn.commit()
    cur.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    return cur.fetchone()[0]


def set_balance(user_id: int, amount: int) -> None:
    cur = conn.cursor()
    _ensure_user(cur, user_id)
    cur.execute(
        "UPDATE users SET balance = ? WHERE user_id = ?",
        (amount, user_id)
    )
    conn.commit()


def get_top_balances(limit: int = 10) -> list[tuple]:
    cur = conn.cursor()
    cur.execute(
        "SELECT user_id, balance FROM users ORDER BY balance DESC LIMIT ?",
        (limit,)
    )
    return cur.fetchall()


# ---------- DAILY ----------

def get_last_daily(user_id: int) -> int:
    cur = conn.cursor()
    _ensure_user(cur, user_id)
    conn.commit()
    cur.execute("SELECT last_daily FROM users WHERE user_id = ?", (user_id,))
    return cur.fetchone()[0]


def set_daily(user_id: int, timestamp: int) -> None:
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET last_daily = ? WHERE user_id = ?",
        (timestamp, user_id)
    )
    conn.commit()


# ---------- STATISTICS ----------

def add_message(user_id: int) -> None:
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO user_messages (user_id, count) VALUES (?, 1) "
        "ON CONFLICT(user_id) DO UPDATE SET count = count + 1",
        (user_id,)
    )
    conn.commit()


def add_voice_time(user_id: int, seconds: int) -> None:
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO user_voice (user_id, seconds) VALUES (?, ?) "
        "ON CONFLICT(user_id) DO UPDATE SET seconds = seconds + ?",
        (user_id, seconds, seconds)
    )
    conn.commit()


def get_user_activity(user_id: int) -> tuple[int, int]:
    cur = conn.cursor()

    cur.execute("SELECT count FROM user_messages WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    messages = row[0] if row else 0

    cur.execute("SELECT seconds FROM user_voice WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    voice = row[0] if row else 0

    return messages, voice


def get_message_leaderboard(limit: int = 10) -> list[tuple]:
    cur = conn.cursor()
    cur.execute(
        "SELECT user_id, count FROM user_messages ORDER BY count DESC LIMIT ?",
        (limit,)
    )
    return cur.fetchall()


def get_voice_leaderboard(limit: int = 10) -> list[tuple]:
    cur = conn.cursor()
    cur.execute(
        "SELECT user_id, seconds FROM user_voice ORDER BY seconds DESC LIMIT ?",
        (limit,)
    )
    return cur.fetchall()


# ---------- RESET ----------

def reset_message_counts() -> None:
    """Wipe all message counts and update the last_reset timestamp."""
    cur = conn.cursor()
    cur.execute("UPDATE user_messages SET count = 0")
    cur.execute(
        "INSERT OR REPLACE INTO meta (key, value) VALUES ('last_reset', ?)",
        (str(int(time.time())),)
    )
    conn.commit()


def get_last_reset() -> int:
    """Returns the Unix timestamp of the last leaderboard reset."""
    cur = conn.cursor()
    cur.execute("SELECT value FROM meta WHERE key = 'last_reset'")
    row = cur.fetchone()
    return int(row[0]) if row else 0