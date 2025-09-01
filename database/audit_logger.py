# database/audit_logger.py
"""
Handles all database operations for the system audit log.
"""
import sqlite3
import json
from datetime import datetime
from .config import DB_PATH, DB_LOCK

def add_audit_log(user_id, component, action, target, status, ip_address, details=None):
    """
    Adds a new entry to the audit log.
    
    Args:
        user_id (int or None): The ID of the user performing the action (None for system actions).
        component (str): The part of the system being affected (e.g., 'User Management').
        action (str): A description of the action (e.g., 'User Created').
        target (str): The object the action was performed on (e.g., a user's email).
        status (str): The outcome of the action ('Success' or 'Failure').
        ip_address (str): The originating IP address.
        details (dict, optional): A dictionary of extra details to be stored as JSON.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    details_json = json.dumps(details) if details else None

    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO audit_log (timestamp, user_id, component, action, target, status, ip_address, details) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (timestamp, user_id, component, action, target, status, ip_address, details_json)
        )
        conn.commit()
        conn.close()

def get_audit_logs(date_range=None, user_filter=None, action_filter=None):
    """
    Retrieves audit logs with optional filters for date, user, and action.
    Joins with the users table to include the user's full name.
    """
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = """
            SELECT a.timestamp, a.action, a.target, a.status, a.ip_address, a.details,
                   a.component, COALESCE(u.full_name, 'System') as user_name
            FROM audit_log a
            LEFT JOIN users u ON a.user_id = u.id
            WHERE 1=1
        """
        params = []
        
        if user_filter:
            query += " AND (u.email LIKE ? OR u.full_name LIKE ?)"
            params.extend([f"%{user_filter}%", f"%{user_filter}%"])
        if action_filter:
            query += " AND a.action LIKE ?"
            params.append(f"%{action_filter}%")
            
        if date_range:
            if ' to ' in date_range:
                try:
                    start, end = date_range.split(' to ')
                    query += " AND a.timestamp BETWEEN ? AND ?"
                    params.extend([f"{start} 00:00:00", f"{end} 23:59:59"])
                except ValueError:
                    print(f"Invalid date range format: {date_range}")
            else:
                single_date = date_range.strip()
                query += " AND a.timestamp BETWEEN ? AND ?"
                params.extend([f"{single_date} 00:00:00", f"{single_date} 23:59:59"])

        query += " ORDER BY a.timestamp DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
    return [dict(row) for row in rows]