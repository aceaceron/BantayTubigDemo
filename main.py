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

# Prioritize importing the LCD module.
from lcd_display import (
    show_startup_banner, start_status, update_status, stop_status,
    clear_lcd, display_readings, display_water_quality, display_network_status, display_hotspot_credentials, display_config_instructions
)

# Import the app and socketio instance here, as they are needed early.
from app import app, socketio

# This middleware specifically catches the BrokenPipeError and handles it gracefully.
class BrokenPipeErrorHandler:
    def __init__(self, application):
        self.application = application

    def __call__(self, environ, start_response):
        try:
            # Attempt to handle the request as normal
            return self.application(environ, start_response)
        except BrokenPipeError:
            # If the client disconnects, log a quiet message instead of a traceback
            print("INFO: Client disconnected (BrokenPipeError). Request ignored.", file=sys.stderr)
            return [] # Return an empty response to signify closure
        except Exception as e:
            # Allow other, unexpected errors to still raise a traceback
            print(f"ERROR: An unexpected exception occurred: {e}", file=sys.stderr)
            raise

# Apply the middleware to your Flask app
app.wsgi_app = BrokenPipeErrorHandler(app.wsgi_app)

show_startup_banner()

from database.setup import create_tables
print("Initializing and verifying database schema...")
create_tables()
print("Database setup complete.")

# Run the function immediately to ensure all tables exist
print("Initializing and verifying database schema...")
create_tables()
print("Database setup complete.")

# === Step 2: Define the main application logic in its own function ===
def run_monitoring_app():
    import json
    from datetime import datetime, timedelta
    import paho.mqtt.client as mqtt

    # === Initialize the LCD and MQTT Client Immediately ===
    start_status("Initializing...")

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

    # === Step 3: Import the rest of your modules ===
    update_status("Loading config...")
    from config import DEVICE_ID, DEVICE_LATITUDE, DEVICE_LONGITUDE

    update_status("Loading sensors...")
    import sensor_reader
    from sensor_reader import (
        read_temp, read_ph, calculate_ph,
        read_tds, calculate_tds,
        read_turbidity, calculate_turbidity, close_spi
    )

    update_status("Loading ML model...")
    from water_quality import predict_water_quality, train_decision_tree

    # --- Function Definitions ---

    def get_ip_address():
        """
        Retrieves the primary local IP address of the device.
        Returns 'Not Connected' if unable to determine the IP.
        """
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(2.0) # Prevent long waits
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "Not Connected"

    def send_heartbeat(current_sensor_values):
        """Sends a heartbeat with the latest sensor readings to the server."""
        if not DEVICE_ID: return
        url = "http://127.0.0.1:5000/api/system_device/heartbeat"
        payload = {"deviceId": DEVICE_ID, "sensor_values": current_sensor_values}
        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code != 200:
                print(f"Heartbeat Error: Server responded with {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Could not send heartbeat. Error: {e}")

    def get_days_since_calibration():
        """Calculates the average age in days of all sensor calibrations."""
        calibration_dates = get_calibrations_for_device(DEVICE_ID)
        if not calibration_dates: return 999
        total_days, num_calibrations = 0, 0
        for sensor_type, date_str in calibration_dates.items():
            try:
                last_cal_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                delta = datetime.now() - last_cal_date
                total_days += delta.days
                num_calibrations += 1
            except (ValueError, TypeError): continue
        return total_days / num_calibrations if num_calibrations > 0 else 999
    
    # === Continue with the rest of the startup sequence ===
    update_status("Initializing database")
    create_tables()

    update_status("Training ML model")
    train_decision_tree()

    update_status("Initializing alerter")
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

    # --- Main Application Loop ---
    last_env_log_time = None
    last_heartbeat_time = datetime.now()
    last_cleanup_time = None
    lcd_display_state = 0  # 0: readings, 1: quality, 2: network status

    # Set the main loop delay to 1 seconds for frequent measurements
    LOOP_DELAY_SECONDS = 1

    try:
        while True:
            try:
                now = datetime.now()
                timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

                # 0. Get the current IP Address
                ip_address = get_ip_address()
                is_connected = (ip_address != "Not Connected")

                # 1. Read sensors and insert into database
                temp_val = read_temp()
                ph_voltage = read_ph(); ph_val = calculate_ph(ph_voltage)
                tds_voltage = read_tds(); tds_val = calculate_tds(tds_voltage)
                turbidity_voltage = read_turbidity(); turbidity_val = calculate_turbidity(turbidity_voltage)
                
                # Get the full prediction dictionary from the ML model
                prediction_result = predict_water_quality(temp_val, ph_val, tds_val, turbidity_val)

                # Extract just the quality STRING for the database
                water_quality_for_db = prediction_result['quality']

                # Insert into the database using the string, not the dictionary
                measurement_id = insert_measurement(
                    timestamp, temp_val, ph_val, ph_voltage, tds_val, tds_voltage,
                    turbidity_val, turbidity_voltage, water_quality_for_db
                )
                
                temp_str = f"{temp_val:.2f}C" if temp_val is not None else "N/A"
                print(
                    f"[{timestamp}] Logged (ID:{measurement_id}): "
                    f"Temp={temp_str} | pH={ph_val:.2f} | TDS={tds_val:.2f} | "
                    f"Turb={turbidity_val:.2f} | Quality={water_quality_for_db}"
                )
                
                sensor_data = {
                    "temperature": temp_val,
                    "ph": ph_val,
                    "tds": tds_val,
                    "turbidity": turbidity_val
                }
                alerter.check_rules_and_trigger_alerts(sensor_data)

                # === 2. RUN HOURLY TASKS (60 minutes) ===
                if last_env_log_time is None or (now - last_env_log_time) >= timedelta(hours=1):
                    if is_connected:
                        print("HOURLY TRIGGER: Fetching and logging environmental context...")
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
                        print(f"-> Logged environmental context for ID: {measurement_id}")
                    else:
                        print("HOURLY TRIGGER SKIPPED: Device is offline.")


                # === 3. RUN MINUTE-LY TASKS (60 seconds) ===
                if (now - last_heartbeat_time) >= timedelta(seconds=60):
                    if is_connected:
                        print("MINUTE-LY TRIGGER: Sending heartbeat and MQTT message...")
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
                    else:
                        print("MINUTE-LY TRIGGER SKIPPED: Device is offline.")

                # === 4. RUN DAILY TASKS (24 hours) ===
                if last_cleanup_time is None or (now - last_cleanup_time) >= timedelta(hours=24):
                    print("DAILY TRIGGER: Running data retention cleanup...")
                    cleanup_old_data()
                    last_cleanup_time = now

                # === 5. UPDATE LCD DISPLAY ===
                if lcd_display_state == 0:
                    display_readings(temp_val, ph_val, tds_val, turbidity_val)
                elif lcd_display_state == 1:
                    display_water_quality(water_quality_for_db, ip_address if is_connected else None)
                elif lcd_display_state == 2 and not is_connected:
                    # This state is only shown if not connected
                    display_network_status()

                # Cycle to the next display state for the next loop
                lcd_display_state += 1
                if is_connected and lcd_display_state > 1:
                    lcd_display_state = 0 # If connected, cycle between 0 and 1
                elif not is_connected and lcd_display_state > 2:
                    lcd_display_state = 0 # If not connected, cycle between 0, 1, and 2

                time.sleep(LOOP_DELAY_SECONDS)

            except Exception as e:
                print(f"!!! LOOP ERROR: An error occurred: {e}")
                print("!!! System will recover in 5 seconds...")
                time.sleep(5)

    except KeyboardInterrupt:
        print("\nShutdown signal received. Cleaning up...")

    finally:
        # --- Graceful Shutdown ---
        print("Stopping main loop and cleaning up resources.")
        client.loop_stop()
        stop_status("System Offline")
        time.sleep(1)
        clear_lcd()
        close_spi()
        alerter.stop_buzzer()
        alerter.destroy_gpio()
        alerter.close_serial()
        print("Cleanup complete. Exiting.")
        sys.exit(0)
