# routes/alerts_routes.py
"""
Handles all API endpoints for alert rules, notification groups, and alert history.
"""
from flask import Blueprint, jsonify, request, abort, session
from database import * # Imports all functions from the database package
from auth.decorators import role_required
from database.alerts_manager import get_all_thresholds, restore_default_thresholds, update_threshold

# A Blueprint is created to organize all alert-related routes.
alerts_bp = Blueprint('alerts_bp', __name__)

@alerts_bp.route('/alerts/latest_triggered', methods=['GET'])
def api_get_latest_triggered_alert():
    """Provides the latest, unacknowledged alert for the global notification banner."""
    alert = get_latest_triggered_alert()
    return jsonify(alert if alert else {})

# --- Alert Rules API Endpoints ---

@alerts_bp.route('/alerts/rules', methods=['GET'])
def api_get_alert_rules():
    """Fetches a list of all configured alert rules from the database."""
    rules = get_all_alert_rules()
    return jsonify(rules)

@alerts_bp.route('/alerts/rules', methods=['POST'])
def api_add_alert_rule():
    """Adds a new alert rule to the database."""
    data = request.json
    try:
        new_id = add_alert_rule(data)
        add_audit_log(
            user_id=session.get('user_id'), component='Alert Rules', action='Rule Created',
            target=f"Name: {data.get('name')}", status='Success', ip_address=request.remote_addr
        )
        return jsonify({"status": "success", "message": "Rule added successfully.", "id": new_id}), 201
    except Exception as e:
        add_audit_log(
            user_id=session.get('user_id'), component='Alert Rules', action='Rule Created',
            target=f"Name: {data.get('name')}", status='Failure', ip_address=request.remote_addr,
            details={'error': str(e)}
        )
        return jsonify({"status": "error", "message": str(e)}), 400

@alerts_bp.route('/alerts/rules/<int:rule_id>', methods=['PUT'])
def api_update_alert_rule(rule_id):
    """Updates an existing alert rule in the database."""
    data = request.json
    try:
        update_alert_rule(rule_id, data)
        add_audit_log(
            user_id=session.get('user_id'), component='Alert Rules', action='Rule Updated',
            target=f"Rule ID: {rule_id}", status='Success', ip_address=request.remote_addr
        )
        return jsonify({"status": "success", "message": "Rule updated successfully."})
    except Exception as e:
        add_audit_log(
            user_id=session.get('user_id'), component='Alert Rules', action='Rule Updated',
            target=f"Rule ID: {rule_id}", status='Failure', ip_address=request.remote_addr,
            details={'error': str(e)}
        )
        return jsonify({"status": "error", "message": str(e)}), 400

@alerts_bp.route('/alerts/rules/<int:rule_id>', methods=['DELETE'])
def api_delete_alert_rule(rule_id):
    """Deletes an alert rule from the database, preventing deletion of default rules."""
    try:
        # First, fetch the rule to check if it's a default rule
        rule_to_delete = get_rule_by_id(rule_id)
        if not rule_to_delete:
            abort(404, "Rule not found.")
        
        if rule_to_delete.get('is_default') == 1:
            # If it's a default rule, return an error
            return jsonify({"status": "error", "message": "Default rules cannot be deleted."}), 403

        # If it's not a default rule, proceed with deletion
        delete_alert_rule(rule_id)
        add_audit_log(
            user_id=session.get('user_id'), component='Alert Rules', action='Rule Deleted',
            target=f"Rule ID: {rule_id}", status='Success', ip_address=request.remote_addr
        )
        return jsonify({"status": "success", "message": "Rule deleted successfully."})
    except Exception as e:
        add_audit_log(
            user_id=session.get('user_id'), component='Alert Rules', action='Rule Deleted',
            target=f"Rule ID: {rule_id}", status='Failure', ip_address=request.remote_addr,
            details={'error': str(e)}
        )
        return jsonify({"status": "error", "message": str(e)}), 500
    
# --- Notification Groups API Endpoints ---

@alerts_bp.route('/alerts/groups', methods=['GET'])
def api_get_notification_groups():
    """Fetches a list of all configured notification groups."""
    groups = get_all_notification_groups()
    return jsonify(groups)

@alerts_bp.route('/alerts/groups/<int:group_id>', methods=['GET'])
def api_get_group_details(group_id):
    """Fetches details for a single group, including its members."""
    details = get_notification_group_details(group_id)
    if details:
        return jsonify(details)
    abort(404, "Group not found")
    
