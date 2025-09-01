# old_app.py
import threading
import time
import datetime
import llm_analyzer
import sqlite3
import random
import json

from flask import Flask, render_template, jsonify, request, abort

# --- NEW: Import the device ID from the config file ---
try:
    from config import DEVICE_ID
except ImportError:
    print("CRITICAL ERROR: config.py not found or DEVICE_ID not set. Please create it.")
    DEVICE_ID = "default-device-id"

from water_quality import train_decision_tree, predict_water_quality, get_feature_importances
from static_analyzer import get_detailed_water_analysis
from llm_analyzer import generate_llm_analysis
from llm_reasoning import generate_reasoning_for_range 
from database import (
    get_latest_data, DB_PATH, DB_LOCK, 
    get_all_devices, add_or_update_device, delete_device
)
from collections import Counter

from threshold_config import (
    PH_GOOD_MIN, PH_GOOD_MAX, PH_AVERAGE_MIN, PH_AVERAGE_MAX, PH_POOR_MIN, PH_POOR_MAX,
    TDS_GOOD_MAX, TDS_AVERAGE_MAX, TDS_POOR_MAX,
    TURB_GOOD_MAX, TURB_AVERAGE_MAX, TURB_POOR_MAX, TURB_BAD_THRESHOLD,
    TEMP_GOOD_MIN, TEMP_GOOD_MAX, TEMP_AVERAGE_MIN, TEMP_AVERAGE_MAX
)

# === Flask App Setup ===
app = Flask(__name__)

# === Model Training in Background ===
def train_model_thread_periodic():
    train_decision_tree()
    while True:
        time.sleep(1800)
        print("Periodic model training initiated...")
        train_decision_tree()
        print("Periodic model training completed (if data available).\n")

training_thread = threading.Thread(target=train_model_thread_periodic)
training_thread.daemon = True
training_thread.start()

# === Flask Web Server Routes ===
@app.route('/')
def index():
    # This remains the same, serving your dashboard
    return render_template('index.html')

# --- NEW ROUTE for Analytics Page ---
@app.route('/analytics')
def analytics():
    """Renders the new analytics and reports page."""
    return render_template('analytics.html')

@app.route('/devices')
def devices():
    """Renders the device and sensor management page."""
    return render_template('devices.html')


# --- API Endpoints for Device Management ---

@app.route('/api/devices', methods=['GET'])
def api_get_devices():
    """API endpoint to get all devices."""
    devices_data = get_all_devices()
    return jsonify(devices_data)


# --- SIMPLIFIED API Endpoints for Single System Device ---

@app.route('/api/system_device', methods=['GET'])
def api_get_system_device():
    """API endpoint to get the single system device's info."""
    all_devices = get_all_devices()
    # Find the device that matches the ID from the config file
    system_device = next((d for d in all_devices if d['id'] == DEVICE_ID), None)
    
    if not system_device:
        # If the device isn't in the database, create a default entry for it
        print(f"System device with ID '{DEVICE_ID}' not found in DB. Creating a default entry.")
        system_device = {
            "id": DEVICE_ID,
            "name": "BantayTubig Monitoring System",
            "location": "14.157478, 122.828580",
            "firmware": "v1.0.0",
            "status": "offline",
            "sensors": [
                {"type": "pH", "status": "unknown", "lastCalibration": "N/A"},
                {"type": "Turbidity", "status": "unknown", "lastCalibration": "N/A"},
                {"type": "TDS", "status": "unknown", "lastCalibration": "N/A"},
                {"type": "Temperature", "status": "unknown", "lastCalibration": "N/A"}
            ],
            "logs": []
        }
        add_or_update_device(system_device)

    return jsonify(system_device)

# --- NEW: Endpoint to receive heartbeats from the device ---
@app.route('/api/system_device/heartbeat', methods=['POST'])
def api_device_heartbeat():
    """Receives a heartbeat and updates the device status to 'online'."""
    data = request.json
    received_id = data.get('deviceId')
    
    # Security check: ensure the heartbeat is from the correct device
    if not received_id or received_id != DEVICE_ID:
        abort(400, "Invalid or missing deviceId for heartbeat.")

    all_devices = get_all_devices()
    device = next((d for d in all_devices if d['id'] == DEVICE_ID), None)
    
    if not device:
        return jsonify({"status": "error", "message": "Device not found in database."}), 404
        
    # Update the device status to online
    device['status'] = 'online'
    
    add_or_update_device(device) 
    
    return jsonify({"status": "success", "message": f"Heartbeat received from {DEVICE_ID}"})