# === Step 3: Main execution block ===
if __name__ == "__main__":
    start_status("Initializing...")
    time.sleep(2)

    update_status("Checking Network...")
    time.sleep(2)

    def run_flask_server():
        """Function to run the Flask-SocketIO server."""
        print("Starting Flask-SocketIO server in a background thread...")
        socketio.run(app, host='0.0.0.0', port=5000, debug=False, log_output=True)

    # 1. START THE SERVER THREAD UNCONDITIONALLY
    # The server is needed for both setup mode and normal operation.
    server_thread = threading.Thread(target=run_flask_server, daemon=True)
    server_thread.start()
    time.sleep(3)  # Give the server a moment to initialize

    # 2. NOW, CHECK THE NETWORK AND HANDLE SETUP MODE IF NEEDED
    if not network_manager.check_wifi_connection():
        print("No WiFi connection. Entering setup mode.")
        stop_status("WiFi Setup Mode")
        time.sleep(1)

        # The server thread is ALREADY RUNNING, so just proceed with the hotspot.
        update_status("Starting Hotspot...")
        if network_manager.start_hotspot():
            display_hotspot_credentials(network_manager.HOTSPOT_SSID, network_manager.HOTSPOT_PASS)
            
            # This loop waits for the user to finish the process on the webpage.
            while not network_manager.check_wifi_connection():
                print("Waiting for user to configure WiFi via web page...")
                if network_manager.is_client_connected():
                    display_config_instructions("10.42.0.1")
                else:
                    display_hotspot_credentials(network_manager.HOTSPOT_SSID, network_manager.HOTSPOT_PASS)
                time.sleep(5)
            
            # This part runs AFTER the user connects the device to WiFi
            print("WiFi connection established by user!")
            clear_lcd()
            stop_status("WiFi Connected!")
            time.sleep(2)
            update_status("Stopping Hotspot...")
            network_manager.stop_hotspot()
            time.sleep(3)
            clear_lcd()
        else:
            stop_status("Hotspot Failed!")
            sys.exit(1)

    # 3. FINALLY, START THE MAIN MONITORING APPLICATION
    print("WiFi connection active. Starting main application.")
    run_monitoring_app()
