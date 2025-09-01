# routes.py
import sqlite3
from datetime import datetime
from flask import render_template, jsonify, request, abort
from app import app
import numpy as np


try:
    from config import DEVICE_ID
except ImportError:
    DEVICE_ID = "default-device-id"

from water_quality import predict_water_quality, get_feature_importances
from static_analyzer import get_detailed_water_analysis
from llm_analyzer import generate_llm_analysis
from llm_reasoning import generate_reasoning_for_range
# MODIFIED: Import the new restore function
from database import *
from collections import Counter
from threshold_config import *
import sensor_reader

# --- Temporary session storage for the current user's ID ---
# Defaults to User ID 1 (typically the first administrator).
CURRENT_USER_ID = 1

# === Web Page Rendering Routes (no changes) ===
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analytics')
def analytics():
    return render_template('analytics.html')

@app.route('/devices')
def devices():
    return render_template('devices.html')

# === NEW PAGE RENDERING ROUTE ===
@app.route('/users')
def user_management():
    return render_template('user_management.html')

# === NEW: API endpoint to simulate logging in as a user ===
@app.route('/api/set_current_user', methods=['POST'])
def set_current_user():
    """Sets the global user ID for the temporary session."""
    global CURRENT_USER_ID
    data = request.json
    user_id = data.get('userId')
    
    if user_id is not None:
        try:
            CURRENT_USER_ID = int(user_id)
            user = get_user_by_id(CURRENT_USER_ID)
            user_name = user['full_name'] if user else 'Unknown User'
            # AUDIT LOGGING
            add_audit_log(user_id=CURRENT_USER_ID, component='Security', action='Simulated Login', 
                          target=f"ID: {CURRENT_USER_ID}", status='Success', ip_address=request.remote_addr)
            return jsonify({"status": "success", "message": f"Current user set to {user_name}"})
        except (ValueError, TypeError):
            return jsonify({"status": "error", "message": "Invalid userId format"}), 400
    
    return jsonify({"status": "error", "message": "userId not provided"}), 400

# === API Endpoints ===

# --- System Device API ---
@app.route('/api/system_device', methods=['GET'])
def api_get_system_device():
    all_devices = get_all_devices()
    system_device = next((d for d in all_devices if d['id'] == DEVICE_ID), None)
    
    if not system_device:
        system_device = {
            "id": DEVICE_ID, "name": "BantayTubig Monitoring System",
            "location": "14.2834, 122.6885", # Jose Panganiban coordinates
            "water_source": "Jose Panganiban Water District",
            "status": "offline",
            "sensors": [
                {"type": "pH", "status": "unknown", "last_value": None},
                {"type": "Turbidity", "status": "unknown", "last_value": None},
                {"type": "TDS", "status": "unknown", "last_value": None},
                {"type": "Temperature", "status": "unknown", "last_value": None}
            ],
            "logs": []
        }
        add_or_update_device(system_device)
    if system_device:
        system_device['logs'] = get_logs_for_device(system_device['id'])
    return jsonify(system_device)


# --- This endpoint receives and stores the latest sensor values ---
@app.route('/api/system_device/heartbeat', methods=['POST'])
def api_device_heartbeat():
    """Receives a heartbeat with sensor values and updates the device status."""
    data = request.json
    received_id = data.get('deviceId')
    sensor_values = data.get('sensor_values', {})

    if not received_id or received_id != DEVICE_ID:
        abort(400, "Invalid or missing deviceId for heartbeat.")

    device = next((d for d in get_all_devices() if d['id'] == DEVICE_ID), None)
    if not device:
        # If the device doesn't exist, create it before updating.
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

# --- Data & Analytics API ---

