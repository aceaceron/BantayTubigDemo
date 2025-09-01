# alerter.py
import serial
import time
import RPi.GPIO as GPIO
import threading
import queue
import json

# Import only the necessary database functions
from database import (
    get_active_alert_rules, add_alert_to_history, resolve_alert_in_history,
    get_device_info, get_all_thresholds_as_dict,
    get_escalation_policy_by_id, get_alert_status_by_id, get_phone_numbers_for_group
)

from config import DEVICE_ID
from extensions import socketio

# Load thresholds from the DB once when the alerter starts up.
THRESHOLDS = get_all_thresholds_as_dict()

# --- CONFIGURATION & STATE ---
SERIAL_PORT = "/dev/ttyS0"  
BAUD_RATE = 9600    
BUZZER_PIN = 17  
ser = None
current_buzzer_thread = None
stop_buzzer_flag = threading.Event()
sms_queue = queue.Queue(maxsize=50)
_sms_worker_thread = None
_active_alerts = {}
_last_alert_times = {}
_escalation_threads = {}

# --- SMS QUEUE + WORKER ---
def start_sms_worker():
    global _sms_worker_thread
    if _sms_worker_thread is None or not _sms_worker_thread.is_alive():
        _sms_worker_thread = threading.Thread(target=_sms_worker_loop, daemon=True)
        _sms_worker_thread.start()

def _sms_worker_loop():
    while True:
        task = sms_queue.get()
        try:
            rule_name = task.get("rule_name")
            group_id = task.get("group_id")
            sensor_readings = task.get("sensor_readings")
            is_escalation = task.get("is_escalation", False)
            
            if not all([rule_name, group_id, sensor_readings]): continue

            target_numbers = get_phone_numbers_for_group(group_id)
            if not target_numbers: continue

            device_info = get_device_info(DEVICE_ID)
            location = device_info.get('location', 'Unknown Location') if device_info else 'Unknown Location'
            
            msg = build_alert_message(rule_name, sensor_readings, location, is_escalation)
            print(f"SMS WORKER: Sending alert for rule '{rule_name}' to group {group_id} ({len(target_numbers)} number(s)). Escalated: {is_escalation}")

            for number in target_numbers:
                send_sms_alert(number, msg)
                time.sleep(5)
        except Exception as e:
            print(f"SMS WORKER ERROR: {e}")
        finally:
            sms_queue.task_done()

def enqueue_sms(rule_name, group_id, sensor_readings, is_escalation=False):
    """Enqueues an SMS task with more detailed context."""
    task = {
        "rule_name": rule_name,
        "group_id": group_id,
        "sensor_readings": sensor_readings,
        "is_escalation": is_escalation
    }
    try:
        sms_queue.put_nowait(task)
    except queue.Full:
        try:
            sms_queue.get_nowait()
            sms_queue.task_done()
            sms_queue.put_nowait(task)
        except queue.Empty:
            pass

# --- SMS MESSAGE BUILDER (RULE-BASED) ---
def _fmt(val, nd=2):
    try: return f"{float(val):.{nd}f}"
    except (ValueError, TypeError): return "N/A"

def _now_local_str_12h():
    return time.strftime("%Y-%m-%d %I:%M:%S %p", time.localtime())

def build_alert_message(rule_name, sensor_readings, location, is_escalation=False):
    """Builds a detailed SMS alert message based on the specific rule that was triggered."""
    ts = _now_local_str_12h()
    alert_title = f"BantayTubig {'ESCALATION' if is_escalation else 'ALERT'}: {rule_name}"
    reason_lines = []
    param_map = {'temperature': 'Temp', 'ph': 'pH', 'tds': 'TDS', 'turbidity': 'Turb'}
    for key, name in param_map.items():
        if key in sensor_readings and sensor_readings[key] is not None:
             reason_lines.append(f"{name}:{_fmt(sensor_readings[key])}")
    reason = "Readings: " + " ".join(reason_lines)
    action = "Action: Please check the system and acknowledge the alert.\nGawin: Paki-check ang system at i-acknowledge ang alert."
    
    location_str = "Unknown Location"
    try:
        location_data = json.loads(location)
        if isinstance(location_data, dict):
            parts = [location_data.get('coordinates'), location_data.get('municipality'), location_data.get('province')]
            location_str = ", ".join(filter(None, parts))
    except (json.JSONDecodeError, TypeError):
        if isinstance(location, str) and location:
            location_str = location

    return "\n".join([alert_title, f"Time: {ts}", f"Location: {location_str}", reason, action])