@app.route('/api/system_device/update', methods=['POST'])
def api_update_system_device():
    """API endpoint to update the system device's name and location."""
    data = request.json
    all_devices = get_all_devices()
    device = next((d for d in all_devices if d['id'] == DEVICE_ID), None)

    if not device:
        return jsonify({"status": "error", "message": "Device not found."}), 404

    # Update only the name and location from the submitted form
    device['name'] = data.get('deviceName', device['name'])
    device['location'] = data.get('deviceLocation', device['location'])
    
    add_or_update_device(device)
    return jsonify({"status": "success", "message": "System details updated."}), 200

@app.route('/api/system_device/log', methods=['POST'])
def api_add_system_log():
    """API endpoint to add a maintenance log to the system device."""
    log_data = request.json
    all_devices = get_all_devices()
    device = next((d for d in all_devices if d['id'] == DEVICE_ID), None)
    
    if not device:
        return jsonify({"status": "error", "message": "Device not found."}), 404
        
    new_log = {
        "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "tech": log_data['technicianName'],
        "notes": log_data['logNotes']
    }
    device['logs'].insert(0, new_log)
    
    add_or_update_device(device)
    return jsonify({"status": "success", "log": new_log}), 200


# --- NEW API ENDPOINT for Key Driver Analysis ---
@app.route('/feature_importance')
def feature_importance():
    """Provides the feature importance data from the trained Random Forest model."""
    importances = get_feature_importances()
    if not importances:
        return jsonify({"error": "Feature importances not available. Model may still be training."}), 503
    sorted_importances = sorted(importances.items(), key=lambda item: item[1], reverse=True)
    return jsonify(dict(sorted_importances))

# --- NEW API ENDPOINT for What-If Scenario Simulator ---
@app.route('/predict_scenario', methods=['POST'])
def predict_scenario():
    """Takes hypothetical sensor values and returns a predicted water quality."""
    data = request.get_json()
    if not data:
        abort(400, "Request body must be JSON.")
    
    temp = data.get('temperature')
    ph = data.get('ph')
    tds = data.get('tds')
    turb = data.get('turbidity')

    if any(v is None for v in [temp, ph, tds, turb]):
        abort(400, "Missing one or more parameters.")

    prediction = predict_water_quality(float(temp), float(ph), float(tds), float(turb))
    return jsonify({"predicted_quality": prediction})


# --- NEW API ENDPOINT for Historical Data ---
@app.route('/historical_data')
def historical_data():
    """
    Fetches historical data from the database based on a date range.
    Expects 'start_date' and 'end_date' query parameters in 'YYYY-MM-DD' format.
    """
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if not start_date or not end_date:
        return jsonify({"error": "start_date and end_date parameters are required"}), 400

    try:
        # Use the centralized lock for thread safety
        with DB_LOCK:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row # This allows accessing columns by name
            cursor = conn.cursor()
            
            query = """
                SELECT timestamp, temperature, ph, tds, turbidity, water_quality 
                FROM measurements 
                WHERE timestamp BETWEEN ? AND ?
                ORDER BY timestamp ASC
            """
            # Add one day to the end date to include all records from that day
            end_date_inclusive = f"{end_date} 23:59:59"
            cursor.execute(query, (f"{start_date} 00:00:00", end_date_inclusive))
            
            rows = cursor.fetchall()
            conn.close()
        
        # Convert rows to a list of dictionaries
        data = [dict(row) for row in rows]
        return jsonify(data)
        
    except Exception as e:
        print(f"Error fetching historical data: {e}")
        return jsonify({"error": "Failed to retrieve data from the database"}), 500

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

