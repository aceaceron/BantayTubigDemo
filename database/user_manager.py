# database/user_manager.py
"""
Manages all database operations related to users, roles, and authentication.
"""
import sqlite3
import hashlib
import os
import secrets
import string
import json
import datetime
from .config import DB_PATH, DB_LOCK

# --- Password Hashing Functions ---

def hash_password(password, salt=None):
    """
    Hashes a password with a salt. Generates a new salt if one isn't provided.
    Returns the hashed password and the salt used.
    """
    if salt is None:
        salt = os.urandom(16).hex()
    salted_password = password.encode('utf-8') + salt.encode('utf-8')
    hashed_password = hashlib.sha256(salted_password).hexdigest()
    return hashed_password, salt

def verify_password(stored_hashed_password, provided_password, salt):
    """
    Verifies a provided password against a stored hash and salt.
    """
    hashed_password, _ = hash_password(provided_password, salt)
    return hashed_password == stored_hashed_password

def generate_secure_password(length=6):
    """
    Generates a random 6-character alphanumeric password for temporary use.
    """
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(length))

# --- User Management Functions ---

def get_user_for_login(email):
    """
    Retrieves essential user details for the login process.
    """
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        # <<< FIX: Added u.phone_number to the SELECT query >>>
        cursor.execute("""
            SELECT u.id, u.full_name, u.hashed_password, u.salt, u.phone_number, r.name as role_name
            FROM users u
            LEFT JOIN roles r ON u.role_id = r.id
            WHERE u.email = ? AND u.status = 'Active'
        """, (email,))
        row = cursor.fetchone()
        conn.close()
    return dict(row) if row else None

def update_last_login(user_id):
    """
    Updates the 'last_login' timestamp for a specific user to the current time.
    """
    # Get the current time in the correct format for the database.
    current_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        cursor = conn.cursor()
        # Execute the SQL UPDATE command.
        cursor.execute(
            "UPDATE users SET last_login = ? WHERE id = ?",
            (current_timestamp, user_id)
        )
        conn.commit()
        conn.close()

def create_user(full_name, email, password, role_name):
    """
    Creates a new user. (Note: This is an older function, prefer using add_user).
    """
    hashed_pass, salt = hash_password(password)
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM roles WHERE name = ?", (role_name,))
        role_result = cursor.fetchone()
        if not role_result:
            raise ValueError(f"Role '{role_name}' not found.")
        role_id = role_result[0]
        cursor.execute(
            "INSERT INTO users (full_name, email, role_id, hashed_password, salt) VALUES (?, ?, ?, ?, ?)",
            (full_name, email, role_id, hashed_pass, salt)
        )
        conn.commit()
        conn.close()
        print(f"User '{email}' created successfully with role '{role_name}'.")

def add_user(full_name, email, role_id, phone_number):
    """
    Adds a new user with a temporary password, returning the new user's ID and the password.
    """
    temp_password = generate_secure_password()
    hashed_pass, salt = hash_password(temp_password)
    
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (full_name, email, phone_number, role_id, hashed_password, salt, status) VALUES (?, ?, ?, ?, ?, ?, 'Active')",
            (full_name, email, phone_number, role_id, hashed_pass, salt)
        )
        new_user_id = cursor.lastrowid
        conn.commit()
        conn.close()
    return new_user_id, temp_password

def update_user(user_id, full_name, role_id, phone_number):
    """
    Updates an existing user's details.
    """
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET full_name = ?, role_id = ?, phone_number = ? WHERE id = ?",
            (full_name, role_id, phone_number, user_id)
        )
        conn.commit()
        conn.close()

def set_user_status(user_id, status):
    """
    Changes a user's status between 'Active' and 'Inactive'.
    """
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET status = ? WHERE id = ?", (status, user_id))
        conn.commit()
        conn.close()

def reset_password_for_user(user_id):
    """
    Generates a new secure password for a user, updates it in the database,
    and returns the new plain-text password.
    """
    new_password = generate_secure_password()
    hashed_pass, salt = hash_password(new_password)
    
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET hashed_password = ?, salt = ? WHERE id = ?",
            (hashed_pass, salt, user_id)
        )
        conn.commit()
        conn.close()
    return new_password

