# routes/device_routes.py
"""
Handles all API endpoints related to device management, sensor data, and calibration.
"""
from flask import Blueprint, jsonify, request, abort, session, send_file
from datetime import datetime
import numpy as np
import json
import os
import csv
import io
import sqlite3

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'bantaytubig.db')

# Import shared config and database functions
from config import DEVICE_ID
from database import *
import sensor_reader

device_bp = Blueprint('device_bp', __name__)

# --- System Device API ---

@device_bp.route('/system_device', methods=['GET'])
def api_get_system_device():
    """Fetches the primary system device's complete status, including sensors and logs."""
    all_devices = get_all_devices()
    system_device = next((d for d in all_devices if d['id'] == DEVICE_ID), None)
    
    if not system_device:
        system_device = {
            "id": DEVICE_ID, "name": "BantayTubig Monitoring System",
            "location": "14.2834, 122.6885",
            "water_source": "Water Service Provider", "status": "offline",
            "sensors": [{"type": "pH", "status": "unknown", "last_value": None}, {"type": "Turbidity", "status": "unknown", "last_value": None}, {"type": "TDS", "status": "unknown", "last_value": None}, {"type": "Temperature", "status": "unknown", "last_value": None}],
            "logs": []
        }
        add_or_update_device(system_device)
    if system_device:
        system_device['logs'] = get_logs_for_device(system_device['id'])
    return jsonify(system_device)

@device_bp.route('/system_device/heartbeat', methods=['POST'])
def api_device_heartbeat():
    """Receives a heartbeat with sensor values from the physical device."""
    data = request.json
    received_id = data.get('deviceId')
    sensor_values = data.get('sensor_values', {})
    if not received_id or received_id != DEVICE_ID:
        abort(400, "Invalid or missing deviceId for heartbeat.")
    device = next((d for d in get_all_devices() if d['id'] == DEVICE_ID), None)
    if not device:
        api_get_system_device()
        device = next((d for d in get_all_devices() if d['id'] == DEVICE_ID), None)
    device['status'] = 'online'
    for sensor in device.get('sensors', []):
        sensor_type = sensor.get('type')
        if sensor_type in sensor_values:
            value = sensor_values[sensor_type]
            sensor['last_value'] = value
            sensor['status'] = 'active' if isinstance(value, (int, float)) else 'error'
    add_or_update_device(device)
    return jsonify({"status": "success", "message": f"Heartbeat from {DEVICE_ID} received."})

@device_bp.route('/system_device/update', methods=['POST'])
def api_update_device_crud():
    """Updates the core details of the system device."""
    device_data = request.json
    if not device_data or 'deviceId' not in device_data:
        abort(400, "Invalid device data provided.")
    db_data = {'id': device_data['deviceId'], 'name': device_data['deviceName'], 'location': device_data.get('deviceLocation'), 'water_source': device_data.get('deviceWaterSource'), 'firmware': device_data.get('firmwareVersion')}
    existing = next((d for d in get_all_devices() if d['id'] == db_data['id']), None)
    if existing:
        db_data.update({k: existing.get(k) for k in ['sensors', 'status']})
    add_or_update_device(db_data)
    add_audit_log(user_id=session.get('user_id'), component='Device Management', action='Device Details Updated', target=f"ID: {db_data['id']}", status='Success', ip_address=request.remote_addr)
    return jsonify({"status": "success"})

@device_bp.route('/devices/delete', methods=['POST'])
def api_delete_device_crud():
    device_id = request.json.get('id')
    if not device_id:
        abort(400, "Device ID is required.")
    delete_device(device_id)
    return jsonify({"status": "success"})

