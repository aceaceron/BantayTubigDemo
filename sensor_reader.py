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
    if sensor == "temp":
        return round(25 + random.uniform(-2, 2), 2)         # °C
    if sensor == "ph":
        return round(7 + random.uniform(-0.5, 0.5), 2)      # pH scale
    if sensor == "tds":
        return round(300 + random.uniform(-50, 50), 0)      # ppm
    if sensor == "turbidity":
        return round(2 + random.uniform(-0.5, 0.5), 2)      # NTU
    return 0.0

# --- Reading Functions ---
def read_temp():
    """Return temperature in Celsius."""
    if not spi:
        return _mock_value("temp")
    # TODO: Replace with actual ADC read from sensor
    return 25.0

def read_ph():
    """Return pH value."""
    if not spi:
        return _mock_value("ph")
    # TODO: Replace with actual ADC read
    return 7.0

def read_tds():
    """Return TDS in ppm."""
    if not spi:
        return _mock_value("tds")
    # TODO: Replace with actual ADC read
    return 300.0

def read_turbidity():
    """Return turbidity in NTU."""
    if not spi:
        return _mock_value("turbidity")
    # TODO: Replace with actual ADC read
    return 2.0

# --- Graceful Shutdown ---
def close_spi():
    """Close SPI connection if opened."""
    global spi
    if spi:
        try:
            spi.close()
            print("SPI connection closed.")
        except Exception as e:
            print(f"Error closing SPI: {e}")
        spi = None


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
