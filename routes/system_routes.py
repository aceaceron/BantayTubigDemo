# routes/system_routes.py
"""
Contains routes for managing system-level settings, like the device name.
"""
from flask import Blueprint, jsonify, request
import sqlite3
import os
import signal 
import subprocess 
import threading
from database.maintenance import cleanup_old_data, get_deletable_data_preview

system_bp = Blueprint('system_bp', __name__)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DB_PATH = os.path.join(BASE_DIR, 'bantaytubig.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@system_bp.route('/system/settings', methods=['GET', 'POST'])
def manage_system_settings():
    """
    GET: Fetches all relevant system settings from the database.
    POST: Updates system settings in the database.
    """
    device_id = 'dev-1' # Assuming a single device system for now

    if request.method == 'GET':
        try:
            conn = get_db_connection()
            # Fetch the device name from the 'devices' table
            device = conn.execute("SELECT name FROM devices WHERE id = ?", (device_id,)).fetchone()
            # Fetch other settings from the 'settings' table
            settings_cursor = conn.execute("SELECT key, value FROM settings").fetchall()
            conn.close()

            settings = {row['key']: row['value'] for row in settings_cursor}
            
            response_data = {
                'systemName': device['name'] if device else 'BantayTubig',
                'sessionTimeout': settings.get('session_timeout', '15'),
                'dataRetention': settings.get('data_retention_days', '365'),
                'showMlConfidence': settings.get('show_ml_confidence', 'true') 
            }
            return jsonify(response_data)
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500

    if request.method == 'POST':
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'Request body cannot be empty.'}), 400
        try:
            conn = get_db_connection()
            
            # Update device name
            if 'systemName' in data:
                conn.execute("UPDATE devices SET name = ? WHERE id = ?", (data['systemName'], device_id))
            
            # Update/Insert other settings in the 'settings' table
            if 'sessionTimeout' in data:
                conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", 
                             ('session_timeout', str(data['sessionTimeout'])))
            if 'dataRetention' in data:
                conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", 
                             ('data_retention_days', str(data['dataRetention'])))
            if 'showMlConfidence' in data:
                conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", 
                             ('show_ml_confidence', str(data['showMlConfidence']).lower()))
            
            conn.commit()
            conn.close()
            return jsonify({'status': 'success', 'message': 'Settings updated successfully.'})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500


@system_bp.route('/system/retention-preview', methods=['POST'])
def get_retention_preview():
    """Provides a preview of data that would be deleted by a new policy."""
    data = request.get_json()
    days = data.get('retention_days')
    table = data.get('table_name')
    if not days or not table:
        return jsonify({'error': 'retention_days and table_name are required'}), 400
    
    preview_data = get_deletable_data_preview(table, int(days))
    return jsonify(preview_data)


@system_bp.route('/system/run-cleanup', methods=['POST'])
def run_cleanup_now():
    """Triggers the data retention cleanup process immediately."""
    try:
        cleanup_old_data()
        return jsonify({'status': 'success', 'message': 'Data cleanup process completed.'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    

@system_bp.route('/system/stop-main', methods=['POST'])
def stop_main_app():
    """
    Stops the main Python application by sending a SIGINT signal to its own process.
    This allows Flask's development server to shut down gracefully.
    """
    try:
        print("--- Received request to stop the application ---")
        # Get the process ID of the current Python script
        pid = os.getpid()
        # Send SIGINT (Ctrl+C) to the process
        os.kill(pid, signal.SIGINT)
        return jsonify({'status': 'success', 'message': 'Application is stopping...'})
    except Exception as e:
        print(f"Error stopping application: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
    
@system_bp.route('/system/power-off', methods=['POST'])
def power_off_sequence():
    """
    Schedules a system shutdown and then stops the application.
    This version includes enhanced error logging for diagnostics.
    """
    def shutdown_task():
        """The task that runs in a separate thread to shut down the Pi."""
        print("--- Shutdown scheduled. Powering off in 5 seconds. ---")
        threading.Event().wait(5)
        try:
            print("--- Executing shutdown command: ['sudo', '/sbin/shutdown', '-h', 'now'] ---")
            result = subprocess.run(
                ['sudo', '/sbin/shutdown', '-h', 'now'],
                check=True,
                capture_output=True,
                text=True
            )
            print(f"--- Shutdown command stdout: {result.stdout} ---")
        except subprocess.CalledProcessError as e:
            # This is the most likely error you will see
            print("--- SHUTDOWN COMMAND FAILED ---")
            print(f"--- Exit Code: {e.returncode}")
            print(f"--- Stderr (Error Message): {e.stderr.strip()}")
            print(f"--- Stdout: {e.stdout.strip()}")
        except Exception as e:
            print(f"--- AN UNEXPECTED PYTHON ERROR OCCURRED: {e} ---")

    try:
        shutdown_thread = threading.Thread(target=shutdown_task, daemon=True)
        shutdown_thread.start()

        def stop_app_task():
            threading.Event().wait(1)
            print(f"--- Stopping application (PID: {os.getpid()}) ---")
            os.kill(os.getpid(), signal.SIGINT)

        stop_thread = threading.Thread(target=stop_app_task, daemon=True)
        stop_thread.start()

        return jsonify({
            'status': 'success',
            'message': 'Shutdown initiated. Check application console for details.'
        })
    except Exception as e:
        print(f"Error initiating power-off sequence: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500