# --- Serial Port & AT Commands ---
def setup_serial():
    global ser
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        ser.flushInput(); ser.flushOutput()
        print(f"Serial port {SERIAL_PORT} opened successfully.")
        time.sleep(20)
        return True
    except serial.SerialException as e:
        print(f"Error opening serial port: {e}")
        ser = None
        return False

def close_serial():
    global ser
    if ser and ser.is_open:
        ser.close()
        ser = None

def send_at_command(command, expected_response="OK", timeout=5):
    if not ser: return False, "Serial port not open"
    ser.flushInput()
    ser.write(f"{command}\r\n".encode())
    start_time = time.time()
    response = ""
    while time.time() - start_time < timeout:
        if ser.in_waiting > 0:
            response += ser.read(ser.in_waiting).decode()
            if expected_response in response:
                return True, response
        time.sleep(0.1)
    return False, response

def check_sim_status(max_attach_seconds=120):
    if not ser: return False, "Serial not initialized"
    send_at_command("ATE0")
    send_at_command("AT+CMEE=2")
    sim_ready = False
    last_resp = ""
    for _ in range(5):
        ok, resp = send_at_command("AT+CPIN?", "+CPIN: READY", timeout=6)
        last_resp = resp
        if ok:
            sim_ready = True
            break
        time.sleep(1)
    if not sim_ready: return False, "No SIM" if "SIM NOT INSERTED" in last_resp else "SIM not ready"
    ok, resp = send_at_command("AT+CFUN?", "OK", timeout=5)
    if ok and "+CFUN: 1" not in resp:
        send_at_command("AT+CFUN=1", "OK", timeout=10)
    send_at_command("AT+COPS=0", "OK", timeout=20)
    start = time.time()
    cfun_cycled = False
    while time.time() - start < max_attach_seconds:
        ok_reg, reg = send_at_command("AT+CREG?", "OK", timeout=8)
        if ok_reg and "+CREG:" in reg:
            try:
                stat = int(reg.split("+CREG:")[1].split(",")[1].strip().split("\r")[0])
                if stat in (1, 5): return True, "Ready"
                if stat == 3: return False, "Registration denied"
            except Exception: pass
        time.sleep(5)
        if not cfun_cycled and (time.time() - start > 45):
            send_at_command("AT+CFUN=0", "OK", timeout=10)
            time.sleep(3)
            send_at_command("AT+CFUN=1", "OK", timeout=10)
            time.sleep(10)
            cfun_cycled = True
    return False, "Searching"

def send_sms_alert(number, message):
    if not ser: return False
    sim_ready, status_msg = check_sim_status()
    if not sim_ready: return False
    if not send_at_command("AT+CMGF=1")[0]: return False
    ser.write(f"AT+CMGS=\"{number}\"\r\n".encode())
    time.sleep(0.5)
    response_buffer = ""
    start_time = time.time()
    while time.time() - start_time < 5:
        if ser.in_waiting > 0:
            char = ser.read(1).decode()
            response_buffer += char
            if '>' in response_buffer:
                break
        time.sleep(0.05)
    else:
        return False
    ser.write(f"{message}\x1A".encode())
    success, resp = send_at_command("", "OK", timeout=20)
    return "+CMGS:" in resp and "OK" in resp

# --- GPIO Setup & Buzzer ---
def setup_gpio():
    try:
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(BUZZER_PIN, GPIO.OUT)
        return True
    except Exception as e:
        print(f"Error setting up GPIO: {e}")
        return False