@app.route('/latest')
def latest():
    latest_sensor_data = get_latest_data()
    if latest_sensor_data:
            temp = latest_sensor_data.get("temperature")
            ph = latest_sensor_data.get("ph")
            tds = latest_sensor_data.get("tds")
            turb = latest_sensor_data.get("turbidity")

            # --- TEMPORARY MODIFICATION FOR TURBIDITY ---
            # This line overrides the actual turbidity value with a random float
            # between 0.0 and 4.9 for demonstration purposes.
            # To revert to actual readings, simply comment out or delete this line.
            if turb is not None:
                turb = random.uniform(0.0, 4.9)
            # --- END OF TEMPORARY MODIFICATION ---

            water_quality_prediction = predict_water_quality(temp, ph, tds, turb)
            detailed_analysis = get_detailed_water_analysis(temp, ph, tds, turb, water_quality_prediction)

            response_data = {
                "timestamp": latest_sensor_data.get("timestamp"),
                "temperature": temp,
                "ph": ph,
                "tds": tds,
                "turbidity": turb,
                "water_quality": detailed_analysis.get("quality"),
                "quality_reason": detailed_analysis.get("reason"),
                "reason_tl": detailed_analysis.get("reason_tl"),
                "consumable_status": detailed_analysis.get("consumableStatus"),
                "consumable_status_tl": detailed_analysis.get("consumableStatus_tl"),
                "other_uses": detailed_analysis.get("otherUses"),
                "other_uses_tl": detailed_analysis.get("otherUses_tl"),
                "quality_suggestion": detailed_analysis.get("suggestion"),
                "quality_suggestion_tl": detailed_analysis.get("suggestion_tl"),
                "quality_notes": detailed_analysis.get("notes"),
                "quality_notes_tl": detailed_analysis.get("notes_tl"),
                "title_text": detailed_analysis.get("title_text"),
                "title_text_tl": detailed_analysis.get("title_text_tl")
            }
            return jsonify(response_data)

    detailed_analysis_for_empty = get_detailed_water_analysis(None, None, None, None, "Unknown")
    return jsonify({
        "timestamp": "N/A",
        "temperature": "N/A",
        "ph": "N/A",
        "tds": "N/A",
        "turbidity": "N/A",
        "water_quality": detailed_analysis_for_empty.get("quality"),
        "quality_reason": detailed_analysis_for_empty.get("reason"),
        "reason_tl": detailed_analysis_for_empty.get("reason_tl"),
        "consumable_status": detailed_analysis_for_empty.get("consumableStatus"),
        "consumable_status_tl": detailed_analysis_for_empty.get("consumableStatus_tl"),
        "other_uses": detailed_analysis_for_empty.get("otherUses"),
        "other_uses_tl": detailed_analysis_for_empty.get("otherUses_tl"),
        "quality_suggestion": detailed_analysis_for_empty.get("suggestion"),
        "quality_suggestion_tl": detailed_analysis_for_empty.get("suggestion_tl"),
        "quality_notes": detailed_analysis_for_empty.get("notes"),
        "quality_notes_tl": detailed_analysis_for_empty.get("notes_tl"),
        "title_text": detailed_analysis_for_empty.get("title_text"),
        "title_text_tl": detailed_analysis_for_empty.get("title_text_tl")
    })

@app.route('/thresholds')
def get_thresholds():
    thresholds = {
        "PH_GOOD_MIN": PH_GOOD_MIN,
        "PH_GOOD_MAX": PH_GOOD_MAX,
        "PH_AVERAGE_MIN": PH_AVERAGE_MIN,
        "PH_AVERAGE_MAX": PH_AVERAGE_MAX,
        "PH_POOR_MIN": PH_POOR_MIN,
        "PH_POOR_MAX": PH_POOR_MAX,
        "TDS_GOOD_MAX": TDS_GOOD_MAX,
        "TDS_AVERAGE_MAX": TDS_AVERAGE_MAX,
        "TDS_POOR_MAX": TDS_POOR_MAX,
        "TURB_GOOD_MAX": TURB_GOOD_MAX,
        "TURB_AVERAGE_MAX": TURB_AVERAGE_MAX,
        "TURB_POOR_MAX": TURB_POOR_MAX,
        "TURB_BAD_THRESHOLD": TURB_BAD_THRESHOLD,
        "TEMP_GOOD_MIN": TEMP_GOOD_MIN,
        "TEMP_GOOD_MAX": TEMP_GOOD_MAX,
        "TEMP_AVERAGE_MIN": TEMP_AVERAGE_MIN,
        "TEMP_AVERAGE_MAX": TEMP_AVERAGE_MAX
    }
    return jsonify(thresholds)

@app.route('/get_llm_analysis', methods=['POST'])
def get_llm_analysis_route():
    try:
        data = request.get_json()
        if not data:
            abort(400, description="Request body must be JSON.")

        temp = data.get('temp')
        ph = data.get('pH')
        tds = data.get('TDS')
        turb = data.get('turb')
        water_quality_prediction = data.get('water_quality')

        llm_response = generate_llm_analysis(temp, ph, tds, turb, water_quality_prediction)

        if "Error" in llm_response.get("reasoning", "") or "Error" in llm_response.get("tagalog_translation", ""):
            return jsonify({"error": llm_response["reasoning"]}), 500
        
        return jsonify(llm_response)

    except Exception as e:
        print(f"Error in /get_llm_analysis route: {e}")
        return jsonify({"error": f"An internal server error occurred: {str(e)}"}), 500

def run_flask_app():
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)

if __name__ == '__main__':
    run_flask_app()
