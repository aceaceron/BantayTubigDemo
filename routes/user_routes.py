# routes/user_routes.py
"""
Handles all API endpoints for user management, role management, and authentication.
"""
from flask import Blueprint, jsonify, request, abort
from database import *

from config import CURRENT_USER_ID, set_current_user_id

user_bp = Blueprint('user_bp', __name__)

# --- Session & Authentication API ---

@user_bp.route('/set_current_user', methods=['POST'])
def set_current_user():
    """Sets the global user ID for the temporary session."""
    data = request.json
    user_id = data.get('userId')
    if user_id is not None:
        try:
            new_id = int(user_id)
            set_current_user_id(new_id) 
            user = get_user_by_id(new_id)
            user_name = user['full_name'] if user else 'Unknown User'
            add_audit_log(user_id=new_id, component='Security', action='Simulated Login', target=f"ID: {new_id}", status='Success', ip_address=request.remote_addr)
            return jsonify({"status": "success", "message": f"Current user set to {user_name}"})
        except (ValueError, TypeError):
            return jsonify({"status": "error", "message": "Invalid userId format"}), 400
    return jsonify({"status": "error", "message": "userId not provided"}), 400

# --- User Management API ---

@user_bp.route('/users', methods=['GET'])
def api_get_users():
    """Fetches a list of all users with their role names."""
    users = get_all_users_with_roles()
    return jsonify(users)

@user_bp.route('/users/<int:user_id>', methods=['GET'])
def api_get_user(user_id):
    """Fetches details for a single user."""
    user = get_user_by_id(user_id)
    if user:
        return jsonify(user)
    abort(404, "User not found")

@user_bp.route('/users/add', methods=['POST'])
def api_add_user():
    """Adds a new user to the system."""
    data = request.json
    try:
        new_user_id, plain_text_password = add_user(data['full_name'], data['email'], data['role_id'], data.get('phone_number'))
        add_audit_log(user_id=CURRENT_USER_ID, component='User Management', action='User Created', target=f"Email: {data['email']}", status='Success', ip_address=request.remote_addr)
        new_user_info = {"id": new_user_id, "name": data['full_name'], "email": data['email'], "phone_number": data.get('phone_number'), "password": plain_text_password}
        return jsonify({"status": "success", "newUser": new_user_info})
    except Exception as e:
        add_audit_log(user_id=CURRENT_USER_ID, component='User Management', action='User Created', target=f"Email: {data['email']}", status='Failure', ip_address=request.remote_addr, details={'error': str(e)})
        abort(400, f"Error creating user: {e}")

@user_bp.route('/users/update', methods=['POST'])
def api_update_user():
    """Updates an existing user's details."""
    data = request.json
    user_id_to_update = data.get('id')
    update_user(user_id_to_update, data['full_name'], data['role_id'], data.get('phone_number'))
    add_audit_log(user_id=CURRENT_USER_ID, component='User Management', action='User Updated', target=f"User ID: {user_id_to_update}", status='Success', ip_address=request.remote_addr)
    return jsonify({"status": "success", "message": "User updated."})

@user_bp.route('/users/set_status', methods=['POST'])
def api_set_user_status():
    """Changes a user's status between 'Active' and 'Inactive'."""
    data = request.json
    user_id_to_update = data.get('id')
    new_status = data.get('status')
    set_user_status(user_id_to_update, new_status)
    add_audit_log(user_id=CURRENT_USER_ID, component='User Management', action='User Status Changed', target=f"User ID: {user_id_to_update}", status='Success', ip_address=request.remote_addr, details={'new_status': new_status})
    return jsonify({"status": "success", "message": "User status updated."})

@user_bp.route('/users/reset_password', methods=['POST'])
def api_reset_user_password():
    """Resets a user's password and returns the new temporary password."""
    data = request.json
    user_id = data.get('id')
    user_info = get_user_by_id(user_id)
    if not user_info:
        abort(404, "User not found.")
    new_password = reset_password_for_user(user_id)
    add_audit_log(user_id=CURRENT_USER_ID, component='User Management', action='Password Reset', target=f"Email: {user_info['email']}", status='Success', ip_address=request.remote_addr)
    reset_user_info = {"name": user_info['full_name'], "email": user_info['email'], "phone_number": user_info.get('phone_number'), "password": new_password}
    return jsonify({"status": "success", "resetUser": reset_user_info})

@user_bp.route('/technicians', methods=['GET'])
def api_get_technicians():
    """Provides a list of users who are Administrators or Technicians."""
    users = get_technicians_and_admins()
    return jsonify(users)

# --- Role Management API ---

@user_bp.route('/roles', methods=['GET'])
def api_get_roles():
    """Fetches a list of all user roles."""
    roles = get_all_roles()
    return jsonify(roles)

@user_bp.route('/roles/<int:role_id>', methods=['GET'])
def api_get_role(role_id):
    """Fetches details for a single user role."""
    role = get_role_by_id(role_id)
    if role:
        return jsonify(role)
    abort(404, "Role not found")

@user_bp.route('/roles/add', methods=['POST'])
def api_add_role():
    """Adds a new user role."""
    data = request.json
    add_role(data['name'], data.get('permissions', ''))
    add_audit_log(user_id=CURRENT_USER_ID, component='Role Management', action='Role Created', target=f"Name: {data['name']}", status='Success', ip_address=request.remote_addr)
    return jsonify({"status": "success", "message": "Role added."})

@user_bp.route('/roles/update', methods=['POST'])
def api_update_role():
    """Updates an existing user role."""
    data = request.json
    update_role(data['id'], data['name'], data.get('permissions', ''))
    add_audit_log(user_id=CURRENT_USER_ID, component='Role Management', action='Role Updated', target=f"Role ID: {data['id']}", status='Success', ip_address=request.remote_addr)
    return jsonify({"status": "success", "message": "Role updated."})

@user_bp.route('/roles/delete', methods=['POST'])
def api_delete_role():
    """Deletes a user role."""
    data = request.json
    role_id = data.get('id')
    role = get_role_by_id(role_id)
    target_name = role['name'] if role else f"ID: {role_id}"
    delete_role(role_id)
    add_audit_log(user_id=CURRENT_USER_ID, component='Role Management', action='Role Deleted', target=target_name, status='Success', ip_address=request.remote_addr)
    return jsonify({"status": "success", "message": "Role deleted."})
