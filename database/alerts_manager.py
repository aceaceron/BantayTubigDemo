# database/alerts_manager.py
"""
Manages all database operations for alerts, notifications, and history.
"""
import sqlite3
import json
import datetime
from .config import DB_PATH, DB_LOCK

# --- Alert Rule Management ---

def get_all_thresholds_as_dict():
    """
    Fetches all water quality thresholds from the database and organizes them
    into a nested dictionary for easy lookup.
    Example structure: {'pH': {'Good': [{'min': 6.5, 'max': 8.5}], 'Average': [...]}}
    """
    thresholds = {}
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM water_quality_thresholds").fetchall()
        conn.close()

        for row in rows:
            param = row['parameter_name']
            level = row['quality_level']
            
            if param not in thresholds:
                thresholds[param] = {}
            if level not in thresholds[param]:
                thresholds[param][level] = []
            
        thresholds[param][level].append({
            'min_value': row['min_value'], 
            'max_value': row['max_value']
        })
    return thresholds

def get_rule_by_id(rule_id):
    """Fetches a single alert rule by its ID."""
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            SELECT r.*, g.name as group_name 
            FROM alert_rules r
            LEFT JOIN notification_groups g ON r.notification_group_id = g.id
            WHERE r.id = ?
        ''', (rule_id,))
        rule = cursor.fetchone()
        conn.close()
        if rule:
            rule_dict = dict(rule)
            rule_dict['conditions'] = json.loads(rule_dict['conditions'])
            return rule_dict
    return None

def get_all_alert_rules():
    """Fetches all alert rules with their associated notification group name."""
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            SELECT r.*, g.name as group_name 
            FROM alert_rules r
            LEFT JOIN notification_groups g ON r.notification_group_id = g.id
            ORDER BY r.name
        ''')
        rules = [dict(row) for row in cursor.fetchall()]
        conn.close()
        # Decode the JSON string for conditions into a Python object
        for rule in rules:
            rule['conditions'] = json.loads(rule['conditions'])
    return rules

def snooze_alert_rule(rule_id, duration_minutes):
    """Updates a rule with a snooze timestamp."""
    snooze_end_time = datetime.datetime.now() + datetime.timedelta(minutes=duration_minutes)
    snooze_end_str = snooze_end_time.strftime("%Y-%m-%d %H:%M:%S")
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE alert_rules SET snoozed_until = ? WHERE id = ?", (snooze_end_str, rule_id))
        conn.commit()
        conn.close()

def get_active_alert_rules():
    """Fetches all enabled and non-snoozed alert rules from the database."""
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        # This query now filters out rules that are currently snoozed
        query = "SELECT * FROM alert_rules WHERE enabled = 1 AND (snoozed_until IS NULL OR snoozed_until < ?)"
        rows = conn.execute(query, (now_str,)).fetchall()
        conn.close()
        
        rule_list = []
        for row in rows:
            rule_dict = dict(row)
            rule_dict['conditions'] = json.loads(rule_dict['conditions'])
            rule_list.append(rule_dict)
    return rule_list

def add_alert_rule(data):
    """Adds a new alert rule to the database."""
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO alert_rules (name, conditions, notification_group_id, enabled, activate_buzzer, escalation_policy_id, buzzer_duration_seconds, buzzer_mode)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['name'],
            json.dumps(data['conditions']),
            data['notification_group_id'],
            data.get('enabled', True),
            data.get('activate_buzzer', False),
            data.get('escalation_policy_id'),
            data.get('buzzer_duration_seconds', 0),
            data.get('buzzer_mode', 'once') 
        ))
        conn.commit()
        new_id = cursor.lastrowid
        conn.close()
    return new_id