def destroy_gpio():
    try:
        GPIO.cleanup()
        print("GPIO cleanup complete.")
    except Exception as e:
        print(f"Error during GPIO cleanup: {e}")

def repeating_buzz_thread(duration, pause):
    while not stop_buzzer_flag.is_set():
        GPIO.output(BUZZER_PIN, GPIO.HIGH)
        time.sleep(duration)
        GPIO.output(BUZZER_PIN, GPIO.LOW)
        if not stop_buzzer_flag.is_set():
            time.sleep(pause)

def start_repeating_buzz(duration, pause):
    global current_buzzer_thread
    stop_buzzer()
    stop_buzzer_flag.clear()
    current_buzzer_thread = threading.Thread(target=repeating_buzz_thread, args=(duration, pause))
    current_buzzer_thread.daemon = True
    current_buzzer_thread.start()

def stop_buzzer():
    global current_buzzer_thread
    if current_buzzer_thread and current_buzzer_thread.is_alive():
        stop_buzzer_flag.set()
        current_buzzer_thread.join(timeout=1.0)
    try:
        GPIO.output(BUZZER_PIN, GPIO.LOW)
    except: pass
    current_buzzer_thread = None

# --- ALERT MANAGER (FULL LIFECYCLE) ---
def _format_conditions(conditions):
    if not conditions: return "N/A"
    parts = [f"{c.get('parameter', '?')} {c.get('operator', '?')} {c.get('value', '?')}" for c in conditions]
    return ", ".join(parts)

def _is_rule_triggered(rule, sensor_readings):
    try:
        for condition in rule['conditions']:
            parameter = condition.get('parameter', '').lower()
            live_value = sensor_readings.get(parameter)
            if live_value is None: return False
            value = float(condition.get('value'))
            operator = condition.get('operator')
            if operator == '>' and not (live_value > value): return False
            elif operator == '<' and not (live_value < value): return False
            elif operator == '=' and not (live_value == value): return False
            elif operator == '>=' and not (live_value >= value): return False
            elif operator == '<=' and not (live_value <= value): return False
        return True
    except (ValueError, TypeError):
        return False
    
def _escalation_worker(history_id, policy_id, rule_name, initial_sensor_readings):
    """This function runs in a background thread to manage the lifecycle of a single escalation."""
    try:
        print(f"ESCALATION WORKER (History ID: {history_id}): Started for policy {policy_id}.")
        policy = get_escalation_policy_by_id(policy_id)
        if not policy or not policy.get('path'):
            print(f"ESCALATION WORKER (History ID: {history_id}): No policy or path found. Exiting.")
            return
        for step in policy['path']:
            wait_minutes = int(step.get('wait_minutes', 0))
            next_group_id = step.get('group_id')
            if wait_minutes <= 0 or not next_group_id: continue
            print(f"ESCALATION WORKER (History ID: {history_id}): Waiting for {wait_minutes} minute(s)...")
            time.sleep(wait_minutes * 60)
            current_status = get_alert_status_by_id(history_id)
            print(f"ESCALATION WORKER (History ID: {history_id}): Wait finished. Current alert status is '{current_status}'.")
            if current_status == 'Triggered':
                print(f"ESCALATION WORKER (History ID: {history_id}): Alert unacknowledged. Escalating to group {next_group_id}.")
                enqueue_sms(
                    rule_name=rule_name,
                    group_id=next_group_id,
                    sensor_readings=initial_sensor_readings,
                    is_escalation=True
                )
            else:
                print(f"ESCALATION WORKER (History ID: {history_id}): Alert has been handled. Stopping escalation.")
                break
    except Exception as e:
        print(f"ESCALATION WORKER (History ID: {history_id}): An error occurred: {e}")
    finally:
        if history_id in _escalation_threads:
            del _escalation_threads[history_id]
        print(f"ESCALATION WORKER (History ID: {history_id}): Finished and cleaned up.")

