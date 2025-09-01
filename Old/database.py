# # database.py
# import sqlite3
# import threading
# import json
# import hashlib
# import os
# import secrets
# import string
# from datetime import datetime

# # --- Centralized Configuration ---
# DB_PATH = 'bantaytubig.db' 
# DB_LOCK = threading.Lock()

# def create_tables():
#     """
#     Creates all necessary tables for the application.
#     """
#     with DB_LOCK:
#         conn = sqlite3.connect(DB_PATH, check_same_thread=False)
#         cursor = conn.cursor()
        
#         # Table 1: Core sensor measurements
#         cursor.execute('''
#             CREATE TABLE IF NOT EXISTS measurements (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 timestamp TEXT NOT NULL,
#                 temperature REAL,
#                 ph REAL,
#                 ph_voltage REAL,
#                 tds REAL,
#                 tds_voltage REAL,
#                 turbidity REAL,
#                 turbidity_voltage REAL,
#                 water_quality TEXT
#             )
#         ''')
        
#         # Table 2: Environmental and contextual data
#         cursor.execute('''
#             CREATE TABLE IF NOT EXISTS environmental_context (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 measurement_id INTEGER,
#                 hour_of_day INTEGER,
#                 day_of_week INTEGER,
#                 month_of_year INTEGER,
#                 rainfall_mm REAL,
#                 air_temp_c REAL,
#                 wind_speed_kph REAL,
#                 pressure_mb REAL,
#                 days_since_calibration INTEGER,
#                 FOREIGN KEY (measurement_id) REFERENCES measurements (id)
#             )
#         ''')
        
#         # Table 3: Device management
#         cursor.execute('''
#             CREATE TABLE IF NOT EXISTS devices (
#                 id TEXT PRIMARY KEY, 
#                 name TEXT NOT NULL, 
#                 location TEXT, 
#                 water_source TEXT DEFAULT 'Water Service Provider',
#                 firmware TEXT DEFAULT '1.0',
#                 status TEXT NOT NULL, 
#                 sensors TEXT
#             )
#         ''')

#         # --- NEW: Separate table for individual sensor calibration data ---
#         cursor.execute('''
#             CREATE TABLE IF NOT EXISTS sensor_calibrations (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 device_id TEXT NOT NULL,
#                 sensor_type TEXT NOT NULL,
#                 last_calibration_date TEXT NOT NULL,
#                 slope REAL,
#                 offset REAL,
#                 is_default INTEGER DEFAULT 1,
#                 UNIQUE(device_id, sensor_type)
#             )
#         ''')

#         # Table 4: User roles
#         cursor.execute('''
#             CREATE TABLE IF NOT EXISTS roles (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 name TEXT UNIQUE NOT NULL,
#                 permissions TEXT
#             )
#         ''')

#         # Table 5: User accounts
#         cursor.execute('''
#             CREATE TABLE IF NOT EXISTS users (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 full_name TEXT NOT NULL,
#                 email TEXT UNIQUE NOT NULL,
#                 -- MODIFIED: Added phone_number column
#                 phone_number TEXT,
#                 role_id INTEGER,
#                 hashed_password TEXT NOT NULL,
#                 salt TEXT NOT NULL,
#                 status TEXT DEFAULT 'Active',
#                 last_login TEXT,
#                 FOREIGN KEY (role_id) REFERENCES roles (id)
#             )
#         ''')

#         # Table 6: System-wide audit log
#         cursor.execute('''
#             CREATE TABLE IF NOT EXISTS audit_log (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 timestamp TEXT NOT NULL,
#                 user_id INTEGER,
#                 component TEXT,
#                 action TEXT NOT NULL,
#                 target TEXT,
#                 details TEXT,
#                 status TEXT,
#                 ip_address TEXT,
#                 FOREIGN KEY (user_id) REFERENCES users (id)
#             )
#         ''')
        
#         # Table 7: Device-specific maintenance logs
#         cursor.execute('''
#             CREATE TABLE IF NOT EXISTS device_logs (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 device_id TEXT NOT NULL,
#                 user_id INTEGER,
#                 timestamp TEXT NOT NULL,
#                 notes TEXT NOT NULL,
#                 FOREIGN KEY (device_id) REFERENCES devices (id),
#                 FOREIGN KEY (user_id) REFERENCES users (id)
#             )
#         ''')
        