@device_bp.route('/devices/log', methods=['POST'])
def api_add_log_crud():
    """Adds a new maintenance log entry for a device."""
    log_data = request.json
    device_id = log_data.get('deviceId')
    user_id_from_form = log_data.get('userId')
    notes = log_data.get('logNotes')
    if not all([device_id, user_id_from_form, notes]):
        abort(400, "Missing data.")
    try:
        add_device_log(device_id=device_id, user_id=user_id_from_form, notes=notes)
        add_audit_log(user_id=session.get('user_id'), component='Device Management', action='Maintenance Log Added', target=f"Device ID: {device_id}", status='Success', ip_address=request.remote_addr, details={'note': notes, 'logged_for_user_id': user_id_from_form})
        user = get_user_by_id(user_id_from_form)
        tech_name = user['full_name'] if user else 'Unknown User'
        response_log = {"date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "tech": tech_name, "notes": notes}
        return jsonify({"status": "success", "log": response_log})
    except Exception as e:
        abort(500, f"Could not write log to database: {e}")

@device_bp.route('/live_sensor_data', methods=['GET'])
def api_get_live_sensor_data():
    """Provides a direct, live voltage reading from a specified sensor."""
    sensor_type = request.args.get('sensorType')
    if not sensor_type:
        abort(400, "sensorType is required.")
    voltage = None
    if sensor_type == 'pH':
        voltage = sensor_reader.read_ph()
    elif sensor_type == 'TDS':
        voltage = sensor_reader.read_tds()
    elif sensor_type == 'Turbidity':
        voltage = sensor_reader.read_turbidity()
    if voltage is None:
        return jsonify({"error": "Could not read sensor."}), 500
    return jsonify({"voltage": voltage})

# --- Sensor Calibration API ---

@device_bp.route('/devices/calibrations', methods=['GET'])
def api_get_calibrations():
    """Fetches all calibration records for a device."""
    device_id = request.args.get('deviceId')
    if not device_id:
        abort(400, "Device ID is required to fetch calibration data.")
    try:
        calibration_data = get_calibrations_for_device(device_id)
        return jsonify(calibration_data)
    except Exception as e:
        return jsonify({"status": "error", "message": "Could not fetch calibration data."}), 500

@device_bp.route('/devices/calculate_calibration', methods=['POST'])
def api_calculate_calibration():
    """Calculates and saves a new sensor calibration formula."""
    data = request.json
    device_id = data.get('deviceId')
    sensor_type = data.get('sensorType')
    try:
        points = data.get('points')
        if not all([device_id, sensor_type, points]) or len(points) < 2:
            abort(400, "Requires deviceId, sensorType, and at least two calibration points.")
        voltages = np.array([p['voltage'] for p in points])
        buffer_values = np.array([p['buffer'] for p in points])
        slope, offset = np.polyfit(voltages, buffer_values, 1)
        new_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        update_sensor_calibration(device_id, sensor_type, new_date, slope, offset, is_default=0)
        add_audit_log(user_id=session.get('user_id'), component='Sensor Calibration', action='Sensor Calibrated', target=f"Device: {device_id}, Sensor: {sensor_type}", status='Success', ip_address=request.remote_addr, details={'slope': slope, 'offset': offset})
        return jsonify({"status": "success", "message": f"New calibration saved for {sensor_type}"})
    except Exception as e:
        add_audit_log(user_id=session.get('user_id'), component='Sensor Calibration', action='Sensor Calibrated', target=f"Device: {device_id}, Sensor: {sensor_type}", status='Failure', ip_address=request.remote_addr, details={'error': str(e)})
        abort(500, "An error occurred during calibration.")

@device_bp.route('/devices/restore_default_calibration', methods=['POST'])
def api_restore_default():
    """Restores a sensor's calibration to its hardcoded default."""
    data = request.json
    device_id = data.get('deviceId')
    sensor_type = data.get('sensorType')
    if not device_id or not sensor_type:
        abort(400, "deviceId and sensorType are required.")
    restore_default_calibration(device_id, sensor_type)
    add_audit_log(user_id=session.get('user_id'), component='Sensor Calibration', action='Calibration Restored', target=f"Device: {device_id}, Sensor: {sensor_type}", status='Success', ip_address=request.remote_addr)
    return jsonify({"status": "success", "message": f"Default calibration restored for {sensor_type}."})
@device_bp.route('/devices/calibration_logs', methods=['GET'])
def api_get_calibration_logs():
    """Return only Sensor Calibration audit logs, formatted for frontend."""
    try:
        logs = get_audit_logs()

        calibration_logs = []
        for log in logs:
            if log.get("component") == "Sensor Calibration":
                raw_details = log.get("details")
                try:
                    parsed_details = json.loads(raw_details) if raw_details else {}
                except Exception:
                    parsed_details = {"raw": raw_details}

                calibration_logs.append({
                    "date": log.get("timestamp"),
                    "tech": log.get("user_name") or "Unknown User",
                    "action": log.get("action"),
                    "target": log.get("target"),
                    "status": log.get("status"),
                    "details": parsed_details
                })

        return jsonify(calibration_logs)
    except Exception as e:
        import traceback
        traceback.print_exc()  # print full error to console
        return jsonify({"status": "error", "message": str(e)}), 500
# --- Turbidity Reference Management (JSON API) ---

@device_bp.route('/dev/settings/turbidity', methods=['GET'])
def api_get_turbidity():
    """
    Return current turbidity reference voltages as JSON.
    Front-end can use this to prefill the form dynamically.
    """
    try:
        refs = get_turbidity_references(DEVICE_ID)
        return jsonify({
            "V_REF_HIGH": refs.get("v_ref_high", 0.49),
            "V_REF_LOW": refs.get("v_ref_low", 0.06)
        })
    except Exception as e:
        return jsonify({"message": f"Error fetching turbidity references: {str(e)}"}), 500

@device_bp.route('/dev/settings/turbidity', methods=['POST'])
def api_update_turbidity():
    """
    Update turbidity voltage references (V_REF_HIGH, V_REF_LOW) via JSON.
    Returns success or error message.
    """
    data = request.get_json()
    if not data or "V_REF_HIGH" not in data or "V_REF_LOW" not in data:
        return jsonify({"message": "Invalid input"}), 400

    try:
        v_high = float(data["V_REF_HIGH"])
        v_low = float(data["V_REF_LOW"])
        update_turbidity_references(DEVICE_ID, v_high, v_low)  # DB function
        add_audit_log(
            user_id=session.get('user_id'),
            component='Developer Settings',
            action='Updated Turbidity References',
            target=f"Device: {DEVICE_ID}",
            status='Success',
            ip_address=request.remote_addr,
            details={'v_ref_high': v_high, 'v_ref_low': v_low}
        )
        return jsonify({"message": "Turbidity references updated successfully!"})
    except Exception as e:
        add_audit_log(
            user_id=session.get('user_id'),
            component='Developer Settings',
            action='Updated Turbidity References',
            target=f"Device: {DEVICE_ID}",
            status='Failure',
            ip_address=request.remote_addr,
            details={'error': str(e)}
        )
        return jsonify({"message": f"Error updating references: {str(e)}"}), 500


@device_bp.route('/dev/logs', methods=['GET'])
def api_get_dev_logs():
    """
    Returns the current contents of the console log file.
    If the file doesn't exist, returns an empty list.
    """
    log_file = os.path.join(os.path.dirname(__file__), "../console.log") 
    logs = []
    if os.path.exists(log_file):
        try:
            with open(log_file, "r") as f:
                # Split lines, remove trailing newlines
                logs = [line.rstrip() for line in f.readlines()]
        except Exception as e:
            return jsonify({"status": "error", "message": f"Could not read log file: {str(e)}"}), 500
    return jsonify({"status": "success", "logs": logs})


# Get all table names
@device_bp.route('/dev/tables', methods=['GET'])
def api_get_tables():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    return jsonify({"tables": tables})

# Fetch table rows
@device_bp.route('/dev/table/<table_name>')
def get_table(table_name):
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 10))
    sort_col = request.args.get("sort_col")
    sort_dir = request.args.get("sort_dir", "asc")
    search = request.args.get("search", "").strip()

    offset = (page - 1) * per_page

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get columns
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [info[1] for info in cursor.fetchall()]

    # Build query
    query = f"SELECT * FROM {table_name}"
    params = []
    if search:
        search_conditions = " OR ".join([f"{col} LIKE ?" for col in columns])
        query += f" WHERE {search_conditions}"
        params = [f"%{search}%"] * len(columns)

    if sort_col and sort_col in columns:
        query += f" ORDER BY {sort_col} {sort_dir.upper()}"

    query += f" LIMIT {per_page} OFFSET {offset}"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return jsonify({"columns": columns, "rows": rows})