@app.route('/latest')
def latest():
    latest_sensor_data = get_latest_data()
    if latest_sensor_data:
            # This now includes the new voltage columns automatically
            
            # The detailed analysis function still only needs the calculated values
            detailed_analysis = get_detailed_water_analysis(
                latest_sensor_data.get("temperature"),
                latest_sensor_data.get("ph"),
                latest_sensor_data.get("tds"),
                latest_sensor_data.get("turbidity"),
                latest_sensor_data.get("water_quality")
            )

            # Combine the database data with the analysis data
            response_data = {**latest_sensor_data, **detailed_analysis}
            return jsonify(response_data)

    # Fallback for when there is no data
    detailed_analysis_for_empty = get_detailed_water_analysis(None, None, None, None, "Unknown")
    return jsonify({
        "timestamp": "N/A", "temperature": "N/A", "ph": "N/A", "tds": "N/A", "turbidity": "N/A",
        "ph_voltage": "N/A", "tds_voltage": "N/A", "turbidity_voltage": "N/A",
        **detailed_analysis_for_empty
    })

@app.route('/api/system_device/update', methods=['POST'])
def api_update_device_crud():
    device_data = request.json
    if not device_data or 'deviceId' not in device_data:
        abort(400, "Invalid device data provided.")
    
    db_data = {
        'id': device_data['deviceId'], 
        'name': device_data['deviceName'],
        'location': device_data.get('deviceLocation'),
        'water_source': device_data.get('deviceWaterSource'),
        'firmware': device_data.get('firmwareVersion')
    }
    existing = next((d for d in get_all_devices() if d['id'] == db_data['id']), None)
    if existing:
        db_data.update({k: existing.get(k) for k in ['sensors', 'status']})
    
    add_or_update_device(db_data)
    
    # AUDIT LOGGING
    add_audit_log(user_id=CURRENT_USER_ID, component='Device Management', action='Device Details Updated', 
                  target=f"ID: {db_data['id']}", status='Success', ip_address=request.remote_addr)
    
    return jsonify({"status": "success"})

@app.route('/api/devices/delete', methods=['POST'])
def api_delete_device_crud():
    device_id = request.json.get('id')
    if not device_id:
        abort(400, "Device ID is required.")
    delete_device(device_id)
    return jsonify({"status": "success"})

