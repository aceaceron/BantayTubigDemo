# database/__init__.py
"""
This file makes the database functions available at the package level,
allowing for cleaner imports in other parts of the application.
"""

# --- Core & Setup ---
from .config import DB_LOCK, DB_PATH
from .setup import create_tables

# --- Data & Measurements ---
from .data_manager import (
    get_context_for_latest_measurement,
    get_latest_data,
    get_latest_reading_with_env,
    get_recent_timeseries_data,
    get_summarized_data_for_range,
    get_thresholds_for_dashboard,
    insert_environmental_context,
    insert_measurement,
    summarize_context_for_range,
)

# --- Device & Sensor Management ---
from .device_manager import (
    add_device_log,
    add_or_update_device,
    delete_device,
    get_all_devices,
    get_calibration_formula,
    get_calibrations_for_device,
    get_device_info,
    get_logs_for_device,
    restore_default_calibration,
    update_sensor_calibration,
)

# --- User, Role & Auth Management ---
from .user_manager import (
    add_role,
    add_user,
    change_user_password,
    create_role,
    create_user,
    delete_role,
    generate_secure_password,
    get_all_roles,
    get_all_users_with_roles,
    get_phone_numbers_for_group,
    get_role_by_id,
    get_technicians_and_admins,
    get_user_by_id,
    get_user_for_login,
    hash_password,
    is_user_admin,
    reset_password_for_user,
    set_user_status,
    update_last_login,
    update_role,
    update_user,
    verify_password,
)

# --- Alerts & Notifications ---
from .alerts_manager import (
    acknowledge_alert,
    add_alert_rule,
    add_alert_to_history,
    add_escalation_policy,
    add_notification_group,
    delete_alert_rule,
    delete_escalation_policy,
    delete_notification_group,
    get_active_alert_rules,
    get_alert_history,
    get_alert_status_by_id,
    get_all_alert_rules,
    get_all_escalation_policies,
    get_all_notification_groups,
    get_all_thresholds_as_dict,
    get_all_users_for_groups,
    get_escalation_policy_by_id,
    get_latest_triggered_alert,
    get_notification_group_details,
    get_rule_by_id,
    restore_default_alert_rules,
    resolve_alert_in_history,
    snooze_alert_rule,
    update_alert_rule,
    update_escalation_policy,
    update_notification_group,
)

# --- Machine Learning ---
from .ml_manager import (
    get_latest_forecasts,
    get_unannotated_anomalies,
    log_anomaly,
    save_annotation,
    save_forecast,
)

# --- System & Maintenance ---
from .audit_logger import add_audit_log, get_audit_logs
from .maintenance import cleanup_old_data, get_deletable_data_preview