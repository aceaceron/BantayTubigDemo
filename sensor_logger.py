import time
import json
import spidev
import sqlite3
import paho.mqtt.client as mqtt
import os
import glob
import pandas as pd  
from RPLCD.i2c import CharLCD
from datetime import datetime
import joblib

# === Temp Sensor (DS18B20) ===
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')
base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28*')[0]
device_file = device_folder + '/w1_slave'

def read_temp():
    try:
        with open(device_file, 'r') as f:
            lines = f.readlines()
        if len(lines) < 2 or 'YES' not in lines[0]:
            print("Temperature sensor not ready.")
            return None
        temp_pos = lines[1].find('t=')
        if temp_pos != -1:
            temp_string = lines[1][temp_pos + 2:]
            temp_c = float(temp_string) / 1000.0
            return temp_c
    except Exception as e:
        print("Error reading temperature:", e)
        return None

# Initialize LCD
lcd = CharLCD(i2c_expander='PCF8574', address=0x27, port=1, cols=20, rows=4, dotsize=8)
lcd.clear()
lcd.write_string("Water Quality System Ready")
time.sleep(2)

# Initialize SPI for MCP3008
spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 1350000

# Initialize MQTT
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "water_quality"
client = mqtt.Client()
client.connect(MQTT_BROKER, MQTT_PORT, 60)

# Connect to SQLite
conn = sqlite3.connect("bantaytubig.db")
cursor = conn.cursor()

# Load the trained model
model = joblib.load('bantaytubig_model.joblib')

# Function to read ADC values from MCP3008
def read_adc(channel):
    adc = spi.xfer2([1, (8 + channel) << 4, 0])
    data = ((adc[1] & 3) << 8) + adc[2]
    return data

def read_ph():
    analog_value = read_adc(0)
    voltage = (analog_value * 3.3) / 1023
    return voltage

def calculate_ph(voltage):
    return 7 + ((2.5 - voltage) / 0.18)

def read_tds():
    analog_value = read_adc(1)
    voltage = (analog_value * 3.3) / 1023
    return voltage

def calibrate_tds(voltage):
    reference_voltage = 0.18
    tds = (voltage / reference_voltage) * 1000
    return tds

def read_turbidity():
    analog_value = read_adc(3)
    voltage = (analog_value * 3.3) / 1023
    ntu = (1 - voltage / 0.91) * 4784
    return max(0, ntu)

# Function to make predictions using the trained model
def predict_water_quality(temperature, ph, tds, turbidity):
    # Create a DataFrame with feature names
    features = pd.DataFrame([[temperature, ph, tds, turbidity]], columns=['temperature', 'ph', 'tds', 'turbidity'])
    prediction = model.predict(features)
    water_quality = {0: 'Good', 1: 'Average', 2: 'Poor'}
    return water_quality[prediction[0]]

# Function to simulate moving average for TDS
def moving_average(values, window_size=5):
    if len(values) < window_size:
        return sum(values) / len(values)
    return sum(values[-window_size:]) / window_size

tds_readings = []

try:
    while True:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Read sensors
        temp = read_temp()
        ph_voltage = read_ph()
        ph = calculate_ph(ph_voltage)
        tds_voltage = read_tds()
        tds_value = calibrate_tds(tds_voltage)
        tds_readings.append(tds_value)
        tds = moving_average(tds_readings)
        turbidity = read_turbidity()

        # Make water quality prediction
        water_quality = predict_water_quality(temp, ph, tds, turbidity)

        
        # Prepare data for MQTT
        data = {
            "timestamp": timestamp,
            "temperature": round(temp, 2) if temp is not None else None,
            "ph": round(ph, 3),
            "tds": round(tds, 2),
            "turbidity": round(turbidity, 2),
            "water_quality": water_quality
        }
        client.publish(MQTT_TOPIC, json.dumps(data))

        # Display sensor readings and water quality on LCD
        if temp is not None:
            temp_str = f"{temp:.2f}°C"
        else:
            temp_str = "Error"

        print(f"[{timestamp}] Logged: Temp={temp_str} | pH={ph:.2f} | TDS={tds:.2f} | Turb={turbidity:.2f} NTU | Water Quality={water_quality}")

        lcd.clear()
        lcd.cursor_pos = (0, 0)
        lcd.write_string(f"Temp: {temp_str}")

        lcd.cursor_pos = (1, 0)
        lcd.write_string(f"pH: {ph:.2f}")
        lcd.cursor_pos = (2, 0)
        lcd.write_string(f"TDS: {tds:.0f} ppm")
        lcd.cursor_pos = (3, 0)
        lcd.write_string(f"Turb: {turbidity:.0f} NTU")

        time.sleep(1)

except KeyboardInterrupt:
    print("\nExiting...")
    spi.close()
    lcd.clear()
    conn.close()
