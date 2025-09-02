# routes/view_routes.py
from flask import render_template, Blueprint, redirect, url_for, request, flash, session
from database import get_user_for_login, verify_password, update_last_login, add_audit_log
from auth.decorators import role_required

view_bp = Blueprint('view_bp', __name__)

# --- Public Routes (No Login Required) ---

@view_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handles the login process."""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = get_user_for_login(email)
        if user and verify_password(user['hashed_password'], password, user['salt']):
            update_last_login(user['id'])
            add_audit_log(
                user_id=user['id'], 
                component='Security', 
                action='Login Success', 
                status='Success', 
                ip_address=request.remote_addr,
                target=f"Email: {email}"
            )
            session['user_id'] = user['id']
            session['user_name'] = user['full_name']
            session['user_role'] = user['role_name']
            return redirect(url_for('view_bp.index'))
        else:
            user_id_for_log = user['id'] if user else None
            add_audit_log(
                user_id=user_id_for_log, 
                component='Security', 
                action='Login Attempt Failed', 
                status='Failure', 
                ip_address=request.remote_addr,
                target=f"Email: {email}",
                details={'reason': 'Invalid credentials'}
            )
            flash('Invalid email or password. Please try again.', 'error')
            return redirect(url_for('view_bp.login'))
    return render_template('login.html')

@view_bp.route('/logout')
def logout():
    """Clears the session and logs the user out."""
    user_id = session.get('user_id')
    user_name = session.get('user_name', 'Unknown User')

    add_audit_log(
        user_id=user_id,
        component='Security', 
        action='Logout', 
        status='Success', 
        ip_address=request.remote_addr,
        target=f"User: {user_name} (ID: {user_id})"
    )

    session.clear()
    flash('You have been successfully logged out.', 'success')
    return redirect(url_for('view_bp.login'))

@view_bp.route('/unauthorized')
@role_required('Administrator', 'Technician', 'Data Scientist', 'Viewer') 
def unauthorized():
    """Renders the custom 'Access Denied' page."""
    return render_template('unauthorized.html')

@view_bp.route('/setup')
def setup():
    """Renders the first-time setup page for WiFi."""
    return render_template('setup.html')

# --- Protected Routes (Login Required) ---

@view_bp.route('/')
@role_required('Administrator', 'Technician', 'Data Scientist', 'Viewer')
def index():
    """Renders the main dashboard page."""
    # <<< Tell the template that 'dashboard' is the active page >>>
    return render_template('index.html', active_page='dashboard')

@view_bp.route('/analytics')
@role_required('Administrator', 'Data Scientist')
def analytics():
    # <<< Tell the template that 'analytics' is the active page >>>
    return render_template('analytics.html', active_page='analytics')

@view_bp.route('/devices')
@role_required('Administrator', 'Technician')
def devices():
    # <<< Tell the template that 'devices' is the active page >>>
    return render_template('devices.html', active_page='devices')

@view_bp.route('/alerts')
@role_required('Administrator', 'Technician')
def alerts():
    # <<< Tell the template that 'alerts' is the active page >>>
    return render_template('alerts.html', active_page='alerts')

@view_bp.route('/machine-learning')
@role_required('Administrator', 'Data Scientist')
def machine_learning():
    # <<< Tell the template that 'machine_learning' is the active page >>>
    return render_template('machine_learning.html', active_page='machine_learning')

@view_bp.route('/users')
@role_required('Administrator')
def users():
    # <<< Tell the template that 'users' is the active page >>>
    return render_template('user_management.html', active_page='users')

@view_bp.route('/settings')
@role_required('Administrator', 'Technician', 'Data Scientist', 'Viewer')
def settings():
    # <<< Tell the template that 'settings' is the active page >>>
    return render_template('system_settings.html', active_page='settings')