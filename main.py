# main.py
import eventlet
eventlet.monkey_patch()

# === Step 1: Import only the most essential modules first ===
import time
import sys
import threading
import socket
import paho.mqtt.client as mqtt
import network_manager
import os

# Detect if running in Render (they set RENDER environment variables)
CLOUD_MODE = os.getenv("RENDER", "false").lower() == "true"

# Prioritize importing the LCD module.
from lcd_display import (
    show_startup_banner, start_status, update_status, stop_status,
    clear_lcd, display_readings, display_water_quality, display_network_status,
    display_hotspot_credentials, display_config_instructions
)

# Import the app and socketio instance here, as they are needed early.
from app import app, socketio

# This middleware specifically catches the BrokenPipeError and handles it gracefully.
class BrokenPipeErrorHandler:
    def __init__(self, application):
        self.application = application

    def __call__(self, environ, start_response):
        try:
            return self.application(environ, start_response)
        except BrokenPipeError:
            print("INFO: Client disconnected (BrokenPipeError). Request ignored.", file=sys.stderr)
            return []
        except Exception as e:
            print(f"ERROR: An unexpected exception occurred: {e}", file=sys.stderr)
            raise

# Apply the middleware to your Flask app
app.wsgi_app = BrokenPipeErrorHandler(app.wsgi_app)

show_startup_banner()

from database.setup import create_tables
print("Initializing and verifying database schema...")
create_tables()
print("Database setup complete.")

