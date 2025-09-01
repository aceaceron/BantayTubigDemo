# app/routes/main_routes.py
from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/analytics')
def analytics():
    return render_template('analytics.html')

@main_bp.route('/devices')
def devices():
    return render_template('devices.html')

@main_bp.route('/users')
def user_management():
    return render_template('user_management.html')