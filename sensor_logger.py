# sensor_logger.py
import time
import json
import sqlite3
import paho.mqtt.client as mqtt
import pandas as pd
from datetime import datetime
import joblib
import random

# === Simulated Temperature Sensor ===
def read_temp():
    # realistic temp between 24°C and 30°C
    return round(random.uniform(24.0, 30.0), 2)

# === Simulated pH Sensor ===
def read_ph():
    # simulate voltage ~ 2.0–2.5 V
    return round(random.uniform(2.0, 2.5), 3)

def calculate_ph(voltage):
    return round(7 + ((2.5 - voltage) / 0.18), 2)

# === Simulated TDS Sensor ===
def read_tds():
    return round(random.uniform(0.1, 0.4), 3)  # fake voltage

def calibrate_tds(voltage):
    return round((voltage / 0.18) * 1000, 2)  # ppm

# === Simulated Turbidity Sensor ===
def read_turbidity():
    return round(random.uniform(0, 50), 2)  # NTU

# === Mock LCD (disable hardware) ===
class MockLCD:
    def clear(self): pass
    def write_string(self, text): pass
    @property
    def cursor_pos(self): return (0, 0)
    @cursor_pos.setter
    def cursor_pos(self, pos): pass

lcd = MockLCD()

# === MQTT (still works if broker is accessible) ===
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "water_quality"
client = mqtt.Client()
try:
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
except Exception:
    print("⚠️ MQTT not available, running without broker.")

# === SQLite (optional, still usable) ===
conn = sqlite3.connect("bantaytubig.db")
cursor = conn.cursor()

# === Load trained model (if exists) ===
try:
    model = joblib.load('bantaytubig_model.joblib')
except Exception:
    print("⚠️ Model not found, skipping ML prediction.")
    model = None

def predict_water_quality(temperature, ph, tds, turbidity):
    if not model:
        return random.choice(['Good', 'Average', 'Poor', 'Bad'])
    features = pd.DataFrame([[temperature, ph, tds, turbidity]],
                            columns=['temperature', 'ph', 'tds', 'turbidity'])
    prediction = model.predict(features)
    water_quality = {0: 'Good', 1: 'Average', 2: 'Poor', 3: 'Bad'}
    return water_quality.get(prediction[0], "Unknown")

try:
    while True:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        temp = read_temp()
        ph_voltage = read_ph()
        ph = calculate_ph(ph_voltage)
        tds_voltage = read_tds()
        tds = calibrate_tds(tds_voltage)
        turbidity = read_turbidity()
        water_quality = predict_water_quality(temp, ph, tds, turbidity)

        data = {
            "timestamp": timestamp,
            "temperature": temp,
            "ph": ph,
            "tds": tds,
            "turbidity": turbidity,
            "water_quality": water_quality
        }

        client.publish(MQTT_TOPIC, json.dumps(data))
        print(f"[{timestamp}] Logged: {data}")

        time.sleep(2)

except KeyboardInterrupt:
    print("\nExiting...")
    conn.close()