def update_alert_rule(rule_id, data):
    """Updates an existing alert rule."""
    with DB_LOCK:
        # These lines were missing
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE alert_rules
            SET name = ?, conditions = ?, notification_group_id = ?, enabled = ?, activate_buzzer = ?, escalation_policy_id = ?, buzzer_duration_seconds = ?, buzzer_mode = ?
            WHERE id = ?
        ''', (
            data['name'],
            json.dumps(data['conditions']),
            data['notification_group_id'],
            data.get('enabled', True),
            data.get('activate_buzzer', False),
            data.get('escalation_policy_id'),
            data.get('buzzer_duration_seconds', 0),
            data.get('buzzer_mode', 'once'),
            rule_id
        ))
        conn.commit()
        conn.close()

def restore_default_alert_rules():
    """
    Deletes all current default rules and re-inserts the pristine default set.
    """
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM alert_rules WHERE is_default = 1")

        # Get the 'Administrators' group ID, falling back to 1 if needed
        try:
            cursor.execute("SELECT id FROM notification_groups WHERE name = 'Administrators'")
            admin_group_row = cursor.fetchone()
            admin_group_id = admin_group_row[0] if admin_group_row else 1
        except:
            admin_group_id = 1

        # This list includes the 'buzzer_mode' data at the end
        default_alert_rules = [
            ('pH Level Critical (Low)', json.dumps([{'parameter': 'pH', 'operator': '<', 'value': '4.0'}]), admin_group_id, 1, 1, 1, 10, 'repeating'),
            ('pH Level Critical (High)', json.dumps([{'parameter': 'pH', 'operator': '>', 'value': '10.0'}]), admin_group_id, 1, 1, 1, 10, 'repeating'),
            ('High Turbidity Detected', json.dumps([{'parameter': 'Turbidity', 'operator': '>', 'value': '50.0'}]), admin_group_id, 1, 1, 1, 5, 'repeating'),
            ('High TDS Detected', json.dumps([{'parameter': 'TDS', 'operator': '>', 'value': '700.0'}]), admin_group_id, 1, 1, 1, 3, 'once')
        ]
        
        # The INSERT statement includes the 'buzzer_mode' column
        cursor.executemany("""
            INSERT INTO alert_rules 
            (name, conditions, notification_group_id, enabled, is_default, activate_buzzer, buzzer_duration_seconds, buzzer_mode) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, default_alert_rules)
        
        conn.commit()
        conn.close()
    
def delete_alert_rule(rule_id):
    """Deletes an alert rule from the database."""
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM alert_rules WHERE id = ?', (rule_id,))
        conn.commit()
        conn.close()


# --- Notification Group Management ---

def get_all_notification_groups():
    """Fetches all notification groups and counts their members."""
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            SELECT g.id, g.name, COUNT(gm.user_id) as member_count
            FROM notification_groups g
            LEFT JOIN group_members gm ON g.id = gm.group_id
            GROUP BY g.id, g.name
            ORDER BY g.name
        ''')
        groups = [dict(row) for row in cursor.fetchall()]
        conn.close()
    return groups

def get_notification_group_details(group_id):
    """Fetches a single group's details and its member IDs."""
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        group = conn.execute('SELECT * FROM notification_groups WHERE id = ?', (group_id,)).fetchone()
        if not group:
            conn.close()
            return None
        
        group_details = dict(group)
        members = conn.execute('SELECT user_id FROM group_members WHERE group_id = ?', (group_id,)).fetchall()
        group_details['members'] = [row['user_id'] for row in members]
        conn.close()
    return group_details

def add_notification_group(data):
    """Adds a new notification group and its members."""
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO notification_groups (name) VALUES (?)', (data['name'],))
        group_id = cursor.lastrowid

        members = [(group_id, int(user_id)) for user_id in data.get('members', [])]
        if members:
            cursor.executemany('INSERT INTO group_members (group_id, user_id) VALUES (?, ?)', members)
        
        conn.commit()
        conn.close()
    return group_id

def update_notification_group(group_id, data):
    """Updates a group's name and members."""
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('UPDATE notification_groups SET name = ? WHERE id = ?', (data['name'], group_id))
        
        # Easiest way to update members is to delete all existing and re-insert
        cursor.execute('DELETE FROM group_members WHERE group_id = ?', (group_id,))
        
        members = [(group_id, int(user_id)) for user_id in data.get('members', [])]
        if members:
            cursor.executemany('INSERT INTO group_members (group_id, user_id) VALUES (?, ?)', members)

        conn.commit()
        conn.close()

