# database/setup.py
"""
Handles the initial setup of the database schema and default data.
"""
import sqlite3
import json
from .config import DB_PATH, DB_LOCK

def create_tables():
    """
    Creates all necessary tables for the application if they don't already exist.
    Also populates the 'roles' table with a default set of user roles.
    This function defines the entire database schema and its initial state.
    """
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        cursor = conn.cursor()
        
        # (Tables 1-14 remain the same)
        # ...
        
        # Table 1: Core sensor measurements
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS measurements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                temperature REAL,
                ph REAL,
                ph_voltage REAL,
                tds REAL,
                tds_voltage REAL,
                turbidity REAL,
                turbidity_voltage REAL,
                water_quality TEXT
            )
        ''')
        
        # Table 2: Environmental and contextual data
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS environmental_context (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                measurement_id INTEGER,
                hour_of_day INTEGER,
                day_of_week INTEGER,
                month_of_year INTEGER,
                rainfall_mm REAL,
                air_temp_c REAL,
                wind_speed_kph REAL,
                pressure_mb REAL,
                days_since_calibration INTEGER,
                FOREIGN KEY (measurement_id) REFERENCES measurements (id)
            )
        ''')
        
        # Table 3: Device management
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS devices (
                id TEXT PRIMARY KEY, 
                name TEXT NOT NULL, 
                location TEXT, 
                water_source TEXT DEFAULT 'Water Service Provider',
                firmware TEXT DEFAULT '1.0',
                status TEXT NOT NULL, 
                sensors TEXT
            )
        ''')

        # Table 4: Individual sensor calibration data
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sensor_calibrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                sensor_type TEXT NOT NULL,
                last_calibration_date TEXT NOT NULL,
                slope REAL,
                offset REAL,
                is_default INTEGER DEFAULT 1,
                UNIQUE(device_id, sensor_type)
            )
        ''')

        # Table 5: User roles
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                permissions TEXT
            )
        ''')

        # Table 6: User accounts
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                phone_number TEXT,
                role_id INTEGER,
                hashed_password TEXT NOT NULL,
                salt TEXT NOT NULL,
                status TEXT DEFAULT 'Active',
                last_login TEXT,
                FOREIGN KEY (role_id) REFERENCES roles (id)
            )
        ''')

        # Table 7: System-wide audit log
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                user_id INTEGER,
                component TEXT,
                action TEXT NOT NULL,
                target TEXT,
                details TEXT,
                status TEXT,
                ip_address TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Table 8: Device-specific maintenance logs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS device_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                user_id INTEGER,
                timestamp TEXT NOT NULL,
                notes TEXT NOT NULL,
                FOREIGN KEY (device_id) REFERENCES devices (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        # Table 9: System-wide settings (key-value store)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        ''')

        # Table 10: Defines the conditions that trigger an alert.
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alert_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                conditions TEXT NOT NULL,
                notification_group_id INTEGER,
                escalation_policy_id INTEGER,
                enabled INTEGER NOT NULL DEFAULT 1,
                is_default INTEGER NOT NULL DEFAULT 0,
                activate_buzzer INTEGER NOT NULL DEFAULT 0,
                buzzer_duration_seconds INTEGER NOT NULL DEFAULT 0,
                buzzer_mode TEXT NOT NULL DEFAULT 'once', -- 'once' or 'repeating'
                snoozed_until TEXT,
                FOREIGN KEY (notification_group_id) REFERENCES notification_groups (id)
            )
        ''')

        # Table 11: Defines groups of users to be notified.
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notification_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
        ''')

        # Table 12: Maps users to notification groups (many-to-many relationship).
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS group_members (
                group_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                PRIMARY KEY (group_id, user_id),
                FOREIGN KEY (group_id) REFERENCES notification_groups (id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        
        # Table 13: A complete log of every alert that has been triggered.
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alert_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                rule_id INTEGER NOT NULL,
                details TEXT,
                status TEXT NOT NULL, -- e.g., Triggered, Acknowledged, Resolved
                acknowledged_by_user_id INTEGER,
                acknowledged_timestamp TEXT,
                FOREIGN KEY (rule_id) REFERENCES alert_rules (id),
                FOREIGN KEY (acknowledged_by_user_id) REFERENCES users (id)
            )
        ''')

        # Table 14: Defines escalation policy workflows.
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS escalation_policies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                path TEXT NOT NULL -- Stored as a JSON string of steps
            )
        ''')
        
        # Table 15: Defines the thresholds for water quality classification.
        # Added 'range_identifier' to handle split ranges for a single quality level.
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS water_quality_thresholds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parameter_name TEXT NOT NULL,
                quality_level TEXT NOT NULL,
                range_identifier TEXT NOT NULL, -- e.g., 'primary', 'low', 'high'
                min_value REAL,
                max_value REAL,
                UNIQUE(parameter_name, quality_level, range_identifier)
            )
        ''')

        # Table to store detected anomalies
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ml_anomalies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                parameter TEXT NOT NULL,
                value REAL NOT NULL,
                severity REAL,
                anomaly_type TEXT, -- 'Issue' or 'Improvement'
                rca_suggestions TEXT, -- Stored as a JSON string
                is_annotated BOOLEAN DEFAULT 0
            )
        """)
        # Table to store user feedback
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ml_annotations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                anomaly_id INTEGER,
                user_id INTEGER,
                label TEXT NOT NULL, -- e.g., 'Pollution Event', 'Sensor Maintenance'
                comments TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (anomaly_id) REFERENCES ml_anomalies (id)
            )
        """)
        # Table to store time-series forecasts
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ml_forecasts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parameter TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                forecast_value REAL,
                lower_bound REAL,
                upper_bound REAL,
                generated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
            
         # <<< FIX: Define the default permissions for each role as a dictionary >>>
        # This structure is based directly on your @role_required decorators.
        admin_perms = {
            "dashboard": True, "analytics": True, "devices": True, 
            "alerts": True, "machine_learning": True, "users": True, "settings": True
        }
        technician_perms = {
            "dashboard": True, "analytics": False, "devices": True, 
            "alerts": True, "machine_learning": False, "users": False, "settings": True
        }
        data_scientist_perms = {
            "dashboard": True, "analytics": True, "devices": False, 
            "alerts": False, "machine_learning": True, "users": False, "settings": True
        }
        viewer_perms = {
            "dashboard": True, "analytics": False, "devices": False, 
            "alerts": False, "machine_learning": False, "users": False, "settings": True
        }

        # <<< Update the roles list to include the permissions object >>>
        roles_to_add = [
            ('Administrator', 'Full access to all system features.', admin_perms),
            ('Technician', 'Manage devices, sensors, and alerts.', technician_perms),
            ('Data Scientist', 'Access to analytics and machine learning models.', data_scientist_perms),
            ('Viewer', 'Read-only access to dashboards and reports.', viewer_perms)
        ]

        # <<< Iterate and insert roles one by one to handle JSON conversion >>>
        for name, description, permissions in roles_to_add:
            cursor.execute(
                "INSERT OR IGNORE INTO roles (name, description, permissions) VALUES (?, ?, ?)",
                (name, description, json.dumps(permissions))
            )

        default_settings = [
            ('session_timeout', '15'),
            ('data_retention_days', '365'),
            ('buzzer_duration_seconds', '1'),
            ('show_ml_confidence', 'true') 
        ]
        cursor.executemany("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", default_settings)

        try:
            cursor.execute("INSERT OR IGNORE INTO notification_groups (name) VALUES (?)", ('Administrators',))
            cursor.execute("SELECT id FROM notification_groups WHERE name = 'Administrators'")
            admin_group_row = cursor.fetchone()
            admin_group_id = admin_group_row[0] if admin_group_row else 1
            # Add user 1 to this group
            cursor.execute("INSERT OR IGNORE INTO group_members (group_id, user_id) VALUES (?, ?)", (admin_group_id, 1))
        except:
            admin_group_id = 1 # Fallback in case of any issue

        # Populate the water_quality_thresholds table with corrected data.
        # This now strictly follows your config without creating new quality levels.
        default_thresholds = [
            # pH Thresholds
            ('pH', 'Good', 'primary', 6.5, 8.5),
            ('pH', 'Average', 'low', 6.0, 6.5),
            ('pH', 'Average', 'high', 8.5, 9.0),
            ('pH', 'Poor', 'low', 4.0, 6.0),
            ('pH', 'Poor', 'high', 9.0, 10.0),
            ('pH', 'Bad', 'low', None, 4.0),
            ('pH', 'Bad', 'high', 10.0, None),
            # TDS Thresholds
            ('TDS', 'Good', 'primary', None, 400.0),
            ('TDS', 'Average', 'primary', 400.0, 700.0),
            ('TDS', 'Poor', 'primary', 700.0, 1000.0),
            ('TDS', 'Bad', 'primary', 1000.0, None),
            # Turbidity Thresholds
            ('Turbidity', 'Good', 'primary', None, 5.0),
            ('Turbidity', 'Average', 'primary', 5.0, 50.0),
            ('Turbidity', 'Poor', 'primary', 50.0, 200.0),
            ('Turbidity', 'Bad', 'primary', 200.0, None),
            # Temperature Thresholds
            ('Temperature', 'Good', 'primary', 5.0, 30.0),
            ('Temperature', 'Average', 'low', 0.0, 5.0),
            ('Temperature', 'Average', 'high', 30.0, 35.0),
            ('Temperature', 'Bad', 'low', None, 0.0),
            ('Temperature', 'Bad', 'high', 35.0, None)
        ]
        cursor.executemany("""
            INSERT OR IGNORE INTO water_quality_thresholds 
            (parameter_name, quality_level, range_identifier, min_value, max_value) 
            VALUES (?, ?, ?, ?, ?)
        """, default_thresholds)

        default_alert_rules = [
            # name, conditions, group_id, enabled, is_default, activate_buzzer, buzzer_duration, buzzer_mode
            ('pH Level Critical (Low)', json.dumps([{'parameter': 'pH', 'operator': '<', 'value': '4.0'}]), admin_group_id, 1, 1, 1, 10, 'repeating'),
            ('pH Level Critical (High)', json.dumps([{'parameter': 'pH', 'operator': '>', 'value': '10.0'}]), admin_group_id, 1, 1, 1, 10, 'repeating'),
            ('High Turbidity Detected', json.dumps([{'parameter': 'Turbidity', 'operator': '>', 'value': '50.0'}]), admin_group_id, 1, 1, 1, 5, 'repeating'),
            ('High TDS Detected', json.dumps([{'parameter': 'TDS', 'operator': '>', 'value': '700.0'}]), admin_group_id, 1, 1, 1, 3, 'once')
        ]
        
        cursor.executemany("""
            INSERT OR IGNORE INTO alert_rules 
            (name, conditions, notification_group_id, enabled, is_default, activate_buzzer, buzzer_duration_seconds, buzzer_mode) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, default_alert_rules)
        
        conn.commit()
        conn.close()