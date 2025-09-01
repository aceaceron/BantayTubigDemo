# cleanup_data.py
import sqlite3
import os
from datetime import datetime, timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'bantaytubig.db')

def get_data_retention_days():
    """Gets the retention policy from the settings table."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = 'data_retention_days'")
    result = cursor.fetchone()
    conn.close()
    # Default to 365 days if not set
    return int(result[0]) if result else 365

def cleanup_old_data():
    """Deletes records from measurements and context tables older than the policy."""
    retention_days = get_data_retention_days()
    cutoff_date = datetime.now() - timedelta(days=retention_days)
    cutoff_timestamp = cutoff_date.strftime("%Y-%m-%d %H:%M:%S")

    print(f"Data retention policy: {retention_days} days.")
    print(f"Deleting records older than {cutoff_timestamp}...")

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Delete from measurements table
        cursor.execute("DELETE FROM measurements WHERE timestamp < ?", (cutoff_timestamp,))
        deleted_count = cursor.rowcount
        cursor.execute("DELETE FROM environmental_context WHERE measurement_id IN (SELECT id FROM measurements WHERE timestamp < ?)", (cutoff_timestamp,))

        conn.commit()
        conn.close()
        print(f"Successfully deleted {deleted_count} old measurement records.")
    except Exception as e:
        print(f"An error occurred during data cleanup: {e}")

if __name__ == "__main__":
    cleanup_old_data()