def change_user_password(user_id, current_password, new_password):
    """
    Changes a user's password after verifying their current password.
    Returns (True, "Success message") or (False, "Error message").
    """
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # 1. Fetch the user's current hash and salt
        cursor.execute("SELECT hashed_password, salt FROM users WHERE id = ?", (user_id,))
        user_data = cursor.fetchone()
        if not user_data:
            conn.close()
            return False, "User not found."

        # 2. Verify the provided current password
        if not verify_password(user_data['hashed_password'], current_password, user_data['salt']):
            conn.close()
            return False, "Incorrect current password."

        # 3. Hash the new password with a new salt
        new_hashed_password, new_salt = hash_password(new_password)

        # 4. Update the database with the new credentials
        cursor.execute(
            "UPDATE users SET hashed_password = ?, salt = ? WHERE id = ?",
            (new_hashed_password, new_salt, user_id)
        )
        conn.commit()
        conn.close()
    
    return True, "Password updated successfully."

def is_user_admin(email):
    """Checks if a user with a given email has the 'Administrator' role."""
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.name as role_name
            FROM users u
            JOIN roles r ON u.role_id = r.id
            WHERE u.email = ?
        """, (email,))
        user = cursor.fetchone()
        conn.close()
    if user and user['role_name'] == 'Administrator':
        return True
    return False

def set_new_password_for_user(user_id, new_password):
    """Generates a new hash and salt for a new password and updates the database."""
    new_hashed_password, new_salt = hash_password(new_password)
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET hashed_password = ?, salt = ? WHERE id = ?",
            (new_hashed_password, new_salt, user_id)
        )
        conn.commit()
        conn.close()
        
def get_all_users_with_roles():
    """
    Retrieves all users along with their assigned role name.
    """
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.id, u.full_name, u.email, u.phone_number, u.status, u.last_login, r.name as role_name, u.role_id
            FROM users u
            LEFT JOIN roles r ON u.role_id = r.id
            ORDER BY u.full_name ASC
        """)
        rows = cursor.fetchall()
        conn.close()
    return [dict(row) for row in rows]

def get_user_by_id(user_id):
    """
    Retrieves a single user's details by their ID.
    """
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT id, full_name, email, phone_number, role_id, status FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
    return dict(row) if row else None

def get_technicians_and_admins():
    """
    Retrieves all active users with the role of 'Technician' or 'Administrator'.
    """
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.id, u.full_name
            FROM users u
            JOIN roles r ON u.role_id = r.id
            WHERE r.name IN ('Administrator', 'Technician') AND u.status = 'Active'
            ORDER BY u.full_name ASC
        """)
        rows = cursor.fetchall()
        conn.close()
    return [dict(row) for row in rows]

def get_phone_numbers_for_group(group_id):
    """
    Fetches a list of valid phone numbers for all users in a specific group.
    """
    phone_numbers = []
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        # Join users and group_members tables to find users in the specified group
        query = """
            SELECT u.phone_number 
            FROM users u 
            JOIN group_members gm ON u.id = gm.user_id 
            WHERE gm.group_id = ?
        """
        cursor = conn.cursor()
        cursor.execute(query, (group_id,))
        rows = cursor.fetchall()
        conn.close()

        for row in rows:
            # Add the number only if it exists and looks like a valid number
            if row['phone_number'] and len(row['phone_number']) > 10:
                phone_numbers.append(row['phone_number'])
                
    return phone_numbers

# --- Role Management Functions ---

def create_role(name, permissions):
    """
    Creates a new user role.
    """
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO roles (name, permissions) VALUES (?, ?)", (name, json.dumps(permissions)))
        conn.commit()
        conn.close()

def get_all_roles():
    """
    Retrieves all roles from the database.
    """
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, permissions FROM roles ORDER BY name ASC")
        rows = cursor.fetchall()
        conn.close()
    return [dict(row) for row in rows]

def get_role_by_id(role_id):
    """
    Retrieves a single role by its ID.
    """
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, permissions FROM roles WHERE id = ?", (role_id,))
        row = cursor.fetchone()
        conn.close()
    return dict(row) if row else None

def add_role(name, permissions):
    """
    Adds a new role to the database.
    """
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO roles (name, permissions) VALUES (?, ?)", (name, permissions))
        conn.commit()
        conn.close()

def update_role(role_id, name, permissions):
    """
    Updates an existing role's name and permissions.
    """
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE roles SET name = ?, permissions = ? WHERE id = ?",
            (name, permissions, role_id)
        )
        conn.commit()
        conn.close()

def delete_role(role_id):
    """
    Deletes a role from the database.
    """
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM roles WHERE id = ?", (role_id,))
        conn.commit()
        conn.close()