# routes/analytics_routes.py
"""
Handles all API endpoints for data analytics, reporting, and AI/ML features.
"""
from flask import Blueprint, jsonify, request, abort
from collections import Counter
import sqlite3

# Import shared config and functions
from config import DEVICE_ID
from database import (
    DB_PATH, DB_LOCK, get_all_devices, get_latest_data, get_context_for_latest_measurement,
    get_audit_logs, summarize_context_for_range, get_thresholds_for_dashboard
)
from water_quality import predict_water_quality, get_feature_importances
from static_analyzer import get_detailed_water_analysis
from llm_analyzer import generate_llm_analysis
from llm_reasoning import generate_reasoning_for_range


analytics_bp = Blueprint('analytics_bp', __name__)

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row # This allows accessing columns by name
    return conn
    
# --- Data & Analytics API ---

@analytics_bp.route('/latest', methods=['GET'])
def get_latest_analytics():
    """
    Fetches the latest sensor reading, runs both the static and ML analysis,
    and returns a combined, flat JSON object for the dashboard.
    """
    try:
        conn = get_db_connection()
        latest_row = conn.execute(
            'SELECT * FROM measurements ORDER BY timestamp DESC LIMIT 1'
        ).fetchone()
        conn.close()

        if latest_row is None:
            return jsonify({"error": "No data available"}), 404

        # Convert the database row to a mutable dictionary
        latest_data = dict(latest_row)
        
        # --- Run both analyses using the latest sensor data ---
        
        # 1. Get the ML prediction result (which includes quality, confidence, etc.)
        ml_prediction = predict_water_quality(
            latest_data.get('temperature'),
            latest_data.get('ph'),
            latest_data.get('tds'),
            latest_data.get('turbidity')
        )

        # 2. Get the static analysis (reasons, suggestions, icons, etc.)
        # We use the ML model's quality prediction as input for the static analyzer
        static_analysis = get_detailed_water_analysis(
            latest_data.get('temperature'),
            latest_data.get('ph'),
            latest_data.get('tds'),
            latest_data.get('turbidity'),
            ml_prediction['quality'] # Use the ML quality prediction here
        )
        
        # --- Combine all data into a single, flat dictionary ---
        # The JavaScript is expecting a flat structure, so we merge them.
        final_response = {}
        final_response.update(latest_data)
        final_response.update(static_analysis)
        final_response.update(ml_prediction)

        # The 'water_quality' from the DB might be stale, ensure we use the ML one.
        final_response['water_quality'] = ml_prediction['quality']

        return jsonify(final_response)

    except Exception as e:
        print(f"Error in /analytics/latest: {e}")
        return jsonify({"error": str(e)}), 500

@analytics_bp.route('/thresholds')
def get_thresholds():
    """
    Provides the defined water quality thresholds to the front-end.
    This now fetches the values dynamically from the database.
    """
    try:
        thresholds = get_thresholds_for_dashboard()
        return jsonify(thresholds)
    except Exception as e:
        print(f"Error in /analytics/thresholds: {e}")
        return jsonify({"error": str(e)}), 500

@analytics_bp.route('/historical_data')
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
        return jsonify({"error": "Failed to retrieve data"}), 500


# --- Machine Learning & AI API ---

@analytics_bp.route('/feature_importance')
def feature_importance():
    """Provides feature importance data from the ML model."""
    importances = get_feature_importances()
    if not importances:
        return jsonify({"error": "Feature importances not available."}), 503
    return jsonify(dict(sorted(importances.items(), key=lambda item: item[1], reverse=True)))

@analytics_bp.route('/predict_scenario', methods=['POST'])
def predict_scenario():
    """Takes hypothetical sensor values and returns a predicted quality."""
    data = request.get_json()
    if not data or any(k not in data for k in ['temperature', 'ph', 'tds', 'turbidity']):
        abort(400, "Missing one or more parameters.")
    prediction = predict_water_quality(float(data['temperature']), float(data['ph']), float(data['tds']), float(data['turbidity']))
    return jsonify({"predicted_quality": prediction})