#         conn.commit()
#         conn.close()

# # --- Password Hashing Functions ---
# def hash_password(password, salt=None):
#     """Hashes a password with a salt. Generates a new salt if one isn't provided."""
#     if salt is None:
#         salt = os.urandom(16).hex()
#     salted_password = password.encode('utf-8') + salt.encode('utf-8')
#     hashed_password = hashlib.sha256(salted_password).hexdigest()
#     return hashed_password, salt

# def verify_password(stored_hashed_password, provided_password, salt):
#     """Verifies a provided password against a stored hash and salt."""
#     hashed_password, _ = hash_password(provided_password, salt)
#     return hashed_password == stored_hashed_password

# # --- Measurement & Context Functions ---
# def insert_measurement(timestamp, temperature, ph, ph_voltage, tds, tds_voltage, turbidity, turbidity_voltage, water_quality):
#     """Inserts a new sensor measurement and returns the ID of the new row."""
#     with DB_LOCK:
#         conn = sqlite3.connect(DB_PATH, check_same_thread=False)
#         cursor = conn.cursor()
#         cursor.execute("""
#             INSERT INTO measurements (timestamp, temperature, ph, ph_voltage, tds, tds_voltage, turbidity, turbidity_voltage, water_quality)
#             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
#         """, (timestamp, temperature, ph, ph_voltage, tds, tds_voltage, turbidity, turbidity_voltage, water_quality))
#         last_id = cursor.lastrowid
#         conn.commit()
#         conn.close()
#         return last_id

# def insert_environmental_context(measurement_id, hour_of_day, day_of_week, month_of_year, rainfall_mm, 
#                                  air_temp_c, wind_speed_kph, pressure_mb, days_since_calibration):
#     """Inserts a new row of contextual data linked to a specific measurement."""
#     with DB_LOCK:
#         conn = sqlite3.connect(DB_PATH, check_same_thread=False)
#         cursor = conn.cursor()
#         cursor.execute("""
#             INSERT INTO environmental_context (
#                 measurement_id, hour_of_day, day_of_week, month_of_year, rainfall_mm, 
#                 air_temp_c, wind_speed_kph, pressure_mb, days_since_calibration
#             )
#             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
#         """, (measurement_id, hour_of_day, day_of_week, month_of_year, rainfall_mm, 
#               air_temp_c, wind_speed_kph, pressure_mb, days_since_calibration))
#         conn.commit()
#         conn.close()

# def get_latest_data():
#     """Fetches the most recent measurement from the database."""
#     with DB_LOCK:
#         conn = sqlite3.connect(DB_PATH, check_same_thread=False)
#         conn.row_factory = sqlite3.Row
#         cursor = conn.cursor()
#         cursor.execute('SELECT * FROM measurements ORDER BY timestamp DESC LIMIT 1')
#         row = cursor.fetchone()
#         conn.close()
#     return dict(row) if row else None


# # --- MODIFIED: Updated to save slope and offset ---
# def update_sensor_calibration(device_id, sensor_type, date_str, slope, offset, is_default=0):
#     """
#     Adds or updates the calibration record for a single sensor on a device.
#     """
#     with DB_LOCK:
#         conn = sqlite3.connect(DB_PATH, check_same_thread=False)
#         cursor = conn.cursor()
#         cursor.execute("""
#             REPLACE INTO sensor_calibrations (device_id, sensor_type, last_calibration_date, slope, offset, is_default)
#             VALUES (?, ?, ?, ?, ?, ?)
#         """, (device_id, sensor_type, date_str, slope, offset, is_default))
#         conn.commit()
#         conn.close()

# # --- NEW: Function to get the specific calibration formula for a sensor ---
# def get_calibration_formula(device_id, sensor_type):
#     """Retrieves the active calibration formula (slope and offset) for a sensor."""
#     with DB_LOCK:
#         conn = sqlite3.connect(DB_PATH, check_same_thread=False)
#         conn.row_factory = sqlite3.Row
#         cursor = conn.cursor()
#         cursor.execute(
#             "SELECT slope, offset FROM sensor_calibrations WHERE device_id = ? AND sensor_type = ?",
#             (device_id, sensor_type)
#         )
#         row = cursor.fetchone()
#         conn.close()
#     return dict(row) if row else None

