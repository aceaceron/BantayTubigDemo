# routes/ml_routes.py

# === IMPORTS ==================================================================
# --- Standard Library Imports ---
from datetime import datetime     # Used for timestamping the demo anomalies.
import random                     # Used to generate random data for demo anomalies.
import sqlite3                    # The driver for connecting to the SQLite database file.

# --- Third-Party Imports ---
import pandas as pd               # Used for data manipulation, specifically to handle the
                                  # SQL query result as a DataFrame for easy conversion.
from flask import Blueprint, jsonify, request  # Core Flask components:
                                  # Blueprint for organizing routes, jsonify for creating
                                  # JSON responses, and request to access incoming data.

# --- Local Application Imports ---
# Imports the application's Socket.IO instance for real-time, non-blocking communication.
from app import socketio

# Imports the path to the database file from the configuration.
from database.config import DB_PATH

# Imports custom functions for interacting with the database.
from database import (
    get_unannotated_anomalies, save_annotation, log_anomaly,
    get_latest_reading_with_env, get_summarized_data_for_range, get_device_info
)

from config import DEVICE_ID

# Imports the specific machine learning functions for generating insights and forecasts.
from database.data_manager import get_annotated_anomalies
from ml_models.llm_insights import generate_current_status_analysis, generate_historical_reasoning
from ml_models.forecasting import generate_demo_forecasts
# ==============================================================================


# Defines a Blueprint for all machine learning related routes, helping to
# keep the application's code organized.
ml_bp = Blueprint('ml_bp', __name__)


# ==============================================================================
# === TAB: LIVE ANALYSIS =======================================================
# ==============================================================================
# This section handles the real-time AI analysis of the current water quality.
# The process is non-blocking, using a Socket.IO background task.

@socketio.on('request_analysis')
def handle_analysis_request():
    """
    Handles the 'request_analysis' event emitted from the client's browser.
    
    How it works:
    1. Triggered when the "Live Analysis" tab loads on the frontend.
    2. Gets the client's unique session ID ('sid') from the socket connection.
    3. Starts the `_run_ai_analysis_and_emit` function in a background thread,
       passing the 'sid' so the result can be sent back to the correct user.
    """
    sid = request.sid
    socketio.start_background_task(_run_ai_analysis_and_emit, sid)
    print(f"Received analysis request from client {sid}. Starting background task.")

def _run_ai_analysis_and_emit(sid):
    """
    A helper function that performs the slow AI analysis in the background.
    
    How it works:
    1. Fetches the most recent sensor and environmental data from the database.
    2. Calls the Large Language Model (LLM) to generate insights. This is the slow part.
    3. Once the analysis is complete, it emits an 'analysis_result' event containing
       the data directly back to the original client using their unique 'sid'.
    """
    print(f"Starting background AI analysis for client {sid}...")
    try:
        latest_data = get_latest_reading_with_env()
        if not latest_data:
            analysis = {"reasoning": "No recent data available for analysis."}
        else:
            analysis = generate_current_status_analysis(
                temp=latest_data.get('temperature'),
                pH=latest_data.get('ph'),
                TDS=latest_data.get('tds'),
                turb=latest_data.get('turbidity'),
                water_quality_prediction=latest_data.get('water_quality'),
                env_context=latest_data.get('env_context')
            )
        socketio.emit('analysis_result', analysis, room=sid)
        print(f"Background AI analysis complete. Result sent to client {sid}.")
    except Exception as e:
        print(f"Error in AI analysis background task: {e}")
        socketio.emit('analysis_result', {"reasoning": "An error occurred during AI analysis."}, room=sid)


# ==============================================================================
# === TAB: HISTORICAL SUMMARY ==================================================
# ==============================================================================
# This section handles the AI-powered summary of water quality over a selected date range.

@ml_bp.route('/ml/historical_reasoning', methods=['POST'])
def api_get_historical_reasoning():
    """Provides an LLM-powered summary for a selected date range."""
    data = request.json
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    
    summary_data = get_summarized_data_for_range(start_date, end_date)
    if not summary_data:
        return jsonify({"html": "<p>No data found for the selected range.</p>"})

    # ADDED: Fetch the device info dynamically from the database.
    device_info = get_device_info(DEVICE_ID) or {} # Use or {} as a fallback

    date_range_str = f"{start_date} to {end_date}"
    
    # MODIFIED: Pass the dynamic device_info to the reasoning function.
    reasoning_html = generate_historical_reasoning(date_range_str, summary_data, device_info)
    
    return jsonify({"html": reasoning_html})

