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
def _mock_voltage(sensor="generic"):
    """Return a mock voltage (0–3.3V full range)."""
    return round(random.uniform(0.0, 3.3), 3)

def _mock_value(sensor="generic"):
    """Return a mock processed value with wide ranges."""
    if sensor == "temp": 
        return round(random.uniform(-10, 50), 2)   # -10°C to 50°C
    if sensor == "ph": 
        return round(random.uniform(0, 14), 2)     # Full pH scale
    if sensor == "tds": 
        return round(random.uniform(0, 2000), 0)   # 0 to 2000 ppm
    if sensor == "turbidity": 
        return round(random.uniform(0, 100), 2)    # 0 to 100 NTU
    return 0.0

# --- Reading Functions (return voltage + value) ---
def read_temp():
    if not spi:
        return _mock_voltage("temp"), _mock_value("temp")
    # Replace with real ADC reading
    return 0.75, 25.0

def read_ph():
    if not spi:
        return _mock_voltage("ph"), _mock_value("ph")
    return 2.8, 7.0

def read_tds():
    if not spi:
        return _mock_voltage("tds"), _mock_value("tds")
    return 1.8, 300.0

def read_turbidity():
    if not spi:
        return _mock_voltage("turbidity"), _mock_value("turbidity")
    return 3.0, 2.0

def close_spi():
    if spi:
        spi.close()
        print("SPI closed.")
