# app.py

from flask import Flask, session, request, redirect, url_for, flash
from flask_socketio import join_room
from socketio_instance import socketio   # ✅ Use only this one
import os
from datetime import timedelta
import sqlite3
import mimetypes
from database.user_manager import is_user_active

# --- Import Blueprints from the 'routes' package ---
from routes.view_routes import view_bp
from routes.analytics_routes import analytics_bp
from routes.device_routes import device_bp
from routes.user_routes import user_bp
from routes.system_routes import system_bp
from routes.network_routes import network_bp
from routes.alerts_routes import alerts_bp
from routes.ml_routes import ml_bp

# --- Paths ---
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'bantaytubig.db')
static_folder_path = os.path.join(BASE_DIR, 'static')
template_folder_path = os.path.join(BASE_DIR, 'templates')

# Fix for font MIME type
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
    """
    app = Flask(
        __name__,
        static_folder=static_folder_path,
        template_folder=template_folder_path
    )

    # Secret key for sessions
    app.config['SECRET_KEY'] = 'a-very-secret-key-that-you-should-change'

    # Configure session lifetime
    timeout_minutes = int(get_setting_from_db('session_timeout', 15))
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=timeout_minutes)
    app.config['SETUP_MODE'] = False

    # --- Session + User checks ---
    @app.before_request
    def before_request_tasks():
        # Skip static files
        if request.path.startswith('/static/'):
            return

        # Skip login/logout
        login_url = url_for('view_bp.login')
        logout_url = url_for('view_bp.logout')
        if request.path in [login_url, logout_url]:
            return

        # Check if user session is still active
        if 'user_id' in session:
            if not is_user_active(session['user_id']):
                session.clear()
                flash('Your session has expired or your account has been deactivated. Please log in again.', 'error')
                return redirect(login_url)

    @app.before_request
    def make_session_permanent():
        session.permanent = True

    # --- Register Blueprints ---
    app.register_blueprint(view_bp, url_prefix='/')
    app.register_blueprint(analytics_bp, url_prefix='/analytics')
    app.register_blueprint(device_bp, url_prefix='/api')
    app.register_blueprint(user_bp, url_prefix='/api')
    app.register_blueprint(system_bp, url_prefix='/api')
    app.register_blueprint(network_bp, url_prefix='/api')
    app.register_blueprint(alerts_bp, url_prefix='/api')
    app.register_blueprint(ml_bp, url_prefix='/api')

    # --- Initialize SocketIO ---
    socketio.init_app(app)

    @socketio.on('join_room')
    def handle_join_room_event(data):
        """Adds the client to a room for broadcasting."""
        print(f"CLIENT-JOIN: A client ({request.sid}) joined the room '{data['room']}'")
        join_room(data['room'])

    return app


# --- App Execution ---
app = create_app()

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