# # --- NEW: Function to get all calibration records for a device ---
# def get_calibrations_for_device(device_id):
#     """Retrieves all calibration records for a specific device."""
#     with DB_LOCK:
#         conn = sqlite3.connect(DB_PATH, check_same_thread=False)
#         conn.row_factory = sqlite3.Row
#         cursor = conn.cursor()
#         cursor.execute("SELECT sensor_type, last_calibration_date FROM sensor_calibrations WHERE device_id = ?", (device_id,))
#         rows = cursor.fetchall()
#         conn.close()
#     # Convert the list of rows into a dictionary for easy lookup: {'pH': '2025-08-13...', ...}
#     return {row['sensor_type']: row['last_calibration_date'] for row in rows}

# # --- NEW: Function to delete a custom calibration, restoring the default ---
# def restore_default_calibration(device_id, sensor_type):
#     """
#     Deletes a specific sensor's custom calibration record, effectively
#     restoring it to the hardcoded default.
#     """
#     with DB_LOCK:
#         conn = sqlite3.connect(DB_PATH, check_same_thread=False)
#         cursor = conn.cursor()
#         cursor.execute(
#             'DELETE FROM sensor_calibrations WHERE device_id = ? AND sensor_type = ?',
#             (device_id, sensor_type)
#         )
#         conn.commit()
#         conn.close()

# # --- User, Role, and Log Functions ---
# def create_role(name, permissions):
#     """Creates a new role."""
#     with DB_LOCK:
#         conn = sqlite3.connect(DB_PATH, check_same_thread=False)
#         cursor = conn.cursor()
#         cursor.execute("INSERT INTO roles (name, permissions) VALUES (?, ?)", (name, json.dumps(permissions)))
#         conn.commit()
#         conn.close()

# def create_user(full_name, email, password, role_name):
#     """Creates a new user."""
#     hashed_pass, salt = hash_password(password)
#     with DB_LOCK:
#         conn = sqlite3.connect(DB_PATH, check_same_thread=False)
#         cursor = conn.cursor()
#         cursor.execute("SELECT id FROM roles WHERE name = ?", (role_name,))
#         role_result = cursor.fetchone()
#         if not role_result:
#             raise ValueError(f"Role '{role_name}' not found.")
#         role_id = role_result[0]
#         cursor.execute(
#             "INSERT INTO users (full_name, email, role_id, hashed_password, salt) VALUES (?, ?, ?, ?, ?)",
#             (full_name, email, role_id, hashed_pass, salt)
#         )
#         conn.commit()
#         conn.close()
#         print(f"User '{email}' created successfully with role '{role_name}'.")

# def add_audit_log(user_id, component, action, target, status, ip_address, details=None):
#     """
#     Adds a new entry to the audit log.
    
#     Args:
#         user_id (int or None): The ID of the user performing the action (None for system actions).
#         component (str): The part of the system being affected (e.g., 'User Management').
#         action (str): A description of the action (e.g., 'User Created').
#         target (str): The object the action was performed on (e.g., a user's email).
#         status (str): The outcome of the action ('Success' or 'Failure').
#         ip_address (str): The originating IP address.
#         details (dict, optional): A dictionary of extra details to be stored as JSON.
#     """
#     timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#     details_json = json.dumps(details) if details else None

#     with DB_LOCK:
#         conn = sqlite3.connect(DB_PATH, check_same_thread=False)
#         cursor = conn.cursor()
#         cursor.execute(
#             """INSERT INTO audit_log (timestamp, user_id, component, action, target, status, ip_address, details) 
#                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
#             (timestamp, user_id, component, action, target, status, ip_address, details_json)
#         )
#         conn.commit()
#         conn.close()


