# database/__init__.py
"""
This file makes the database functions available at the package level,
allowing for cleaner imports in other parts of the application.
"""
from .config import DB_PATH, DB_LOCK
from .setup import create_tables
from .data_manager import (
    insert_measurement, 
    insert_environmental_context,
    get_latest_data,
    get_context_for_latest_measurement,
    summarize_context_for_range,
    get_latest_reading_with_env,
    get_summarized_data_for_range,
    get_recent_timeseries_data,
    get_thresholds_for_dashboard 
)

from .device_manager import (
    get_all_devices, get_device_info, add_or_update_device, delete_device,
    update_sensor_calibration, get_calibration_formula, get_calibrations_for_device,
    restore_default_calibration, add_device_log, get_logs_for_device
)

from .user_manager import (
    hash_password, verify_password, generate_secure_password,
    create_user, add_user, update_user, set_user_status, reset_password_for_user,
    get_all_users_with_roles, get_user_by_id, get_technicians_and_admins,
    create_role, get_all_roles, get_role_by_id, add_role, update_role, delete_role, get_phone_numbers_for_group
)

from .audit_logger import add_audit_log, get_audit_logs

from .maintenance import cleanup_old_data 

from .alerts_manager import * 

from .ml_manager import (
    log_anomaly,
    save_forecast,
    get_latest_forecasts,
    get_unannotated_anomalies,
    save_annotation
)