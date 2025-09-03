# database/maintenance.py
"""
Handles periodic database maintenance tasks, such as enforcing data retention policies.
"""
import sqlite3
from datetime import datetime, timedelta
from .config import DB_PATH, DB_LOCK

def get_data_retention_days():
    """Gets the retention policy from the settings table."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = 'data_retention_days'")
    result = cursor.fetchone()
    conn.close()
    # Default to 365 days if not set
    return int(result[0]) if result else 365

def cleanup_old_data():
    """Deletes records from all time-stamped log tables older than the policy."""
    retention_days = get_data_retention_days()
    cutoff_date = datetime.now() - timedelta(days=retention_days)
    cutoff_timestamp = cutoff_date.strftime("%Y-%m-%d %H:%M:%S")

    print(f"\nDATA CLEANUP: Policy={retention_days} days. Deleting records older than {cutoff_timestamp}...")

    try:
        with DB_LOCK:
            conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            cursor = conn.cursor()

            # --- Measurements & Context ---
            cursor.execute("SELECT id FROM measurements WHERE timestamp < ?", (cutoff_timestamp,))
            m_ids = [row[0] for row in cursor.fetchall()]
            if m_ids:
                cursor.execute(f"DELETE FROM environmental_context WHERE measurement_id IN ({','.join('?' for _ in m_ids)})", m_ids)
                cursor.execute(f"DELETE FROM measurements WHERE id IN ({','.join('?' for _ in m_ids)})", m_ids)
                print(f"-> Deleted {len(m_ids)} measurement records.")

            # --- Audit Logs ---
            cursor.execute("DELETE FROM audit_log WHERE timestamp < ?", (cutoff_timestamp,))
            print(f"-> Deleted {cursor.rowcount} audit log records.")

            # --- Device Logs ---
            cursor.execute("DELETE FROM device_logs WHERE timestamp < ?", (cutoff_timestamp,))
            print(f"-> Deleted {cursor.rowcount} device log records.")

            conn.commit()
            conn.close()
        
        print("-> Cleanup complete.")
    except Exception as e:
        print(f"-> An error occurred during data cleanup: {e}")


def get_deletable_data_preview(table_name, retention_days):
    """
    Fetches a preview of records that would be deleted based on a retention policy.
    Returns a list of dictionaries (rows).
    """
    cutoff_date = datetime.now() - timedelta(days=retention_days)
    cutoff_timestamp = cutoff_date.strftime("%Y-%m-%d %H:%M:%S")

    # Define valid tables and their relevant columns for preview
    valid_tables = {
        # **THE FIX:** Changed from specific columns to '*' to select ALL columns for measurements.
        'measurements': "*",
        'audit_log': "id, timestamp, action || ' on ' || target as Details",
        'device_logs': "id, timestamp, notes as Details"
    }

    if table_name not in valid_tables:
        return []

    query = f"SELECT {valid_tables[table_name]} FROM {table_name} WHERE timestamp < ? ORDER BY timestamp DESC"
    
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query, (cutoff_timestamp,))
        rows = cursor.fetchall()
        conn.close()
    
    return [dict(row) for row in rows]