# === Step 2: Define the main application logic ===
def run_monitoring_app():
    import json
    from datetime import datetime, timedelta
    import paho.mqtt.client as mqtt

    # === Initialize the LCD and MQTT Client Immediately ===
    start_status("Initializing...")

    from ml_models.main_processor import run_ml_analysis
    
    # Connect to MQTT Broker right after LCD
    update_status("Connecting to MQTT")
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
    client.connect_async("broker.hivemq.com", 1883, 60)
    client.loop_start()

    update_status("Loading database...")
    from database import (
        create_tables,
        insert_measurement,
        insert_environmental_context,
        get_calibrations_for_device,
        cleanup_old_data
    )

    update_status("Loading server...")
    from weather_api import get_weather_data
    import alerter
    import requests

    update_status("Loading config...")
    from config import DEVICE_ID, DEVICE_LATITUDE, DEVICE_LONGITUDE

    update_status("Loading sensors...")
    import sensor_reader
    from sensor_reader import (
        read_temp, read_ph, read_tds, read_turbidity, close_spi
    )

    update_status("Loading ML model...")
    from water_quality import predict_water_quality, train_decision_tree

    # --- Function Definitions ---
    def get_ip_address():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(2.0)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "Not Connected"

    def send_heartbeat(current_sensor_values):
        if not DEVICE_ID:
            return
    
        # Use environment variable if available, else default to local
        base_url = os.getenv("SERVER_URL", "http://127.0.0.1:5000")
        url = f"{base_url}/api/system_device/heartbeat"
    
        payload = {"deviceId": DEVICE_ID, "sensor_values": current_sensor_values}
        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code != 200:
                print(f"Heartbeat Error: Server responded with {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Could not send heartbeat. Error: {e}")

    def get_days_since_calibration():
        calibration_dates = get_calibrations_for_device(DEVICE_ID)
        if not calibration_dates: return 999
        total_days, num_calibrations = 0, 0
        for _, date_str in calibration_dates.items():
            try:
                last_cal_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                delta = datetime.now() - last_cal_date
                total_days += delta.days
                num_calibrations += 1
            except (ValueError, TypeError):
                continue
        return total_days / num_calibrations if num_calibrations > 0 else 999

    # === Startup Sequence ===
    update_status("Initializing database")
    create_tables()

    update_status("Training ML model")
    train_decision_tree()

    update_status("Initializing alerter")
    if CLOUD_MODE:
        print("Cloud mode: Skipping SIM/GPIO setup...")
    else:
        if not alerter.setup_serial():
            update_status("SIM module ERROR")
        else:
            update_status("SIM module ready")
        if not alerter.setup_gpio():
            update_status("Buzzer ERROR")
        else:
            update_status("Buzzer ready")
    alerter.start_sms_worker()
    update_status("SMS worker started")


    stop_status("BantayTubig Running")
    time.sleep(1)

    # --- Main Loop ---
    last_env_log_time = None
    last_heartbeat_time = datetime.now()
    last_cleanup_time = None
    lcd_display_state = 0
    LOOP_DELAY_SECONDS = 1
    last_ml_analysis_time = None

    try:
        while True:
            try:
                now = datetime.now()
                timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

                # 0. Network
                ip_address = get_ip_address()
                is_connected = (ip_address != "Not Connected")

                # 1. Read sensors and insert into database
                temp_voltage, temp_val = read_temp()
                ph_voltage, ph_val = read_ph()
                tds_voltage, tds_val = read_tds()
                turbidity_voltage, turbidity_val = read_turbidity()
                
                # Get the full prediction dictionary from the ML model
                prediction_result = predict_water_quality(temp_val, ph_val, tds_val, turbidity_val)
                water_quality_for_db = prediction_result['quality']
                
                # Insert into the database using both value + voltage
                measurement_id = insert_measurement(
                    timestamp, temp_val, ph_val, ph_voltage,
                    tds_val, tds_voltage, turbidity_val, turbidity_voltage,
                    water_quality_for_db
                )
                
                print(
                    f"[{timestamp}] Logged (ID:{measurement_id}): "
                    f"Temp={temp_val:.2f}C (V={temp_voltage:.3f}) | "
                    f"pH={ph_val:.2f} (V={ph_voltage:.3f}) | "
                    f"TDS={tds_val:.2f} (V={tds_voltage:.3f}) | "
                    f"Turb={turbidity_val:.2f} (V={turbidity_voltage:.3f}) | "
                    f"Quality={water_quality_for_db}"
                )

                sensor_data = {"temperature": temp_val, "ph": ph_val, "tds": tds_val, "turbidity": turbidity_val}
                alerter.check_rules_and_trigger_alerts(sensor_data)

                # 2. Hourly tasks
                if last_env_log_time is None or (now - last_env_log_time) >= timedelta(hours=1):
                    if is_connected:
                        weather_context = get_weather_data(DEVICE_LATITUDE, DEVICE_LONGITUDE)
                        days_since_cal = get_days_since_calibration()
                        insert_environmental_context(
                            measurement_id=measurement_id, hour_of_day=now.hour,
                            day_of_week=now.weekday(), month_of_year=now.month,
                            rainfall_mm=weather_context.get('rainfall_mm'),
                            air_temp_c=weather_context.get('air_temp_c'),
                            wind_speed_kph=weather_context.get('wind_speed_kph'),
                            pressure_mb=weather_context.get('pressure_mb'),
                            days_since_calibration=days_since_cal
                        )
                        last_env_log_time = now

                # 3. Minute-ly tasks
                if (now - last_heartbeat_time) >= timedelta(seconds=60):
                    if is_connected:
                        heartbeat_payload = {
                            "Temperature": temp_val, "pH": ph_val, "TDS": tds_val, "Turbidity": turbidity_val
                        }
                        send_heartbeat(heartbeat_payload)
                        mqtt_payload = {
                            "timestamp": timestamp, "temperature": temp_val, "ph": ph_val,
                            "tds": tds_val, "turbidity": turbidity_val, "water_quality": water_quality_for_db
                        }
                        client.publish("water_quality/measurements", json.dumps(mqtt_payload))
                        last_heartbeat_time = now

                # 4. Daily tasks
                if last_cleanup_time is None or (now - last_cleanup_time) >= timedelta(hours=24):
                    cleanup_old_data()
                    last_cleanup_time = now

                # 5. LCD Display
                if lcd_display_state == 0:
                    display_readings(temp_val, ph_val, tds_val, turbidity_val)
                elif lcd_display_state == 1:
                    display_water_quality(water_quality_for_db, ip_address if is_connected else None)
                elif lcd_display_state == 2 and not is_connected:
                    display_network_status()

                lcd_display_state += 1
                if is_connected and lcd_display_state > 1:
                    lcd_display_state = 0
                elif not is_connected and lcd_display_state > 2:
                    lcd_display_state = 0
                
                if last_ml_analysis_time is None or (now - last_ml_analysis_time) >= timedelta(minutes=15):
                    print("PERIODIC TRIGGER: Running ML analysis for forecasts and anomalies...")
                    try:
                        # Run the entire ML pipeline in the background.
                        # Using a thread prevents this from freezing the main sensor loop.
                        ml_thread = threading.Thread(target=run_ml_analysis, daemon=True)
                        ml_thread.start()
                    except Exception as ml_err:
                        print(f"!!! ML ANALYSIS ERROR: {ml_err}")
                    last_ml_analysis_time = now
                time.sleep(LOOP_DELAY_SECONDS)

            except Exception as e:
                print(f"!!! LOOP ERROR: {e}")
                time.sleep(5)

    except KeyboardInterrupt:
        print("\nShutdown signal received. Cleaning up...")

    finally:
        client.loop_stop()
        stop_status("System Offline")
        clear_lcd()
        close_spi()
        alerter.stop_buzzer()
        alerter.destroy_gpio()
        alerter.close_serial()
        sys.exit(0)

# === Step 3: Entry point ===
if __name__ == "__main__":
    start_status("Initializing...")
    time.sleep(2)

    if CLOUD_MODE:
        print("Running in CLOUD MODE (Render). Skipping WiFi setup...")
        port = int(os.getenv("PORT", 5000))
        server_thread = threading.Thread(
            target=lambda: socketio.run(app, host="0.0.0.0", port=port), daemon=True
        )
        server_thread.start()
        run_monitoring_app()
    else:
        # Your existing WiFi/hotspot setup flow
        update_status("Checking Network...")
        time.sleep(2)
