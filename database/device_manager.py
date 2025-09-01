# database/device_manager.py
"""
Handles all database operations related to devices, sensor calibrations,
and maintenance logs.
"""
import sqlite3
import json
from datetime import datetime
from .config import DB_PATH, DB_LOCK

# --- Device Management Functions ---

def get_all_devices():
    """
    Fetches all devices from the database, parsing the JSON sensor data.
    """
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM devices')
        rows = cursor.fetchall()
        conn.close()
    devices = []
    for row in rows:
        device = dict(row)
        device['sensors'] = json.loads(device['sensors']) if device['sensors'] else []
        devices.append(device)
    return devices

def get_device_info(device_id):
    """
    Fetches all details for a single device by its ID.
    """
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM devices WHERE id = ?", (device_id,))
        device = cursor.fetchone()
        conn.close()
        
        if device:
            return dict(device)
    return None

def add_or_update_device(device_data):
    """
    Adds a new device or updates an existing one using REPLACE INTO.
    Serializes sensor data into a JSON string for storage.
    """
    sensors_json = json.dumps(device_data.get('sensors', []))
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("""
            REPLACE INTO devices (id, name, location, water_source, firmware, status, sensors)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            device_data['id'],
            device_data['name'],
            device_data.get('location'),
            device_data.get('water_source'),
            device_data.get('firmware'),
            device_data.get('status', 'offline'),
            sensors_json
        ))
        conn.commit()
        conn.close()

def delete_device(device_id):
    """
    Deletes a device from the database by its unique ID.
    """
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM devices WHERE id = ?', (device_id,))
        conn.commit()
        conn.close()

# --- Sensor Calibration Functions ---

def update_sensor_calibration(device_id, sensor_type, date_str, slope, offset, is_default=0):
    """
    Adds or updates the calibration record for a single sensor on a device,
    including its calculated slope and offset.
    """
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("""
            REPLACE INTO sensor_calibrations (device_id, sensor_type, last_calibration_date, slope, offset, is_default)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (device_id, sensor_type, date_str, slope, offset, is_default))
        conn.commit()
        conn.close()

def get_calibration_formula(device_id, sensor_type):
    """
    Retrieves the active calibration formula (slope and offset) for a specific sensor.
    """
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT slope, offset FROM sensor_calibrations WHERE device_id = ? AND sensor_type = ?",
            (device_id, sensor_type)
        )
        row = cursor.fetchone()
        conn.close()
    return dict(row) if row else None

def get_calibrations_for_device(device_id):
    """
    Retrieves all calibration records for a specific device, returning a dictionary
    mapping sensor types to their last calibration date.
    """
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT sensor_type, last_calibration_date FROM sensor_calibrations WHERE device_id = ?", (device_id,))
        rows = cursor.fetchall()
        conn.close()
    return {row['sensor_type']: row['last_calibration_date'] for row in rows}

def restore_default_calibration(device_id, sensor_type):
    """
    Deletes a sensor's custom calibration record, effectively reverting it
    to the hardcoded default formula used in the application logic.
    """
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute(
            'DELETE FROM sensor_calibrations WHERE device_id = ? AND sensor_type = ?',
            (device_id, sensor_type)
        )
        conn.commit()
        conn.close()

# --- Device Log Functions ---

def add_device_log(device_id, user_id, notes):
    """
    Adds a new maintenance log entry for a specific device.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO device_logs (device_id, user_id, timestamp, notes) VALUES (?, ?, ?, ?)",
            (device_id, user_id, timestamp, notes)
        )
        conn.commit()
        conn.close()

def get_logs_for_device(device_id):
    """
    Retrieves all maintenance logs for a specific device, joining with the users
    table to get the technician's name.
    """
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                l.timestamp as date, 
                l.notes, 
                COALESCE(u.full_name, 'System') as tech 
            FROM device_logs l
            LEFT JOIN users u ON l.user_id = u.id
            WHERE l.device_id = ? 
            ORDER BY l.timestamp DESC
        """, (device_id,))
        rows = cursor.fetchall()
        conn.close()
    return [dict(row) for row in rows]