def delete_notification_group(group_id):
    """Deletes a notification group. Members are deleted automatically via CASCADE."""
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM notification_groups WHERE id = ?', (group_id,))
        conn.commit()
        conn.close()


# --- Alert History Management ---

def add_alert_to_history(rule, sensor_readings):
    """Adds a new triggered alert to the history log."""
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Create a detailed message about what triggered the alert
        details_list = []
        for condition in rule['conditions']:
            param = condition.get('parameter', 'N/A').lower()
            live_value = sensor_readings.get(param)
            if live_value is not None:
                details_list.append(f"{condition.get('parameter')} was {live_value:.2f}")
        details = ", ".join(details_list)

        cursor.execute('''
            INSERT INTO alert_history (timestamp, rule_id, details, status)
            VALUES (?, ?, ?, ?)
        ''', (timestamp, rule['id'], details, 'Triggered'))
        
        conn.commit()
        new_id = cursor.lastrowid
        conn.close()
    return new_id

def get_alert_status_by_id(history_id):
    """Fetches the current status of a specific alert from the history."""
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH)
        # Fetch a single column, which is more efficient
        cursor = conn.execute('SELECT status FROM alert_history WHERE id = ?', (history_id,))
        result = cursor.fetchone()
        conn.close()
    return result[0] if result else None
def get_alert_history(filters=None):
    """Fetches alert history, joining with rules and users for more details."""
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        # TODO: Add WHERE clauses based on filters
        cursor.execute('''
            SELECT 
                h.*, 
                r.name as rule_name, 
                u.full_name as acknowledged_by
            FROM alert_history h
            LEFT JOIN alert_rules r ON h.rule_id = r.id
            LEFT JOIN users u ON h.acknowledged_by_user_id = u.id
            ORDER BY h.timestamp DESC
        ''')
        history = [dict(row) for row in cursor.fetchall()]
        conn.close()
    return history

def acknowledge_alert(log_id, user_id):
    """Updates an alert's status to 'Acknowledged' in the history."""
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute('''
            UPDATE alert_history
            SET status = 'Acknowledged', 
                acknowledged_by_user_id = ?, 
                acknowledged_timestamp = ?
            WHERE id = ? AND status = 'Triggered'
        ''', (user_id, timestamp, log_id))
        conn.commit()
        conn.close()

def resolve_alert_in_history(log_id):
    """Updates an active alert's status to 'Resolved'."""
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # Only update alerts that are currently Triggered or Acknowledged
        cursor.execute("""
            UPDATE alert_history
            SET status = 'Resolved'
            WHERE id = ? AND status IN ('Triggered', 'Acknowledged')
        """, (log_id,))
        conn.commit()
        conn.close()

# --- Utility Functions ---

def get_all_users_for_groups():
    """Fetches a simplified list of all users (id and name) for group selection."""
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        users = conn.execute('SELECT id, full_name FROM users ORDER BY full_name').fetchall()
        conn.close()
    return [dict(user) for user in users]

# --- Escalation Policy Management ---

def get_all_escalation_policies():
    """Fetches all escalation policies."""
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM escalation_policies ORDER BY name')
        policies = [dict(row) for row in cursor.fetchall()]
        conn.close()
        # Decode the JSON string for the path into a Python object
        for policy in policies:
            policy['path'] = json.loads(policy['path'])
    return policies

def get_escalation_policy_by_id(policy_id):
    """Fetches a single escalation policy by its ID."""
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        policy = conn.execute('SELECT * FROM escalation_policies WHERE id = ?', (policy_id,)).fetchone()
        conn.close()

        if not policy:
            return None
        
        policy_dict = dict(policy)
        # Decode the JSON string for the path into a Python object
        policy_dict['path'] = json.loads(policy_dict['path'])
        return policy_dict

