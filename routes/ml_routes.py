# routes/ml_routes.py
import sqlite3
from database.config import DB_PATH 
import pandas as pd
from flask import Blueprint, jsonify, request
# Assuming these functions exist or will be created in your database manager
from database import (
    get_latest_forecasts, get_unannotated_anomalies, save_annotation,
    get_latest_reading_with_env, get_summarized_data_for_range
)
# Import the new consolidated LLM functions
from ml_models.llm_insights import generate_current_status_analysis, generate_historical_reasoning

ml_bp = Blueprint('ml_bp', __name__)

@ml_bp.route('/ml/forecasts', methods=['GET'])
def api_get_forecasts():
    """Provides forecast data for charts on the ML page."""
    conn = sqlite3.connect(DB_PATH)
    forecasts = {}
    
    # This map ensures the API sends the short names ('temp') that the HTML expects,
    # while still querying the database with the correct full column names ('temperature').
    param_map = {
        'temp': 'temperature',
        'ph': 'ph',
        'tds': 'tds',
        'turbidity': 'turbidity'
    }

    for short_name, db_column_name in param_map.items():
        query = "SELECT timestamp, forecast_value, lower_bound, upper_bound FROM ml_forecasts WHERE parameter = ? ORDER BY timestamp"
        df = pd.read_sql_query(query, conn, params=(db_column_name,))
        forecasts[short_name] = df.to_dict('records')

    conn.close()
    return jsonify(forecasts)

@ml_bp.route('/ml/anomalies', methods=['GET'])
def api_get_anomalies():
    """Provides a list of anomalies that need user feedback."""
    anomalies = get_unannotated_anomalies()
    return jsonify(anomalies)

@ml_bp.route('/ml/annotate', methods=['POST'])
def api_annotate_event():
    """Endpoint for users to submit their feedback on an anomaly."""
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
    

# NEW ENDPOINT for Current Status Analysis
@ml_bp.route('/ml/current_analysis', methods=['GET'])
def api_get_current_analysis():
    """Provides an LLM-powered analysis of the most recent sensor reading."""
    latest_data = get_latest_reading_with_env() # You need to implement this DB function
    if not latest_data:
        return jsonify({"reasoning": "No recent data available."}), 404
        
    analysis = generate_current_status_analysis(
        temp=latest_data.get('temperature'),
        pH=latest_data.get('ph'),
        TDS=latest_data.get('tds'),
        turb=latest_data.get('turbidity'),
        water_quality_prediction=latest_data.get('water_quality'),
        env_context=latest_data.get('env_context')
    )
    return jsonify(analysis)

# NEW ENDPOINT for Historical Reasoning
@ml_bp.route('/ml/historical_reasoning', methods=['POST'])
def api_get_historical_reasoning():
    """Provides an LLM-powered summary for a selected date range."""
    data = request.json
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    
    summary_data = get_summarized_data_for_range(start_date, end_date) # You need to implement this DB function
    if not summary_data:
        return jsonify({"html": "<p>No data found for the selected range.</p>"})

    date_range_str = f"{start_date} to {end_date}"
    reasoning_html = generate_historical_reasoning(date_range_str, summary_data)
    
    return jsonify({"html": reasoning_html})