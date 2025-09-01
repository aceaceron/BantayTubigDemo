# routes/view_routes.py
"""
Contains all the routes for rendering the main HTML pages of the application,
including the captive portal logic.
"""
from flask import Blueprint, render_template, current_app, redirect, url_for, request

view_bp = Blueprint('view_bp', __name__)

# --- Standard Web Page Routes ---

@view_bp.route('/')
def index():
    return render_template('index.html')

@view_bp.route('/analytics')
def analytics():
    return render_template('analytics.html')

@view_bp.route('/devices')
def devices():
    return render_template('devices.html')

@view_bp.route('/users')
def user_management():
    return render_template('user_management.html')

@view_bp.route('/alerts')
def alerts():
    """Renders the Alerts & Notification page."""
    return render_template('alerts.html')

@view_bp.route('/settings')
def system_settings():
    return render_template('system_settings.html')

@view_bp.route('/setup')
def setup():
    return render_template('setup.html')

@view_bp.route('/machine-learning')
def ml_analytics():
    return render_template('machine_learning.html')
