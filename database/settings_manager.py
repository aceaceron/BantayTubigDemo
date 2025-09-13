# database/settings_manager.py
import sqlite3
from .config import DB_PATH, DB_LOCK

def get_setting(key, default=None):
    """Fetches a single setting's value from the settings table."""
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else default

def update_setting(key, value):
    """Inserts or updates a setting in the settings table."""
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
        conn.commit()
        conn.close()