def add_escalation_policy(data):
    """Adds a new escalation policy to the database."""
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO escalation_policies (name, path) VALUES (?, ?)',
            (data['name'], json.dumps(data['path']))
        )
        conn.commit()
        new_id = cursor.lastrowid
        conn.close()
    return new_id

def update_escalation_policy(policy_id, data):
    """Updates an existing escalation policy."""
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE escalation_policies SET name = ?, path = ? WHERE id = ?',
            (data['name'], json.dumps(data['path']), policy_id)
        )
        conn.commit()
        conn.close()

def delete_escalation_policy(policy_id):
    """Deletes an escalation policy."""
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM escalation_policies WHERE id = ?', (policy_id,))
        conn.commit()
        conn.close()

def get_latest_triggered_alert():
    """

    Fetches the single most recent alert from history that is still in the 'Triggered' state.
    """
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        # We need the rule_id to be able to snooze the rule
        query = """
            SELECT h.id, h.details, r.name as rule_name, r.id as rule_id
            FROM alert_history h
            JOIN alert_rules r ON h.rule_id = r.id
            WHERE h.status = 'Triggered'
            ORDER BY h.timestamp DESC
            LIMIT 1
        """
        alert = conn.execute(query).fetchone()
        conn.close()
        return dict(alert) if alert else None


# --- Water Quality Threshold Management ---

def get_all_thresholds():
    """Fetches all water quality thresholds as a flat list for editing."""
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM water_quality_thresholds ORDER BY parameter_name, quality_level, min_value')
        thresholds = [dict(row) for row in cursor.fetchall()]
        conn.close()
    return thresholds

def update_threshold(threshold_id, data):
    """Updates the min and max values for a specific threshold entry."""
    # Convert empty strings from form to None for the database
    min_value = data.get('min_value') if data.get('min_value') != '' else None
    max_value = data.get('max_value') if data.get('max_value') != '' else None
    
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE water_quality_thresholds SET min_value = ?, max_value = ? WHERE id = ?',
            (min_value, max_value, threshold_id)
        )
        conn.commit()
        conn.close()

def restore_default_thresholds():
    """Deletes all current thresholds and re-inserts the default set."""
    default_thresholds = [
        # pH Thresholds
        ('pH', 'Good', 'primary', 6.5, 8.5), ('pH', 'Average', 'low', 6.0, 6.5),
        ('pH', 'Average', 'high', 8.5, 9.0), ('pH', 'Poor', 'low', 4.0, 6.0),
        ('pH', 'Poor', 'high', 9.0, 10.0), ('pH', 'Bad', 'low', None, 4.0),
        ('pH', 'Bad', 'high', 10.0, None),
        # TDS Thresholds
        ('TDS', 'Good', 'primary', None, 400.0), ('TDS', 'Average', 'primary', 400.0, 700.0),
        ('TDS', 'Poor', 'primary', 700.0, 1000.0), ('TDS', 'Bad', 'primary', 1000.0, None),
        # Turbidity Thresholds
        ('Turbidity', 'Good', 'primary', None, 5.0), ('Turbidity', 'Average', 'primary', 5.0, 50.0),
        ('Turbidity', 'Poor', 'primary', 50.0, 200.0), ('Turbidity', 'Bad', 'primary', 200.0, None),
        # Temperature Thresholds
        ('Temperature', 'Good', 'primary', 5.0, 30.0), ('Temperature', 'Average', 'low', 0.0, 5.0),
        ('Temperature', 'Average', 'high', 30.0, 35.0), ('Temperature', 'Bad', 'low', None, 0.0),
        ('Temperature', 'Bad', 'high', 35.0, None)
    ]
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # Delete all existing entries
        cursor.execute('DELETE FROM water_quality_thresholds')
        # Re-insert the default values
        cursor.executemany("""
            INSERT INTO water_quality_thresholds 
            (parameter_name, quality_level, range_identifier, min_value, max_value) 
            VALUES (?, ?, ?, ?, ?)
        """, default_thresholds)
        conn.commit()
        conn.close()