@analytics_bp.route('/get_llm_analysis', methods=['POST'])
def get_llm_analysis_route():
    """Provides a detailed, AI-generated analysis for a given set of water parameters."""
    try:
        data = request.get_json()
        if not data:
            abort(400, "Request body cannot be empty.")

        # Extract data from the POST request
        temp = data.get('temp')
        ph = data.get('pH')
        tds = data.get('TDS')
        turb = data.get('turb')
        quality = data.get('water_quality')

        # 1. Fetch the most recent environmental context from the database.
        latest_context = get_context_for_latest_measurement()

        # 2. Pass this context to the LLM analyzer function.
        analysis_result = generate_llm_analysis(
            temp, ph, tds, turb, quality,
            env_context=latest_context 
        )

        return jsonify(analysis_result)
    except Exception as e:
        return jsonify({"error": f"An internal server error occurred: {str(e)}"}), 500

@analytics_bp.route('/generate_reasoning', methods=['POST'])
def generate_reasoning_route():
    """
    Generates a contextual analysis of summarized water quality data,
    now including summarized environmental data.
    """
    try:
        data = request.get_json()
        primary_range = data.get('primary_range')
        comparison_range = data.get('comparison_range')
        if not primary_range:
            abort(400, description="Primary date range is required.")
        
        device = next((d for d in get_all_devices() if d['id'] == DEVICE_ID), None)
        if not device:
            abort(404, description="System device not found in database.")
        
        # Fetch summaries for sensor data
        primary_summary = summarize_data_for_range(primary_range, primary_range)
        # Fetch summaries for environmental context data
        primary_context_summary = summarize_context_for_range(primary_range, primary_range)
        
        comparison_summary = None
        comparison_context_summary = None
        if comparison_range:
            comparison_summary = summarize_data_for_range(comparison_range, comparison_range)
            comparison_context_summary = summarize_context_for_range(comparison_range, comparison_range)

        # Pass all data to the LLM reasoning function
        reasoning_text = generate_reasoning_for_range(
            primary_range, primary_summary, device.get('location'), device.get('water_source'),
            primary_context_summary=primary_context_summary,
            comparison_range=comparison_range,
            comparison_summary=comparison_summary,
            comparison_context_summary=comparison_context_summary
        )
        return jsonify({"reasoning": reasoning_text})
    except Exception as e:
        return jsonify({"error": f"An internal server error occurred: {str(e)}"}), 500


# Helper function used by the generate_reasoning_route
def summarize_data_for_range(start_date, end_date):
    if not start_date or not end_date:
        return {}
    summary = {"avg_temp": "N/A", "avg_ph": "N/A", "avg_tds": "N/A", "avg_turb": "N/A", "most_common_quality": "N/A"}
    try:
        with DB_LOCK:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            query = "SELECT temperature, ph, tds, turbidity, water_quality FROM measurements WHERE timestamp BETWEEN ? AND ?"
            end_date_inclusive = f"{end_date.split(' to ')[-1].strip()} 23:59:59"
            start_date_inclusive = f"{start_date.split(' to ')[0].strip()} 00:00:00"
            cursor.execute(query, (start_date_inclusive, end_date_inclusive))
            rows = cursor.fetchall()
            conn.close()
        if not rows:
            return summary
        temps, phs, tdss, turbs, qualities = [], [], [], [], []
        for row in rows:
            try:
                if row['temperature'] is not None: temps.append(float(row['temperature']))
            except (ValueError, TypeError): pass
            try:
                if row['ph'] is not None: phs.append(float(row['ph']))
            except (ValueError, TypeError): pass
            try:
                if row['tds'] is not None: tdss.append(float(row['tds']))
            except (ValueError, TypeError): pass
            try:
                if row['turbidity'] is not None: turbs.append(float(row['turbidity']))
            except (ValueError, TypeError): pass
            if row['water_quality']: qualities.append(row['water_quality'])
        if temps: summary["avg_temp"] = f"{sum(temps) / len(temps):.2f}"
        if phs: summary["avg_ph"] = f"{sum(phs) / len(phs):.2f}"
        if tdss: summary["avg_tds"] = f"{sum(tdss) / len(tdss):.2f}"
        if turbs: summary["avg_turb"] = f"{sum(turbs) / len(turbs):.2f}"
        if qualities:
            summary["most_common_quality"] = Counter(qualities).most_common(1)[0][0]
        return summary
    except Exception as e:
        print(f"Error summarizing data for range: {e}")
        return summary