# routes/analytics_routes.py
"""
Handles all API endpoints for data analytics, reporting, and AI/ML features.
"""
from flask import Blueprint, jsonify, request, abort, session, send_file, Response
from collections import Counter
import io
import csv
import tempfile
import os
import sqlite3

# Import shared config and functions
from config import DEVICE_ID
from database import (
    DB_PATH, DB_LOCK, add_audit_log, get_all_devices, get_latest_data, get_context_for_latest_measurement,
    get_audit_logs, summarize_context_for_range, get_thresholds_for_dashboard,
    cleanup_old_data, get_deletable_data_preview
)
from water_quality import predict_water_quality, get_feature_importances
from static_analyzer import get_detailed_water_analysis
from llm_analyzer import generate_llm_analysis
from llm_reasoning import generate_reasoning_for_range
from auth.decorators import role_required

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
    
@analytics_bp.route('/retention_policy', methods=['POST'])
@role_required('Administrator')
def set_retention_policy():
    """Updates just the data retention setting."""
    data = request.get_json()
    new_retention_days = data.get('dataRetention')
    if not new_retention_days:
        return jsonify({'status': 'error', 'message': 'dataRetention not provided.'}), 400
    
    try:
        conn = get_db_connection()
        conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", 
                     ('data_retention_days', str(new_retention_days)))
        conn.commit()
        conn.close()
        add_audit_log(user_id=session.get('user_id'), component='Data Management', action='Policy Updated', target=f"{new_retention_days} days", status='Success', ip_address=request.remote_addr)
        return jsonify({'status': 'success', 'message': f"Data retention policy set to {new_retention_days} days."})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    

@analytics_bp.route('/retention-preview', methods=['POST'])
@role_required('Administrator')
def get_retention_preview():
    """Provides a preview of data that would be deleted by a new policy."""
    data = request.get_json()
    days = data.get('retention_days')
    table = data.get('table_name')
    if not days or not table:
        return jsonify({'error': 'retention_days and table_name are required'}), 400
    
    preview_data = get_deletable_data_preview(table, int(days))
    return jsonify(preview_data)

@analytics_bp.route('/run-cleanup', methods=['POST'])
@role_required('Administrator')
def run_cleanup_now():
    """Triggers the data retention cleanup process immediately."""
    try:
        cleanup_old_data()
        add_audit_log(
            user_id=session.get('user_id'), component='Data Management', action='Manual Cleanup', 
            status='Success', ip_address=request.remote_addr
        )
        return jsonify({'status': 'success', 'message': 'Data cleanup process completed.'})
    except Exception as e:
        add_audit_log(
            user_id=session.get('user_id'), component='Data Management', action='Manual Cleanup', 
            status='Failure', ip_address=request.remote_addr, details={'error': str(e)}
        )
        return jsonify({'status': 'error', 'message': str(e)}), 500


@analytics_bp.route('/export-deletable-data', methods=['POST'])
@role_required('Administrator')
def export_deletable_data():
    """Exports data scheduled for deletion into CSV or a new SQLite DB file."""
    data = request.get_json()
    days = data.get('retention_days')
    table_name = data.get('table_name')
    export_format = data.get('format') # 'csv' or 'db'

    if not all([days, table_name, export_format]):
        return jsonify({'error': 'retention_days, table_name, and format are required'}), 400

    # Fetch the exact same data the user is previewing
    records_to_export = get_deletable_data_preview(table_name, int(days))

    if not records_to_export:
        return jsonify({'error': 'No data to export for the given criteria'}), 404

    # --- CSV EXPORT LOGIC ---
    if export_format == 'csv':
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=records_to_export[0].keys())
        writer.writeheader()
        writer.writerows(records_to_export)
        
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-disposition": f"attachment; filename={table_name}_export.csv"}
        )

    # --- SQLITE DB EXPORT LOGIC ---
    elif export_format == 'db':
        """
        This revised logic builds the database to a temporary file on disk to ensure it's
        correctly structured and closed. It then reads this complete file into an
        in-memory buffer (io.BytesIO) and sends that buffer. This prevents issues
        where the file might be sent before it's fully written or gets deleted prematurely.
        """
        temp_db_path = None
        try:
            # 1. Create a temporary file with a unique name to avoid conflicts.
            fd, temp_db_path = tempfile.mkstemp(suffix=".db")
            os.close(fd)  # Close the initial file handle.

            # 2. Get the table schema from the main database.
            main_conn = get_db_connection()
            schema_query = main_conn.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'").fetchone()
            if not schema_query:
                main_conn.close()
                return jsonify({'error': f'Could not find schema for table {table_name}'}), 500
            table_schema = schema_query['sql']
            main_conn.close()

            # 3. Connect to the new temporary file and populate it.
            export_conn = sqlite3.connect(temp_db_path)
            export_cursor = export_conn.cursor()
            export_cursor.execute(table_schema)  # Create the table.

            keys = records_to_export[0].keys()
            placeholders = ', '.join(['?'] * len(keys))
            insert_sql = f"INSERT INTO {table_name} ({', '.join(keys)}) VALUES ({placeholders})"
            rows_to_insert = [tuple(rec.get(key) for key in keys) for rec in records_to_export]
            export_cursor.executemany(insert_sql, rows_to_insert)
            
            export_conn.commit()
            export_conn.close()  # CRITICAL: This closes and finalizes the database file.

            # 4. Read the finalized database file into an in-memory byte buffer.
            with open(temp_db_path, 'rb') as f:
                db_bytes = f.read()

            # 5. Send the file from the in-memory buffer.
            return send_file(
                io.BytesIO(db_bytes),
                as_attachment=True,
                download_name=f"{table_name}_export.db",
                mimetype='application/vnd.sqlite3'  # Using the official MIME type for SQLite
            )

        finally:
            # 6. Securely clean up the temporary file from the server's disk.
            if temp_db_path and os.path.exists(temp_db_path):
                os.remove(temp_db_path)

    return jsonify({'error': 'Invalid format specified'}), 400