# def get_technicians_and_admins():
#     """Retrieves all users with the role of 'Technician' or 'Administrator'."""
#     with DB_LOCK:
#         conn = sqlite3.connect(DB_PATH, check_same_thread=False)
#         conn.row_factory = sqlite3.Row
#         cursor = conn.cursor()
#         cursor.execute("""
#             SELECT u.id, u.full_name
#             FROM users u
#             JOIN roles r ON u.role_id = r.id
#             WHERE r.name IN ('Administrator', 'Technician') AND u.status = 'Active'
#             ORDER BY u.full_name ASC
#         """)
#         rows = cursor.fetchall()
#         conn.close()
#     return [dict(row) for row in rows]

# def add_device_log(device_id, user_id, notes):
#     """Adds a new maintenance log entry for a specific device."""
#     timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#     with DB_LOCK:
#         conn = sqlite3.connect(DB_PATH, check_same_thread=False)
#         cursor = conn.cursor()
#         cursor.execute(
#             "INSERT INTO device_logs (device_id, user_id, timestamp, notes) VALUES (?, ?, ?, ?)",
#             (device_id, user_id, timestamp, notes)
#         )
#         conn.commit()
#         conn.close()

# def get_logs_for_device(device_id):
#     """Retrieves all logs for a specific device."""
#     with DB_LOCK:
#         conn = sqlite3.connect(DB_PATH, check_same_thread=False)
#         conn.row_factory = sqlite3.Row
#         cursor = conn.cursor()
#         # MODIFIED: Changed to a LEFT JOIN to include logs with no user,
#         # and aliased 'timestamp' to 'date' for frontend compatibility.
#         # Also, if a user is not found, it defaults the tech name.
#         cursor.execute("""
#             SELECT 
#                 l.timestamp as date, 
#                 l.notes, 
#                 COALESCE(u.full_name, 'System') as tech 
#             FROM device_logs l
#             LEFT JOIN users u ON l.user_id = u.id
#             WHERE l.device_id = ? 
#             ORDER BY l.timestamp DESC
#         """, (device_id,))
#         rows = cursor.fetchall()
#         conn.close()
#     return [dict(row) for row in rows]

# # --- Device Management Functions ---
# def get_all_devices():
#     """Fetches all devices from the database."""
#     with DB_LOCK:
#         conn = sqlite3.connect(DB_PATH, check_same_thread=False)
#         conn.row_factory = sqlite3.Row
#         cursor = conn.cursor()
#         cursor.execute('SELECT * FROM devices')
#         rows = cursor.fetchall()
#         conn.close()
#     devices = []
#     for row in rows:
#         device = dict(row)
#         device['sensors'] = json.loads(device['sensors']) if device['sensors'] else []
#         devices.append(device)
#     return devices

# def add_or_update_device(device_data):
#     """Adds a new device or updates an existing one."""
#     sensors_json = json.dumps(device_data.get('sensors', []))
#     with DB_LOCK:
#         conn = sqlite3.connect(DB_PATH, check_same_thread=False)
#         cursor = conn.cursor()
#         cursor.execute("""
#             REPLACE INTO devices (id, name, location, water_source, firmware, status, sensors)
#             VALUES (?, ?, ?, ?, ?, ?, ?)
#         """, (
#             device_data['id'],
#             device_data['name'],
#             device_data.get('location'),
#             # MODIFIED: Added the water_source value to the tuple.
#             device_data.get('water_source'),
#             device_data.get('firmware'),
#             device_data.get('status', 'offline'),
#             sensors_json
#         ))
#         conn.commit()
#         conn.close()

# def delete_device(device_id):
#     """Deletes a device from the database by its ID."""
#     with DB_LOCK:
#         conn = sqlite3.connect(DB_PATH, check_same_thread=False)
#         cursor = conn.cursor()
#         cursor.execute('DELETE FROM devices WHERE id = ?', (device_id,))
#         conn.commit()
#         conn.close()


# # --- NEW USER & ROLE FUNCTIONS ---

# def populate_initial_roles():
#     """Adds predefined roles to the database if they don't exist."""
#     roles = [
#         ('Administrator', 'Full access to all system features.'),
#         ('Technician', 'Manage devices, sensors, and alerts.'),
#         ('Manager / Viewer', 'Read-only access to dashboards and reports.'),
#         ('Data Scientist', 'Access to analytics and machine learning models.')
#     ]
#     with DB_LOCK:
#         conn = sqlite3.connect(DB_PATH, check_same_thread=False)
#         cursor = conn.cursor()
#         cursor.executemany("INSERT OR IGNORE INTO roles (name, permissions) VALUES (?, ?)", roles)
#         conn.commit()
#         conn.close()

