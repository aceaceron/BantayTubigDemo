# routes/user_routes.py
"""
Handles all API endpoints for user management, role management, and authentication.
"""
from flask import Blueprint, jsonify, request, abort, session
from database import * 
import secrets
import time
from auth.decorators import role_required
from alerter import send_generic_sms
from database.user_manager import set_new_password_for_user, create_first_admin
from lcd_display import stop_status

user_bp = Blueprint('user_bp', __name__)


# In-memory store for reset codes. Format: {'email': {'code': '123456', 'expires': timestamp}}
_password_reset_codes = {}

# --- User Management API (Now Secured) ---

@user_bp.route('/users', methods=['GET'])
@role_required('Administrator', 'Technician') # Allow Admins and Techs to view user lists
def api_get_users():
    """Fetches a list of all users with their role names."""
    users = get_all_users_with_roles()
    return jsonify(users)

@user_bp.route('/users/<int:user_id>', methods=['GET'])
@role_required('Administrator')
def api_get_user(user_id):
    """Fetches details for a single user."""
    user = get_user_by_id(user_id)
    if user:
        return jsonify(user)
    abort(404, "User not found")

@user_bp.route('/users/add', methods=['POST'])
@role_required('Administrator')
def api_add_user():
    """Adds a new user to the system."""
    data = request.json
    try:
        new_user_id, plain_text_password = add_user(data['full_name'], data['email'], data['role_id'], data.get('phone_number'))
        add_audit_log(user_id=session.get('user_id'), component='User Management', action='User Created', target=f"Email: {data['email']}", status='Success', ip_address=request.remote_addr)
        new_user_info = {"id": new_user_id, "name": data['full_name'], "email": data['email'], "phone_number": data.get('phone_number'), "password": plain_text_password}
        return jsonify({"status": "success", "newUser": new_user_info})
    except Exception as e:
        add_audit_log(user_id=session.get('user_id'), component='User Management', action='User Created', target=f"Email: {data['email']}", status='Failure', ip_address=request.remote_addr, details={'error': str(e)})
        abort(400, f"Error creating user: {e}")

@user_bp.route('/users/update', methods=['POST'])
@role_required('Administrator')
def api_update_user():
    """Updates an existing user's details."""
    data = request.json
    user_id_to_update = data.get('id')
    update_user(user_id_to_update, data['full_name'], data['role_id'], data.get('phone_number'))
    add_audit_log(user_id=session.get('user_id'), component='User Management', action='User Updated', target=f"User ID: {user_id_to_update}", status='Success', ip_address=request.remote_addr)
    return jsonify({"status": "success", "message": "User updated."})

@user_bp.route('/users/set_status', methods=['POST'])
@role_required('Administrator')
def api_set_user_status():
    """Changes a user's status between 'Active' and 'Inactive'."""
    data = request.json
    user_id_to_update = data.get('id')
    new_status = data.get('status')
    set_user_status(user_id_to_update, new_status)
    add_audit_log(user_id=session.get('user_id'), component='User Management', action='User Status Changed', target=f"User ID: {user_id_to_update}", status='Success', ip_address=request.remote_addr, details={'new_status': new_status})
    return jsonify({"status": "success", "message": "User status updated."})

@user_bp.route('/users/reset_password', methods=['POST'])
@role_required('Administrator')
def api_reset_user_password():
    """Resets a user's password and returns the new temporary password."""
    data = request.json
    user_id = data.get('id')
    user_info = get_user_by_id(user_id)
    if not user_info:
        abort(404, "User not found.")
    new_password = reset_password_for_user(user_id)
    add_audit_log(user_id=session.get('user_id'), component='User Management', action='Password Reset', target=f"Email: {user_info['email']}", status='Success', ip_address=request.remote_addr)
    reset_user_info = {"name": user_info['full_name'], "email": user_info['email'], "phone_number": user_info.get('phone_number'), "password": new_password}
    return jsonify({"status": "success", "resetUser": reset_user_info})