@alerts_bp.route('/alerts/groups', methods=['POST'])
def api_add_notification_group():
    """Adds a new notification group."""
    data = request.json
    try:
        new_id = add_notification_group(data)
        add_audit_log(
            user_id=session.get('user_id'), component='Notification Groups', action='Group Created',
            target=f"Name: {data.get('name')}", status='Success', ip_address=request.remote_addr
        )
        return jsonify({"status": "success", "message": "Group added successfully.", "id": new_id}), 201
    except Exception as e:
        add_audit_log(
            user_id=session.get('user_id'), component='Notification Groups', action='Group Created',
            target=f"Name: {data.get('name')}", status='Failure', ip_address=request.remote_addr,
            details={'error': str(e)}
        )
        return jsonify({"status": "error", "message": str(e)}), 400

@alerts_bp.route('/alerts/groups/<int:group_id>', methods=['PUT'])
def api_update_notification_group(group_id):
    """Updates a notification group."""
    data = request.json
    try:
        update_notification_group(group_id, data)
        add_audit_log(
            user_id=session.get('user_id'), component='Notification Groups', action='Group Updated',
            target=f"Group ID: {group_id}", status='Success', ip_address=request.remote_addr
        )
        return jsonify({"status": "success", "message": "Group updated successfully."})
    except Exception as e:
        add_audit_log(
            user_id=session.get('user_id'), component='Notification Groups', action='Group Updated',
            target=f"Group ID: {group_id}", status='Failure', ip_address=request.remote_addr,
            details={'error': str(e)}
        )
        return jsonify({"status": "error", "message": str(e)}), 400

@alerts_bp.route('/alerts/groups/<int:group_id>', methods=['DELETE'])
def api_delete_notification_group(group_id):
    """Deletes a notification group."""
    try:
        delete_notification_group(group_id)
        add_audit_log(
            user_id=session.get('user_id'), component='Notification Groups', action='Group Deleted',
            target=f"Group ID: {group_id}", status='Success', ip_address=request.remote_addr
        )
        return jsonify({"status": "success", "message": "Group deleted successfully."})
    except Exception as e:
        add_audit_log(
            user_id=session.get('user_id'), component='Notification Groups', action='Group Deleted',
            target=f"Group ID: {group_id}", status='Failure', ip_address=request.remote_addr,
            details={'error': str(e)}
        )
        return jsonify({"status": "error", "message": str(e)}), 400
    
# --- Escalation Policies API Endpoints ---

@alerts_bp.route('/alerts/policies', methods=['GET'])
def api_get_escalation_policies():
    """Fetches a list of all escalation policies."""
    try:
        policies = get_all_escalation_policies()
        return jsonify(policies)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@alerts_bp.route('/alerts/policies', methods=['POST'])
def api_add_escalation_policy():
    """Adds a new escalation policy."""
    data = request.json
    try:
        new_id = add_escalation_policy(data)
        add_audit_log(
            user_id=session.get('user_id'), component='Escalation Policies', action='Policy Created',
            target=f"Name: {data.get('name')}", status='Success', ip_address=request.remote_addr
        )
        return jsonify({"status": "success", "message": "Policy added successfully.", "id": new_id}), 201
    except Exception as e:
        add_audit_log(
            user_id=session.get('user_id'), component='Escalation Policies', action='Policy Created',
            target=f"Name: {data.get('name')}", status='Failure', ip_address=request.remote_addr,
            details={'error': str(e)}
        )
        return jsonify({"status": "error", "message": str(e)}), 400

@alerts_bp.route('/alerts/policies/<int:policy_id>', methods=['PUT'])
def api_update_escalation_policy(policy_id):
    """Updates an escalation policy."""
    data = request.json
    try:
        update_escalation_policy(policy_id, data)
        add_audit_log(
            user_id=session.get('user_id'), component='Escalation Policies', action='Policy Updated',
            target=f"Policy ID: {policy_id}", status='Success', ip_address=request.remote_addr
        )
        return jsonify({"status": "success", "message": "Policy updated successfully."})
    except Exception as e:
        add_audit_log(
            user_id=session.get('user_id'), component='Escalation Policies', action='Policy Updated',
            target=f"Policy ID: {policy_id}", status='Failure', ip_address=request.remote_addr,
            details={'error': str(e)}
        )
        return jsonify({"status": "error", "message": str(e)}), 400