# def get_all_roles():
#     """Retrieves all roles from the database."""
#     with DB_LOCK:
#         conn = sqlite3.connect(DB_PATH, check_same_thread=False)
#         conn.row_factory = sqlite3.Row
#         cursor = conn.cursor()
#         # MODIFIED: Select all columns to get permissions as well
#         cursor.execute("SELECT id, name, permissions FROM roles ORDER BY name ASC")
#         rows = cursor.fetchall()
#         conn.close()
#     return [dict(row) for row in rows]

# def get_role_by_id(role_id):
#     """Retrieves a single role by its ID."""
#     with DB_LOCK:
#         conn = sqlite3.connect(DB_PATH, check_same_thread=False)
#         conn.row_factory = sqlite3.Row
#         cursor = conn.cursor()
#         cursor.execute("SELECT id, name, permissions FROM roles WHERE id = ?", (role_id,))
#         row = cursor.fetchone()
#         conn.close()
#     return dict(row) if row else None

# def add_role(name, permissions):
#     """Adds a new role to the database."""
#     with DB_LOCK:
#         conn = sqlite3.connect(DB_PATH, check_same_thread=False)
#         cursor = conn.cursor()
#         cursor.execute("INSERT INTO roles (name, permissions) VALUES (?, ?)", (name, permissions))
#         conn.commit()
#         conn.close()

# def update_role(role_id, name, permissions):
#     """Updates an existing role."""
#     with DB_LOCK:
#         conn = sqlite3.connect(DB_PATH, check_same_thread=False)
#         cursor = conn.cursor()
#         cursor.execute(
#             "UPDATE roles SET name = ?, permissions = ? WHERE id = ?",
#             (name, permissions, role_id)
#         )
#         conn.commit()
#         conn.close()

# def delete_role(role_id):
#     """Deletes a role from the database."""
#     # Note: In a production system, you might prevent deleting roles assigned to users.
#     with DB_LOCK:
#         conn = sqlite3.connect(DB_PATH, check_same_thread=False)
#         cursor = conn.cursor()
#         cursor.execute("DELETE FROM roles WHERE id = ?", (role_id,))
#         conn.commit()
#         conn.close()

# def get_all_users_with_roles():
#     """Retrieves all users with their assigned role name."""
#     with DB_LOCK:
#         conn = sqlite3.connect(DB_PATH, check_same_thread=False)
#         conn.row_factory = sqlite3.Row
#         cursor = conn.cursor()
#         # MODIFIED: Added u.phone_number to the SELECT statement
#         cursor.execute("""
#             SELECT u.id, u.full_name, u.email, u.phone_number, u.status, u.last_login, r.name as role_name, u.role_id
#             FROM users u
#             LEFT JOIN roles r ON u.role_id = r.id
#             ORDER BY u.full_name ASC
#         """)
#         rows = cursor.fetchall()
#         conn.close()
#     return [dict(row) for row in rows]

# def get_user_by_id(user_id):
#     with DB_LOCK:
#         conn = sqlite3.connect(DB_PATH, check_same_thread=False)
#         conn.row_factory = sqlite3.Row
#         cursor = conn.cursor()
#         cursor.execute("SELECT id, full_name, email, phone_number, role_id, status FROM users WHERE id = ?", (user_id,))
#         row = cursor.fetchone()
#         conn.close()
#     return dict(row) if row else None

# # --- NEW HELPER FUNCTION ---
# def generate_secure_password(length=6):
#     """Generates a random 6-character alphanumeric password."""
#     # Define the characters to use (letters and numbers only)
#     alphabet = string.ascii_letters + string.digits
#     return ''.join(secrets.choice(alphabet) for i in range(length))

# # --- MODIFIED add_user FUNCTION ---
# def add_user(full_name, email, role_id, phone_number):
#     """Adds a new user, including their phone number, and returns their credentials."""
#     temp_password = generate_secure_password()
#     hashed_pass, salt = hash_password(temp_password)
    
