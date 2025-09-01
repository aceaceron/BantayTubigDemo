# routes/device_routes.py
"""
Handles all API endpoints related to device management, sensor data, and calibration.
"""
from flask import Blueprint, jsonify, request, abort
from datetime import datetime
import numpy as np

# Import shared config and database functions
from config import DEVICE_ID, CURRENT_USER_ID
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
    add_audit_log(user_id=CURRENT_USER_ID, component='Device Management', action='Device Details Updated', target=f"ID: {db_data['id']}", status='Success', ip_address=request.remote_addr)
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
        add_audit_log(user_id=CURRENT_USER_ID, component='Device Management', action='Maintenance Log Added', target=f"Device ID: {device_id}", status='Success', ip_address=request.remote_addr, details={'note': notes, 'logged_for_user_id': user_id_from_form})
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
        add_audit_log(user_id=CURRENT_USER_ID, component='Sensor Calibration', action='Sensor Calibrated', target=f"Device: {device_id}, Sensor: {sensor_type}", status='Success', ip_address=request.remote_addr, details={'slope': slope, 'offset': offset})
        return jsonify({"status": "success", "message": f"New calibration saved for {sensor_type}"})
    except Exception as e:
        add_audit_log(user_id=CURRENT_USER_ID, component='Sensor Calibration', action='Sensor Calibrated', target=f"Device: {device_id}, Sensor: {sensor_type}", status='Failure', ip_address=request.remote_addr, details={'error': str(e)})
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
    add_audit_log(user_id=CURRENT_USER_ID, component='Sensor Calibration', action='Calibration Restored', target=f"Device: {device_id}, Sensor: {sensor_type}", status='Success', ip_address=request.remote_addr)
    return jsonify({"status": "success", "message": f"Default calibration restored for {sensor_type}."})

@device_bp.route('/audit_log', methods=['GET'])
def api_get_audit_log():
    """Fetches the system audit log with optional filters."""
    date_range = request.args.get('date_range')
    user = request.args.get('user')
    action = request.args.get('action')
    logs = get_audit_logs(date_range, user_filter=user, action_filter=action)
    return jsonify(logs)
