# app.py

from flask import Flask, session, request, redirect, url_for, flash
from flask_socketio import join_room
import os
from datetime import timedelta
import sqlite3 
from extensions import socketio 
import mimetypes
from database.user_manager import is_user_active

# --- Import Blueprints from the new 'routes' package ---
# These blueprints contain the organized routes for different
# parts of the application.
from routes.view_routes import view_bp
from routes.analytics_routes import analytics_bp
from routes.device_routes import device_bp
from routes.user_routes import user_bp
from routes.system_routes import system_bp
from routes.network_routes import network_bp 
from routes.alerts_routes import alerts_bp 
from routes.ml_routes import ml_bp 

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'bantaytubig.db')

# Determine the absolute path to the project directory
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Define paths for static and template folders relative to the base directory
static_folder_path = os.path.join(BASE_DIR, 'static')
template_folder_path = os.path.join(BASE_DIR, 'templates')

mimetypes.add_type('font/woff2', '.woff2')

def get_setting_from_db(key, default):
    """Helper function to get a single setting from the database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        conn.close()
        return row[0] if row else default
    except:
        return default

def create_app():
    """
    Creates and configures the Flask application.
    This factory pattern is useful for testing and scalability.
    """
    # Initialize the Flask app, specifying the custom folder paths
    app = Flask(
        __name__,
        static_folder=static_folder_path,
        template_folder=template_folder_path
    )
    
    # THIS FUNCTION NOW HANDLES ALL PRE-REQUEST TASKS
    @app.before_request
    def before_request_tasks():
        if 'user_id' in session:
            if request.path.startswith('/static/') or request.path in [url_for('view_bp.logout'), url_for('view_bp.login')]:
                return
            if not is_user_active(session['user_id']):
                session.clear()
                flash('Your session has expired or your account has been deactivated. Please log in again.', 'error')
                return redirect(url_for('view_bp.login'))

    # Add a secret key required for sessions
    app.config['SECRET_KEY'] = 'a-very-secret-key-that-you-should-change'

    # Configure session lifetime
    timeout_minutes = int(get_setting_from_db('session_timeout', 15))
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=timeout_minutes)

    app.config['SETUP_MODE'] = False

    # This function runs before each request to enforce the timeout
    @app.before_request
    def make_session_permanent():
        session.permanent = True

    # --- Register Blueprints ---
    # Each blueprint is registered with the app. A url_prefix can be
    # added to group all routes within that blueprint under a common path.

    # For rendering web pages (e.g., /, /analytics, /devices)
    app.register_blueprint(view_bp, url_prefix='/')

    # For all data and ML-related API endpoints (e.g., /analytics/latest, /analytics/thresholds)
    app.register_blueprint(analytics_bp, url_prefix='/analytics')

    # For API endpoints related to devices and users
    # This groups routes like /api/users, /api/devices/heartbeat etc.
    app.register_blueprint(device_bp, url_prefix='/api')
    app.register_blueprint(user_bp, url_prefix='/api')
    app.register_blueprint(system_bp, url_prefix='/api') 
    app.register_blueprint(network_bp, url_prefix='/api') 
    app.register_blueprint(alerts_bp, url_prefix='/api')
    app.register_blueprint(ml_bp, url_prefix='/api') 


    # Initialize SocketIO with the app
    socketio.init_app(app)


    @socketio.on('join_room')
    def handle_join_room_event(data):
        """Adds the client to a room for broadcasting."""
        print(f"CLIENT-JOIN: A client ({request.sid}) joined the room '{data['room']}'")
        join_room(data['room'])

    return app

# --- App Execution ---
# This section allows the Flask app to be run directly or by a WSGI server.
app = create_app()
