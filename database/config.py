# database/config.py
"""
Centralized configuration for the database.
"""
import threading

# --- Centralized Configuration ---

# The file path for the SQLite database.
DB_PATH = 'bantaytubig.db' 

# A thread lock to prevent race conditions during concurrent database writes.
DB_LOCK = threading.Lock()