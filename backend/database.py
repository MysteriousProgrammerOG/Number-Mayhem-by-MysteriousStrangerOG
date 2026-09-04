# database.py
# SQLite persistence layer for Number Mayhem.
# This module handles all database operations.
# It is designed so it can be replaced with PostgreSQL later
# without changing the game logic in other files.

import json
import sqlite3
from pathlib import Path

# The database file lives in the project root (one level up from backend/)
DB_PATH = Path(__file__).resolve().parent.parent / "players.db"


def get_connection():
    """Create a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Allows accessing columns by name
    return conn


def init_db():
    """Create the players table if it doesn't exist."""
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY,
            data TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def load_player_data():
    """Load the single player's data from the database.
    Returns None if no player exists yet.
    """
    init_db()
    conn = get_connection()
    row = conn.execute("SELECT data FROM players WHERE id = 1").fetchone()
    conn.close()

    if row is None:
        return None

    try:
        return json.loads(row["data"])
    except json.JSONDecodeError:
        # Corrupted data - start fresh
        return None


def save_player_data(player_data):
    """Save the player's data to the database.
    Uses INSERT OR REPLACE so it works whether the player exists or not.
    """
    init_db()
    conn = get_connection()
    conn.execute(
        "INSERT OR REPLACE INTO players (id, data) VALUES (1, ?)",
        (json.dumps(player_data),)
    )
    conn.commit()
    conn.close()