@user_bp.route('/users/change_password', methods=['POST'])
@role_required('Administrator', 'Technician', 'Data Scientist', 'Viewer')
def api_change_password():
    """Changes the password for the currently logged-in user."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"status": "error", "message": "Authentication required."}), 401

    data = request.json
    current_password = data.get('current_password')
    new_password = data.get('new_password')

    if not all([current_password, new_password]):
        return jsonify({"status": "error", "message": "Missing required fields."}), 400

    success, message = change_user_password(user_id, current_password, new_password)
    
    # Define the target for the audit log
    log_target = f"User ID: {user_id}"

    if success:
        add_audit_log(user_id=user_id, component='Security', action='Password Changed', target=log_target, status='Success', ip_address=request.remote_addr)
        return jsonify({"status": "success", "message": message})
    else:
        add_audit_log(user_id=user_id, component='Security', action='Password Changed', target=log_target, status='Failure', ip_address=request.remote_addr, details={'reason': message})
        return jsonify({"status": "error", "message": message}), 400
    

@user_bp.route('/technicians', methods=['GET'])
@role_required('Administrator', 'Technician')
def api_get_technicians():
    """Provides a list of users who are Administrators or Technicians."""
    users = get_technicians_and_admins()
    return jsonify(users)

# --- Role Management API (Now Secured) ---
@user_bp.route('/roles/setup', methods=['GET'])
def api_get_roles_for_setup():
    """
    Publicly fetches roles, but ONLY if no users exist in the database.
    This is used for the initial administrator setup.
    """
    if get_all_users_with_roles():
        abort(403, "This endpoint is only available for initial setup.")
    roles = get_all_roles()
    return jsonify(roles)

@user_bp.route('/roles', methods=['GET'])
@role_required('Administrator')
def api_get_roles():
    """Fetches a list of all user roles."""
    roles = get_all_roles()
    return jsonify(roles)

@user_bp.route('/roles/<int:role_id>', methods=['GET'])
@role_required('Administrator')
def api_get_role(role_id):
    """Fetches details for a single user role."""
    role = get_role_by_id(role_id)
    if role:
        return jsonify(role)
    abort(404, "Role not found")

@user_bp.route('/roles/add', methods=['POST'])
@role_required('Administrator')
def api_add_role():
    data = request.json
    add_role(data['name'], data.get('description', ''), data.get('permissions', {}))
    add_audit_log(user_id=session.get('user_id'), component='Role Management', action='Role Created', target=f"Name: {data['name']}", status='Success', ip_address=request.remote_addr)
    return jsonify({"status": "success", "message": "Role added."})

@user_bp.route('/roles/update', methods=['POST'])
@role_required('Administrator')
def api_update_role():
    data = request.json
    update_role(data['id'], data['name'], data.get('description', ''), data.get('permissions', {}))
    add_audit_log(user_id=session.get('user_id'), component='Role Management', action='Role Updated', target=f"Role ID: {data['id']}", status='Success', ip_address=request.remote_addr)
    return jsonify({"status": "success", "message": "Role updated."})

@user_bp.route('/roles/delete', methods=['POST'])
@role_required('Administrator')
def api_delete_role():
    """Deletes a user role."""
    data = request.json
    role_id = data.get('id')
    role = get_role_by_id(role_id)
    target_name = role['name'] if role else f"ID: {role_id}"
    delete_role(role_id)
    add_audit_log(user_id=session.get('user_id'), component='Role Management', action='Role Deleted', target=target_name, status='Success', ip_address=request.remote_addr)
    return jsonify({"status": "success", "message": "Role deleted."})

@user_bp.route('/users/setup/create_first_admin', methods=['POST'])
def api_create_first_admin():
    """
    Creates the very first administrator account and logs them in.
    This endpoint only works if the users table is empty.
    """
    if get_all_users_with_roles():
        abort(403, "Cannot create first admin; user accounts already exist.")

    data = request.json
    password = data.get('password')
    if not password:
        abort(400, "Password is required.")
    
    if not all(k in data for k in ['full_name', 'email', 'role_id']):
        abort(400, "Missing required fields: full_name, email, role_id.")

    try:
        new_user_id = create_first_admin(
            data['full_name'], 
            data['email'], 
            password,
            data['role_id'], 
            data.get('phone_number')
        )
        
        # --- Automatically log the user in by creating a session ---
        session.clear()
        session['user_id'] = new_user_id
        session['user_name'] = data['full_name']
        session['user_role'] = 'Administrator' 

        add_audit_log(
            user_id=new_user_id, 
            component='System Setup', 
            action='First Admin Created & Logged In', 
            target=f"Email: {data['email']}", 
            status='Success', 
            ip_address=request.remote_addr
        )

        new_user_info = { "id": new_user_id, "name": data['full_name'], "email": data['email'] }
        return jsonify({"status": "success", "newUser": new_user_info})

    except Exception as e:
        add_audit_log(
            user_id=None, 
            component='System Setup', 
            action='First Admin Creation Failed', 
            target=f"Email: {data.get('email', 'N/A')}", 
            status='Failure', 
            ip_address=request.remote_addr, 
            details={'error': str(e)}
        )
        abort(400, f"Error creating first admin: {e}")


@user_bp.route('/users/check-admin-status', methods=['POST'])
def check_admin_status():
    """Checks if the provided email belongs to an admin."""
    email = request.json.get('email')
    if not email:
        return jsonify({"is_admin": False})
    
    is_admin = is_user_admin(email)
    return jsonify({"is_admin": is_admin})

@user_bp.route('/users/send-reset-code', methods=['POST'])
def send_reset_code():
    """Generates a reset code, stores it, and sends it via SMS."""
    email = request.json.get('email')
    user = get_user_for_login(email) # Re-use this function to get user details

    if not user or user['role_name'] != 'Administrator':
        return jsonify({"status": "error", "message": "User is not a valid administrator."}), 403
    
    if not user.get('phone_number'):
        return jsonify({"status": "error", "message": "Admin has no registered phone number."}), 400

    # Generate and store code
    code = str(secrets.randbelow(900000) + 100000) # 6-digit code
    _password_reset_codes[email] = {
        "code": code,
        "expires": time.time() + 600 # Code expires in 10 minutes
    }
    
    # Send SMS
    message = f"Your BantayTubig password reset code is: {code}. This code is valid for 10 minutes."
    send_generic_sms(user['phone_number'], message)

    add_audit_log(
        user_id=user['id'], 
        component='Security', 
        action='Password Reset Initiated', 
        status='Success', 
        ip_address=request.remote_addr,
        target=f"User: {user['full_name']}"
    )

    return jsonify({"status": "success", "message": "A reset code has been sent to the registered mobile number."})

@user_bp.route('/users/verify-reset-code', methods=['POST'])
def verify_reset_code():
    """
    Verifies a reset code. If valid, it returns a secure, single-use token 
    that authorizes the user to set a new password.
    """
    email = request.json.get('email')
    code = request.json.get('code')
    
    user_info = get_user_for_login(email)
    stored_info = _password_reset_codes.get(email)
    
    # Check for invalid or expired code
    if not stored_info or stored_info.get('code') != code or time.time() > stored_info.get('expires', 0):
        # This audit log will now work correctly.
        add_audit_log(
            user_id=user_info.get('id') if user_info else None, 
            component='Security', 
            action='Password Reset Failed', 
            status='Failure', 
            ip_address=request.remote_addr,
            target=f"Email: {email}",
            details={'reason': 'Invalid or expired verification code.'}
        )
        return jsonify({"status": "error", "message": "Invalid or expired verification code."}), 400
        
    reset_token = secrets.token_hex(16)
    # Update the stored info with the new token and a new, shorter expiration time.
    stored_info['token'] = reset_token
    stored_info['expires'] = time.time() + 300 # Token is valid for 5 minutes
    
    return jsonify({"status": "success", "message": "Verification successful.", "reset_token": reset_token})

@user_bp.route('/users/set-new-password', methods=['POST'])
def set_new_password():
    """Sets the new password for a user after token verification."""
    email = request.json.get('email')
    token = request.json.get('token')
    new_password = request.json.get('new_password')
    
    stored_info = _password_reset_codes.get(email)

    # Check for invalid or expired token
    if not stored_info or stored_info.get('token') != token or time.time() > stored_info.get('expires', 0):
        return jsonify({"status": "error", "message": "Invalid or expired reset token."}), 400
        
    # <<< FIX: Use the correct function to get user details. >>>
    user_info = get_user_for_login(email=email)
    if not user_info:
         return jsonify({"status": "error", "message": "User not found."}), 404
    
    # Set the new password in the database
    set_new_password_for_user(user_info['id'], new_password)
    
    del _password_reset_codes[email] # Clean up the used token
    
    add_audit_log(
        user_id=user_info['id'], 
        component='Security', 
        action='Password Reset Completed', 
        status='Success', 
        ip_address=request.remote_addr,
        target=f"User: {user_info['full_name']}"
    )
    
    return jsonify({"status": "success", "message": "Password has been successfully reset."})