@alerts_bp.route('/alerts/policies/<int:policy_id>', methods=['DELETE'])
def api_delete_escalation_policy(policy_id):
    """Deletes an escalation policy."""
    try:
        delete_escalation_policy(policy_id)
        add_audit_log(
            user_id=session.get('user_id'), component='Escalation Policies', action='Policy Deleted',
            target=f"Policy ID: {policy_id}", status='Success', ip_address=request.remote_addr
        )
        return jsonify({"status": "success", "message": "Policy deleted successfully."})
    except Exception as e:
        add_audit_log(
            user_id=session.get('user_id'), component='Escalation Policies', action='Policy Deleted',
            target=f"Policy ID: {policy_id}", status='Failure', ip_address=request.remote_addr,
            details={'error': str(e)}
        )
        return jsonify({"status": "error", "message": str(e)}), 400


# --- Water Quality Thresholds API Endpoints ---

@alerts_bp.route('/thresholds', methods=['GET'])
def api_get_thresholds():
    """Fetches all water quality thresholds for the editing table."""
    try:
        thresholds = get_all_thresholds()
        return jsonify(thresholds)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@alerts_bp.route('/thresholds/<int:threshold_id>', methods=['PUT'])
def api_update_threshold(threshold_id):
    """Updates a specific threshold's min/max values."""
    data = request.json
    try:
        update_threshold(threshold_id, data)
        # We don't need a full audit log for this simple change, but you could add one.
        return jsonify({"status": "success", "message": "Threshold updated."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@alerts_bp.route('/thresholds/restore', methods=['POST'])
def api_restore_thresholds():
    """Restores the water quality thresholds to their default values."""
    try:
        restore_default_thresholds()
        add_audit_log(
            user_id=session.get('user_id'), component='Thresholds', action='Defaults Restored',
            status='Success', ip_address=request.remote_addr
        )
        return jsonify({"status": "success", "message": "Default thresholds restored."})
    except Exception as e:
        add_audit_log(
            user_id=session.get('user_id'), component='Thresholds', action='Defaults Restored',
            status='Failure', ip_address=request.remote_addr, details={'error': str(e)}
        )
        return jsonify({"status": "error", "message": str(e)}), 500

# --- Alert History API Endpoints ---

@alerts_bp.route('/alerts/history', methods=['GET'])
def api_get_alert_history():
    """Fetches the alert history log, with optional filtering."""
    history = get_alert_history()
    return jsonify(history)

@alerts_bp.route('/alerts/history/<int:log_id>/acknowledge', methods=['POST'])
@role_required('Administrator', 'Technician') # Allow Admins and Techs to acknowledge
def api_acknowledge_alert(log_id):
    """Marks a specific alert in the history as 'Acknowledged'."""
    try:
        current_user_id = session.get('user_id')
        if not current_user_id:
             return jsonify({"status": "error", "message": "User not logged in."}), 401

        acknowledge_alert(log_id, current_user_id)
        add_audit_log(
            user_id=current_user_id, component='Alert Management', action='Alert Acknowledged',
            target=f"History ID: {log_id}", status='Success', ip_address=request.remote_addr
        )
        return jsonify({"status": "success", "message": "Alert acknowledged."})
    except Exception as e:
        add_audit_log(
            user_id=session.get('user_id'), component='Alert Management', action='Alert Acknowledged',
            target=f"History ID: {log_id}", status='Failure', ip_address=request.remote_addr,
            details={'error': str(e)}
        )
        return jsonify({"status": "error", "message": str(e)}), 400

@alerts_bp.route('/alerts/rules/<int:rule_id>', methods=['GET'])
def api_get_rule_details(rule_id):
    """Fetches details for a single alert rule."""
    rule = get_rule_by_id(rule_id)
    if rule:
        return jsonify(rule)
    abort(404, "Rule not found")

@alerts_bp.route('/alerts/rules/<int:rule_id>/snooze', methods=['POST'])
def api_snooze_rule(rule_id):
    """Snoozes a specific alert rule for a given duration."""
    data = request.json
    duration_minutes = data.get('duration_minutes')
    if not isinstance(duration_minutes, int) or duration_minutes <= 0:
        abort(400, "A valid duration in minutes is required.")
    try:
        snooze_alert_rule(rule_id, duration_minutes)
        add_audit_log(
            user_id=session.get('user_id'), component='Alert Rules', action='Rule Snoozed',
            target=f"Rule ID: {rule_id}", status='Success', ip_address=request.remote_addr,
            details={'duration_minutes': duration_minutes}
        )
        return jsonify({"status": "success", "message": f"Rule snoozed for {duration_minutes} minutes."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
        
# --- Utility API Endpoint ---

@alerts_bp.route('/alerts/users_for_groups', methods=['GET'])
def api_get_users_for_groups():
    """Provides a simplified list of users for populating group member forms."""
    users = get_all_users_for_groups()
    return jsonify(users)