def _trigger_new_alert_actions(rule, sensor_readings):
    """Handles the buzzer, SMS, history, and WebSocket actions for a new alert."""
    rule_id = rule['id']
    now = time.time()
    last_sent = _last_alert_times.get(rule_id, 0)

    if now - last_sent > 300: # 5-minute throttle
        print(f"ALERT: Rule '{rule['name']}' triggered. Executing actions.")
        try:
            history_id = add_alert_to_history(rule, sensor_readings)
            _active_alerts[rule_id] = history_id
            print(f" -> Successfully logged alert (ID: {history_id}).")

            alert_data = {
                'id': history_id,
                'rule_id': rule_id,
                'rule_name': rule['name'],
                'details': f"Condition met: {_format_conditions(rule['conditions'])}"
            }
            socketio.emit('new_alert', alert_data, to='broadcast_room')
            print(f" -> Emitted 'new_alert' event via WebSocket.")

            # Send the initial SMS notification
            enqueue_sms(
                rule_name=rule.get('name'),
                group_id=rule.get('notification_group_id'),
                sensor_readings=sensor_readings,
                is_escalation=False
            )
            _last_alert_times[rule_id] = now
            
            # Start the escalation worker if a policy is attached
            policy_id = rule.get('escalation_policy_id')
            if policy_id and history_id not in _escalation_threads:
                print(f" -> Escalation policy {policy_id} found. Starting escalation worker thread.")
                escalation_thread = threading.Thread(
                    target=_escalation_worker,
                    args=(history_id, policy_id, rule.get('name'), sensor_readings),
                    daemon=True
                )
                _escalation_threads[history_id] = escalation_thread
                escalation_thread.start()
        except Exception as e:
            print(f" -> ACTION ERROR: {e}")
        
def check_rules_and_trigger_alerts(sensor_readings):
    """Manages the full alert lifecycle: triggering new alerts and auto-resolving cleared ones."""
    try:
        alertable_rules = get_active_alert_rules()
    except Exception as e:
        print(f"ALERTER ERROR: Could not fetch alert rules: {e}")
        return

    triggered_rules = [rule for rule in alertable_rules if _is_rule_triggered(rule, sensor_readings)]
    triggered_rule_ids = {rule['id'] for rule in triggered_rules}

    for rule in triggered_rules:
        if rule['id'] not in _active_alerts:
            _trigger_new_alert_actions(rule, sensor_readings)

    resolved_rule_ids = set(_active_alerts.keys()) - triggered_rule_ids
    if resolved_rule_ids:
        for rule_id in resolved_rule_ids:
            history_log_id = _active_alerts.pop(rule_id)
            print(f"INFO: Rule ID {rule_id} cleared. Resolving log ID {history_log_id}.")
            try:
                resolve_alert_in_history(history_log_id)
                socketio.emit('alert_cleared', to='broadcast_room')
                print(f" -> Emitted 'alert_cleared' event.")
            except Exception as e:
                print(f"DATABASE ERROR: Failed to resolve alert: {e}")
            if rule_id in _last_alert_times:
                del _last_alert_times[rule_id]
            if history_log_id in _escalation_threads:
                print(f" -> Note: Escalation thread for history ID {history_log_id} will self-terminate.")
                _escalation_threads.pop(history_log_id, None)

    if not triggered_rules:
        stop_buzzer()
    else:
        most_severe_rule = max(triggered_rules, key=lambda r: (r.get('activate_buzzer', False), r.get('buzzer_mode') == 'repeating', r.get('buzzer_duration_seconds', 0)))
        if most_severe_rule.get('activate_buzzer'):
            duration = most_severe_rule.get('buzzer_duration_seconds', 0)
            mode = most_severe_rule.get('buzzer_mode', 'once')
            if duration > 0 and mode == 'repeating':
                if not (current_buzzer_thread and current_buzzer_thread.is_alive()):
                    start_repeating_buzz(duration, pause=1.0)