# ==============================================================================
# === TAB: FORECASTING =========================================================
# ==============================================================================
# This section provides the data for the predictive forecasting charts.

@ml_bp.route('/ml/forecasts', methods=['GET'])
def api_get_forecasts():
    """
    Provides forecast data for the charts on the "Forecasting" tab.
    
    How it works:
    1. Triggered by a GET request when the tab loads or a demo option is selected.
    2. Checks the 'source' parameter in the URL.
    3. If 'source' is a demo, it calls `generate_demo_forecasts` to train a new model on-the-fly.
    4. If 'source' is 'database' (the default), it reads the standard, pre-calculated
       forecast from the database.
    5. Returns a JSON object with the data points for all four sensor charts.
    """
    source = request.args.get('source', 'database')
    if source in ['continuous_30d', 'non_continuous_7d']:
        return jsonify(generate_demo_forecasts(source))
    
    conn = sqlite3.connect(DB_PATH)
    forecasts = {}
    param_map = {'temp': 'temperature', 'ph': 'ph', 'tds': 'tds', 'turbidity': 'turbidity'}
    for short_name, db_column_name in param_map.items():
        query = "SELECT timestamp, forecast_value, lower_bound, upper_bound FROM ml_forecasts WHERE parameter = ? ORDER BY timestamp DESC LIMIT 24"
        df = pd.read_sql_query(query, conn, params=(db_column_name,))
        forecasts[short_name] = df.iloc[::-1].to_dict('records')
    conn.close()
    return jsonify(forecasts)


# ==============================================================================
# === TAB: EVENT ANNOTATION ====================================================
# ==============================================================================
# This section handles the entire "human-in-the-loop" feedback system.

@ml_bp.route('/ml/anomalies', methods=['GET'])
def api_get_anomalies():
    """
    Provides a list of anomalies that need user feedback.
    
    How it works:
    1. Triggered by a GET request when the "Event Annotation" tab loads.
    2. Queries the database for all anomalies that have not yet been annotated by a user.
    3. Returns a JSON list of these events to be displayed as review cards.
    """
    anomalies = get_unannotated_anomalies()
    return jsonify(anomalies)

@ml_bp.route('/ml/annotate', methods=['POST'])
def api_annotate_event():
    """
    Saves the user's feedback for a specific anomaly.
    
    How it works:
    1. Triggered by a POST request when the user submits an annotation form.
    2. Receives the anomaly ID, the user's selected label, and any comments.
    3. Calls a database function to save this information, marking the event as "annotated".
    4. This annotated data can now be used by the feedback loop to retrain the AI.
    """
    data = request.json
    try:
        save_annotation(
            anomaly_id=data.get('anomaly_id'),
            user_id=1,  # In a real app, get this from the logged-in user session
            label=data.get('label'),
            comments=data.get('comments')
        )
        return jsonify({"status": "success", "message": "Annotation saved. Thank you for your feedback!"}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@ml_bp.route('/ml/generate_demo_anomaly', methods=['POST'])
def api_generate_demo_anomaly():
    """
    Creates and logs a fake anomaly to the database for demonstration.
    
    How it works:
    1. Triggered by a POST request from the "Generate Demo Event" button.
    2. Creates a dictionary with plausible random data for a fake anomaly.
    3. Calls the `log_anomaly` function to save this fake event to the database.
    4. The frontend then refreshes its list, and the new demo event appears for annotation.
    """
    try:
        demo_params = {
            "parameter": random.choice(["ph", "turbidity"]),
            "value": round(random.uniform(3.5, 4.5) if random.choice([True, False]) else random.uniform(800, 950), 2),
            "severity": round(random.uniform(0.4, 0.8), 3),
            "anomaly_type": "Issue",
            "rca_suggestions": random.choice([
                ["High Correlation with Rainfall (92%)", "Possible Agricultural Runoff"],
                ["Sudden Spike without Rainfall", "Potential Industrial Discharge"]
            ])
        }
        
        log_anomaly(timestamp=datetime.now(), **demo_params)
        return jsonify({"status": "success", "message": "Demo anomaly generated successfully."}), 201
    except Exception as e:
        print(f"Error generating demo anomaly: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
    
@ml_bp.route('/ml/anomalies/history', methods=['GET'])
def api_get_annotation_history():
    """Provides a list of all previously annotated anomalies for the history log."""
    history = get_annotated_anomalies()
    return jsonify(history)
