# sensor_reader.py
import os
import random
import time

try:
    import spidev
    _spi_available = os.path.exists("/dev/spidev0.0") or os.path.exists("/dev/spidev0.1")
except ImportError:
    spidev = None
    _spi_available = False

# --- Safe SPI Setup ---
spi = None
if _spi_available:
    try:
        spi = spidev.SpiDev()
        spi.open(0, 0)
        spi.max_speed_hz = 1350000
        print("SPI initialized successfully.")
    except Exception as e:
        print(f"SPI init failed: {e}. Using mock mode.")
        spi = None
else:
    print("SPI not available. Running in mock mode.")

# --- Mock Sensor Generators ---
def _mock_value(sensor="generic"):
    if sensor == "temp": return round(25 + random.uniform(-2, 2), 2)
    if sensor == "ph": return round(7 + random.uniform(-0.5, 0.5), 2)
    if sensor == "tds": return round(300 + random.uniform(-50, 50), 0)
    if sensor == "turbidity": return round(2 + random.uniform(-0.5, 0.5), 2)
    return 0.0

# --- Reading Functions ---
def read_temp():
    return _mock_value("temp") if not spi else 25.0  # Replace with real ADC read

def read_ph():
    return _mock_value("ph") if not spi else 7.0     # Replace with real ADC read

def calculate_ph(voltage):
    return float(voltage)

def read_tds():
    return _mock_value("tds") if not spi else 300.0  # Replace with real ADC read

def calculate_tds(voltage):
    return float(voltage)

def read_turbidity():
    return _mock_value("turbidity") if not spi else 2.0  # Replace with real ADC read

def calculate_turbidity(voltage):
    return float(voltage)

def close_spi():
    if spi:
        spi.close()
        print("SPI connection closed.")