# Insert row
@device_bp.route('/dev/table/<table_name>/row', methods=['POST'])
def api_insert_row(table_name):
    data = request.json
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?']*len(data))
        cursor.execute(f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})", tuple(data.values()))
        conn.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        conn.close()

# Update row
@device_bp.route('/dev/table/<table_name>/row/<int:row_id>', methods=['PUT'])
def api_update_row(table_name, row_id):
    data = request.json
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        set_clause = ', '.join([f"{k}=?" for k in data.keys()])
        cursor.execute(f"UPDATE {table_name} SET {set_clause} WHERE id=?", (*data.values(), row_id))
        conn.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        conn.close()

# Delete row
@device_bp.route('/dev/table/<table_name>/row/<int:row_id>', methods=['DELETE'])
def api_delete_row(table_name, row_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(f"DELETE FROM {table_name} WHERE id=?", (row_id,))
        conn.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        conn.close()

@device_bp.route('/dev/table/<table_name>/delete_all', methods=['POST'])
def api_delete_all(table_name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(f"DELETE FROM {table_name}")
        conn.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        conn.close()

@device_bp.route('/dev/table/<table_name>/drop', methods=['POST'])
def api_drop_table(table_name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        conn.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        conn.close()


# --- Exporting Methods ---

@device_bp.route('/dev/export/database', methods=['GET'])
def api_export_database():
    """Download the full SQLite database file."""
    try:
        return send_file(DB_PATH, as_attachment=True, download_name="bantaytubig.db")
    except Exception as e:
        return jsonify({"error": f"Failed to export database: {str(e)}"}), 500


@device_bp.route('/dev/export/table/<table_name>', methods=['GET'])
def api_export_table(table_name):
    """Export a single table as SQL dump."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # Extract table schema + inserts
        schema = cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table_name,)).fetchone()
        if not schema:
            return jsonify({"error": f"Table '{table_name}' not found."}), 404
        sql_dump = schema[0] + ";\n"
        rows = cursor.execute(f"SELECT * FROM {table_name}").fetchall()
        columns = [desc[0] for desc in cursor.description]

        for row in rows:
            values = ', '.join([f"'{str(v)}'" if v is not None else "NULL" for v in row])
            sql_dump += f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({values});\n"

        conn.close()
        return send_file(
            io.BytesIO(sql_dump.encode("utf-8")),
            as_attachment=True,
            download_name=f"{table_name}.sql",
            mimetype="text/sql"
        )
    except Exception as e:
        return jsonify({"error": f"Failed to export table: {str(e)}"}), 500


@device_bp.route('/dev/export/table/<table_name>/csv', methods=['GET'])
def api_export_table_csv(table_name):
    """Export a single table as CSV."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        conn.close()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(columns)  # write header
        writer.writerows(rows)

        return send_file(
            io.BytesIO(output.getvalue().encode("utf-8")),
            as_attachment=True,
            download_name=f"{table_name}.csv",
            mimetype="text/csv"
        )
    except Exception as e:
        return jsonify({"error": f"Failed to export CSV: {str(e)}"}), 500
    