#     with DB_LOCK:
#         conn = sqlite3.connect(DB_PATH, check_same_thread=False)
#         cursor = conn.cursor()
#         # MODIFIED: Added phone_number to the INSERT statement
#         cursor.execute(
#             "INSERT INTO users (full_name, email, phone_number, role_id, hashed_password, salt, status) VALUES (?, ?, ?, ?, ?, ?, 'Active')",
#             (full_name, email, phone_number, role_id, hashed_pass, salt)
#         )
#         new_user_id = cursor.lastrowid
#         conn.commit()
#         conn.close()
        
#     return new_user_id, temp_password

# def update_user(user_id, full_name, role_id, phone_number):
#     """Updates a user's details, including their phone number."""
#     with DB_LOCK:
#         conn = sqlite3.connect(DB_PATH, check_same_thread=False)
#         cursor = conn.cursor()
#         # MODIFIED: Added phone_number to the UPDATE statement
#         cursor.execute(
#             "UPDATE users SET full_name = ?, role_id = ?, phone_number = ? WHERE id = ?",
#             (full_name, role_id, phone_number, user_id)
#         )
#         conn.commit()
#         conn.close()

# def set_user_status(user_id, status):
#     with DB_LOCK:
#         conn = sqlite3.connect(DB_PATH, check_same_thread=False)
#         cursor = conn.cursor()
#         cursor.execute("UPDATE users SET status = ? WHERE id = ?", (status, user_id))
#         conn.commit()
#         conn.close()

# def get_audit_logs(date_range=None, user_filter=None, action_filter=None):
#     """Retrieves audit logs with optional filters, joining with users and devices tables."""
#     with DB_LOCK:
#         conn = sqlite3.connect(DB_PATH, check_same_thread=False)
#         conn.row_factory = sqlite3.Row
#         cursor = conn.cursor()
        
#         query = """
#             SELECT a.timestamp, a.action, a.target, a.status, a.ip_address, a.details,
#                    a.component, COALESCE(u.full_name, 'System') as user_name
#             FROM audit_log a
#             LEFT JOIN users u ON a.user_id = u.id
#             WHERE 1=1
#         """
#         params = []
        
#         if user_filter:
#             query += " AND (u.email LIKE ? OR u.full_name LIKE ?)"
#             params.extend([f"%{user_filter}%", f"%{user_filter}%"])
#         if action_filter:
#             query += " AND a.action LIKE ?"
#             params.append(f"%{action_filter}%")
            
#         # MODIFIED: This logic now handles both single dates and date ranges
#         if date_range:
#             # Case 1: The filter is a range (e.g., "2025-08-06 to 2025-08-14")
#             if ' to ' in date_range:
#                 try:
#                     start, end = date_range.split(' to ')
#                     query += " AND a.timestamp BETWEEN ? AND ?"
#                     params.extend([f"{start} 00:00:00", f"{end} 23:59:59"])
#                 except ValueError:
#                     print(f"Invalid date range format: {date_range}")
#             # Case 2: The filter is a single day (e.g., "2025-08-06")
#             else:
#                 single_date = date_range.strip()
#                 query += " AND a.timestamp BETWEEN ? AND ?"
#                 params.extend([f"{single_date} 00:00:00", f"{single_date} 23:59:59"])

#         query += " ORDER BY a.timestamp DESC"
        
#         cursor.execute(query, params)
#         rows = cursor.fetchall()
#         conn.close()
#     return [dict(row) for row in rows]

# # --- NEW FUNCTION FOR PASSWORD RESETS ---
# def reset_password_for_user(user_id):
#     """
#     Generates a new secure 6-character password for a user, updates the database,
#     and returns the new password.
#     """
#     # MODIFIED: Changed to use the 6-character password generator
#     new_password = generate_secure_password()
#     hashed_pass, salt = hash_password(new_password)
    
#     with DB_LOCK:
#         conn = sqlite3.connect(DB_PATH, check_same_thread=False)
#         cursor = conn.cursor()
#         cursor.execute(
#             "UPDATE users SET hashed_password = ?, salt = ? WHERE id = ?",
#             (hashed_pass, salt, user_id)
#         )
#         conn.commit()
#         conn.close()
    
#     return new_password