@app.route('/api/devices/log', methods=['POST'])
def api_add_log_crud():
    log_data = request.json
    device_id = log_data.get('deviceId')
    user_id_from_form = log_data.get('userId')
    notes = log_data.get('logNotes')

    if not all([device_id, user_id_from_form, notes]):
        abort(400, "Missing data.")
    
    try:
        add_device_log(device_id=device_id, user_id=user_id_from_form, notes=notes)
        
        add_audit_log(user_id=CURRENT_USER_ID, component='Device Management', action='Maintenance Log Added', 
                      target=f"Device ID: {device_id}", status='Success', ip_address=request.remote_addr,
                      details={'note': notes, 'logged_for_user_id': user_id_from_form})
        
        user = get_user_by_id(user_id_from_form)
        tech_name = user['full_name'] if user else 'Unknown User'
        response_log = {"date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "tech": tech_name, "notes": notes}
        return jsonify({"status": "success", "log": response_log})
    except Exception as e:
        abort(500, f"Could not write log to database: {e}")

# --- NEW: API endpoint to fetch eligible technicians and admins ---
@app.route('/api/technicians', methods=['GET'])
def api_get_technicians():
    """Provides a list of users who are Administrators or Technicians."""
    users = get_technicians_and_admins()
    return jsonify(users)
# --- Data & Analytics API ---

@app.route('/historical_data')
def historical_data():
    """Fetches historical data from the database based on a date range."""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    if not start_date or not end_date:
        return jsonify({"error": "start_date and end_date are required"}), 400

    try:
        with DB_LOCK:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            query = "SELECT * FROM measurements WHERE timestamp BETWEEN ? AND ? ORDER BY timestamp ASC"
            end_date_inclusive = f"{end_date} 23:59:59"
            cursor.execute(query, (f"{start_date} 00:00:00", end_date_inclusive))
            rows = cursor.fetchall()
            conn.close()
        return jsonify([dict(row) for row in rows])
    except Exception as e:
        print(f"Error fetching historical data: {e}")
        return jsonify({"error": "Failed to retrieve data"}), 500

@app.route('/thresholds')
def get_thresholds():
    """Provides the defined water quality thresholds to the front-end."""
    return jsonify({k: v for k, v in globals().items() if k.endswith(('_MIN', '_MAX', '_THRESHOLD'))})

# --- API Endpoint for updating a specific sensor's calibration date ---
@app.route('/api/devices/calibrate', methods=['POST'])
def api_calibrate_device():
    """Updates the last calibration date for a specific sensor on a device."""
    data = request.json
    device_id = data.get('deviceId')
    sensor_type = data.get('sensorType') # Get the specific sensor type
    
    if not device_id or not sensor_type:
        abort(400, "Device ID and Sensor Type are required for calibration.")

    new_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    new_calibration_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        # Pass the specific sensor type to the database function
        update_sensor_calibration(device_id, sensor_type, new_calibration_date)
        return jsonify({"status": "success", "message": f"Calibration for {sensor_type} on {device_id} updated."})
    except Exception as e:
        print(f"Error updating calibration date: {e}")
        return jsonify({"status": "error", "message": "Could not update calibration date."}), 500
    
# ---  API Endpoint to fetch calibration dates for a device ---
@app.route('/api/devices/calibrations', methods=['GET'])
def api_get_calibrations():
    """Fetches all calibration records for a specific device."""
    device_id = request.args.get('deviceId')
    if not device_id:
        abort(400, "Device ID is required to fetch calibration data.")
    
    try:
        # This function already exists in your database.py
        calibration_data = get_calibrations_for_device(device_id)
        return jsonify(calibration_data)
    except Exception as e:
        print(f"Error fetching calibration data: {e}")
        return jsonify({"status": "error", "message": "Could not fetch calibration data."}), 500

# --- NEW: API Endpoint to get a live, single sensor reading ---
@app.route('/api/live_sensor_data', methods=['GET'])
def api_get_live_sensor_data():
    """Reads a sensor directly and returns its current raw voltage."""
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

# --- MODIFIED: API Endpoint to calculate and save the new calibration formula ---
@app.route('/api/devices/calculate_calibration', methods=['POST'])
def api_calculate_calibration():
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
        
        # MODIFIED: Use 'target' instead of 'device_id'
        add_audit_log(user_id=CURRENT_USER_ID, component='Sensor Calibration', action='Sensor Calibrated', 
                      target=f"Device: {device_id}, Sensor: {sensor_type}", status='Success', 
                      ip_address=request.remote_addr, details={'slope': slope, 'offset': offset})
        
        return jsonify({"status": "success", "message": f"New calibration saved for {sensor_type}"})
    except Exception as e:
        # MODIFIED: Use 'target' instead of 'device_id'
        add_audit_log(user_id=CURRENT_USER_ID, component='Sensor Calibration', action='Sensor Calibrated', 
                      target=f"Device: {device_id}, Sensor: {sensor_type}", status='Failure', 
                      ip_address=request.remote_addr, details={'error': str(e)})
        abort(500, "An error occurred during calibration.")

# --- MODIFIED: API Endpoint to restore default calibration is now active ---
@app.route('/api/devices/restore_default_calibration', methods=['POST'])
def api_restore_default():
    data = request.json
    device_id = data.get('deviceId')
    sensor_type = data.get('sensorType')
    if not device_id or not sensor_type:
        abort(400, "deviceId and sensorType are required.")
    
    restore_default_calibration(device_id, sensor_type)

    add_audit_log(user_id=CURRENT_USER_ID, component='Sensor Calibration', action='Calibration Restored', 
                  target=f"Device: {device_id}, Sensor: {sensor_type}", status='Success', 
                  ip_address=request.remote_addr)

    return jsonify({"status": "success", "message": f"Default calibration restored for {sensor_type}."})


    return jsonify({"status": "success", "message": f"Default calibration restored for {sensor_type}."})


# --- Machine Learning & AI API ---
@app.route('/feature_importance')
def feature_importance():
    """Provides feature importance data from the ML model."""
    importances = get_feature_importances()
    if not importances:
        return jsonify({"error": "Feature importances not available."}), 503
    return jsonify(dict(sorted(importances.items(), key=lambda item: item[1], reverse=True)))

@app.route('/predict_scenario', methods=['POST'])
def predict_scenario():
    """Takes hypothetical sensor values and returns a predicted quality."""
    data = request.get_json()
    if not data or any(k not in data for k in ['temperature', 'ph', 'tds', 'turbidity']):
        abort(400, "Missing one or more parameters.")
    
    prediction = predict_water_quality(
        float(data['temperature']), float(data['ph']),
        float(data['tds']), float(data['turbidity'])
    )
    return jsonify({"predicted_quality": prediction})

@app.route('/get_llm_analysis', methods=['POST'])
def get_llm_analysis_route():
    """Generates a detailed AI analysis for a single data point."""
    data = request.get_json()
    if not data: abort(400, "Request body must be JSON.")
    
    try:
        llm_response = generate_llm_analysis(
            data.get('temp'), data.get('pH'), data.get('TDS'),
            data.get('turb'), data.get('water_quality')
        )
        return jsonify(llm_response)
    except Exception as e:
        print(f"Error in /get_llm_analysis: {e}")
        return jsonify({"error": str(e)}), 500

def summarize_data_for_range(start_date, end_date):
    """
    Fetches data for a given date range and returns a summary dictionary.
    """
    if not start_date or not end_date:
        return {}
        
    summary = {
        "avg_temp": 0, "avg_ph": 0, "avg_tds": 0, "avg_turb": 0,
        "most_common_quality": "N/A"
    }
    
    try:
        with DB_LOCK:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = "SELECT temperature, ph, tds, turbidity, water_quality FROM measurements WHERE timestamp BETWEEN ? AND ?"
            # Handle both "YYYY-MM-DD" and "YYYY-MM-DD to YYYY-MM-DD" formats
            end_date_inclusive = f"{end_date.split(' to ')[-1].strip()} 23:59:59"
            start_date_inclusive = f"{start_date.split(' to ')[0].strip()} 00:00:00"

            cursor.execute(query, (start_date_inclusive, end_date_inclusive))
            rows = cursor.fetchall()
            conn.close()

        if not rows:
            return summary

        # Calculate averages
        temps, phs, tdss, turbs, qualities = [], [], [], [], []
        for row in rows:
            # FIX: Use try-except blocks to safely convert values to float,
            # ignoring any that cause an error (like the string 'Error').
            try:
                if row['temperature'] is not None: temps.append(float(row['temperature']))
            except (ValueError, TypeError):
                pass # Ignore non-numeric values
            
            try:
                if row['ph'] is not None: phs.append(float(row['ph']))
            except (ValueError, TypeError):
                pass
            
            try:
                if row['tds'] is not None: tdss.append(float(row['tds']))
            except (ValueError, TypeError):
                pass
            
            try:
                if row['turbidity'] is not None: turbs.append(float(row['turbidity']))
            except (ValueError, TypeError):
                pass

            if row['water_quality']: qualities.append(row['water_quality'])

        # Calculate averages only if lists are not empty
        summary["avg_temp"] = f"{sum(temps) / len(temps):.2f}" if temps else "N/A"
        summary["avg_ph"] = f"{sum(phs) / len(phs):.2f}" if phs else "N/A"
        summary["avg_tds"] = f"{sum(tdss) / len(tdss):.2f}" if tdss else "N/A"
        summary["avg_turb"] = f"{sum(turbs) / len(turbs):.2f}" if turbs else "N/A"

        # Find most common quality
        if qualities:
            summary["most_common_quality"] = Counter(qualities).most_common(1)[0][0]

        return summary
    except Exception as e:
        print(f"Error summarizing data for range {start_date} to {end_date}: {e}")
        return summary

@app.route('/generate_reasoning', methods=['POST'])
def generate_reasoning_route():
    """
    Receives date ranges, summarizes data, gets device info,
    and then calls the LLM for a contextual analysis.
    """
    try:
        data = request.get_json()
        if not data:
            abort(400, description="Request body must be JSON.")

        primary_range = data.get('primary_range')
        comparison_range = data.get('comparison_range')

        if not primary_range:
            abort(400, description="Primary date range is required.")
            
        # MODIFIED: Fetch current device info to pass to the LLM
        device = next((d for d in get_all_devices() if d['id'] == DEVICE_ID), None)
        if not device:
            abort(404, description="System device not found in database.")
            
        device_location = device.get('location', 'Unknown Location')
        device_water_source = device.get('water_source', 'Unknown Source')

        # Summarize data for the primary range
        primary_summary = summarize_data_for_range(primary_range, primary_range)
        
        # Summarize data for the comparison range, if it exists
        comparison_summary = None
        if comparison_range:
            comparison_summary = summarize_data_for_range(comparison_range, comparison_range)

        # Call the dedicated function from llm_reasoning.py with new arguments
        reasoning_text = generate_reasoning_for_range(
            primary_range, 
            primary_summary, 
            device_location,
            device_water_source,
            comparison_range, 
            comparison_summary
        )

        return jsonify({"reasoning": reasoning_text})

    except Exception as e:
        print(f"Error in /generate_reasoning route: {e}")
        return jsonify({"error": f"An internal server error occurred: {str(e)}"}), 500
    """
    Receives date ranges, summarizes the data for those ranges,
    and then calls the LLM for a contextual analysis.
    """
    try:
        data = request.get_json()
        if not data:
            abort(400, description="Request body must be JSON.")

        primary_range = data.get('primary_range')
        comparison_range = data.get('comparison_range')

        if not primary_range:
            abort(400, description="Primary date range is required.")

        # Summarize data for the primary range
        primary_summary = summarize_data_for_range(primary_range, primary_range)
        
        # Summarize data for the comparison range, if it exists
        comparison_summary = None
        if comparison_range:
            comparison_summary = summarize_data_for_range(comparison_range, comparison_range)

        # Call the dedicated function from llm_reasoning.py
        reasoning_text = generate_reasoning_for_range(
            primary_range, 
            primary_summary, 
            comparison_range, 
            comparison_summary
        )

        return jsonify({"reasoning": reasoning_text})

    except Exception as e:
        print(f"Error in /generate_reasoning route: {e}")
        return jsonify({"error": f"An internal server error occurred: {str(e)}"}), 500
    

# === NEW API ENDPOINTS FOR USER MANAGEMENT ===

@app.route('/api/users', methods=['GET'])
def api_get_users():
    users = get_all_users_with_roles()
    return jsonify(users)

@app.route('/api/users/<int:user_id>', methods=['GET'])
def api_get_user(user_id):
    user = get_user_by_id(user_id)
    if user:
        return jsonify(user)
    abort(404, "User not found")

@app.route('/api/users/add', methods=['POST'])
def api_add_user():
    data = request.json
    try:
        new_user_id, plain_text_password = add_user(
            data['full_name'], 
            data['email'], 
            data['role_id'], 
            data.get('phone_number')
        )
        
        add_audit_log(user_id=CURRENT_USER_ID, component='User Management', action='User Created', 
                      target=f"Email: {data['email']}", status='Success', ip_address=request.remote_addr)

        new_user_info = {
            "id": new_user_id,
            "name": data['full_name'],
            "email": data['email'],
            # MODIFIED: Added the phone number to the response object
            "phone_number": data.get('phone_number'),
            "password": plain_text_password
        }
        return jsonify({"status": "success", "newUser": new_user_info})
    except Exception as e:
        add_audit_log(user_id=CURRENT_USER_ID, component='User Management', action='User Created', 
                      target=f"Email: {data['email']}", status='Failure', ip_address=request.remote_addr, 
                      details={'error': str(e)})
        abort(400, f"Error creating user: {e}")

@app.route('/api/users/update', methods=['POST'])
def api_update_user():
    data = request.json
    user_id_to_update = data.get('id')
    update_user(user_id_to_update, data['full_name'], data['role_id'], data.get('phone_number'))

    add_audit_log(user_id=CURRENT_USER_ID, component='User Management', action='User Updated', 
                  target=f"User ID: {user_id_to_update}", status='Success', ip_address=request.remote_addr)
                  
    return jsonify({"status": "success", "message": "User updated."})

@app.route('/api/users/set_status', methods=['POST'])
def api_set_user_status():
    data = request.json
    user_id_to_update = data.get('id')
    new_status = data.get('status')
    set_user_status(user_id_to_update, new_status)

    add_audit_log(user_id=CURRENT_USER_ID, component='User Management', action='User Status Changed', 
                  target=f"User ID: {user_id_to_update}", status='Success', ip_address=request.remote_addr, 
                  details={'new_status': new_status})

    return jsonify({"status": "success", "message": "User status updated."})

@app.route('/api/users/reset_password', methods=['POST'])
def api_reset_user_password():
    data = request.json
    user_id = data.get('id')
    user_info = get_user_by_id(user_id)
    if not user_info:
        abort(404, "User not found.")

    new_password = reset_password_for_user(user_id)
    
    add_audit_log(user_id=CURRENT_USER_ID, component='User Management', action='Password Reset', 
                  target=f"Email: {user_info['email']}", status='Success', ip_address=request.remote_addr)
    
    reset_user_info = {
        "name": user_info['full_name'],
        "email": user_info['email'],
        "phone_number": user_info.get('phone_number'),
        "password": new_password
    }
    
    return jsonify({"status": "success", "resetUser": reset_user_info})

@app.route('/api/audit_log', methods=['GET'])
def api_get_audit_log():
    date_range = request.args.get('date_range')
    user = request.args.get('user')
    action = request.args.get('action')
    logs = get_audit_logs(date_range, user, action)
    return jsonify(logs)


@app.route('/api/roles', methods=['GET'])
def api_get_roles():
    roles = get_all_roles()
    return jsonify(roles)

# --- NEW: API endpoints for role CRUD operations ---

@app.route('/api/roles/<int:role_id>', methods=['GET'])
def api_get_role(role_id):
    role = get_role_by_id(role_id)
    if role:
        return jsonify(role)
    abort(404, "Role not found")

@app.route('/api/roles/add', methods=['POST'])
def api_add_role():
    data = request.json
    add_role(data['name'], data.get('permissions', ''))
    
    add_audit_log(user_id=CURRENT_USER_ID, component='Role Management', action='Role Created', 
                  target=f"Name: {data['name']}", status='Success', ip_address=request.remote_addr)

    return jsonify({"status": "success", "message": "Role added."})

@app.route('/api/roles/update', methods=['POST'])
def api_update_role():
    data = request.json
    update_role(data['id'], data['name'], data.get('permissions', ''))
    
    add_audit_log(user_id=CURRENT_USER_ID, component='Role Management', action='Role Updated', 
                  target=f"Role ID: {data['id']}", status='Success', ip_address=request.remote_addr)
    
    return jsonify({"status": "success", "message": "Role updated."})

@app.route('/api/roles/delete', methods=['POST'])
def api_delete_role():
    data = request.json
    role_id = data.get('id')
    role = get_role_by_id(role_id)
    target_name = role['name'] if role else f"ID: {role_id}"
    
    add_audit_log(user_id=CURRENT_USER_ID, component='Role Management', action='Role Deleted', 
                  target=target_name, status='Success', ip_address=request.remote_addr)
                  
    delete_role(role_id)
    return jsonify({"status": "success", "message": "Role deleted."})