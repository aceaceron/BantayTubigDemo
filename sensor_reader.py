# # sensor_reader.py
# import time
# import spidev
# import os
# import glob
# import random
# import numpy as np

# from database import get_calibration_formula

# try:
#     from config import DEVICE_ID
# except ImportError:
#     print("WARNING: config.py not found or DEVICE_ID not set.")
#     DEVICE_ID = "default-device-id"

# # === Global SPI Setup ===
# spi = spidev.SpiDev()
# spi.open(0, 0)
# spi.max_speed_hz = 1000000
# VREF = 3.3

# # === Temp Sensor (DS18B20) ===
# # This sensor is digital and doesn't use the ADC or the new calibration model system.
# base_dir = '/sys/bus/w1/devices/'
# device_folder = glob.glob(base_dir + '28*')
# if device_folder:
#     device_folder = device_folder[0]
#     device_file = device_folder + '/w1_slave'
# else:
#     print("WARNING: DS18B20 device folder not found. Temperature readings may fail.")
#     device_file = None

# CALIBRATION_OFFSET = -1.69

# def read_temp():
#     """
#     Reads temperature from the DS18B20 sensor.
#     MODIFIED: Returns a temporary random value for testing.
#     """
#     # --- TEMPORARY MODIFICATION FOR TESTING ---
#     return random.uniform(25.0, 30.0)
#     # --- END OF TEMPORARY MODIFICATION ---
    
#     # Original logic below is currently bypassed.
#     if device_file is None:
#         return None
#     max_retries = 3
#     for _ in range(max_retries):
#         try:
#             with open(device_file, 'r') as f:
#                 lines = f.readlines()
#             if len(lines) >= 2 and 'YES' in lines[0]:
#                 temp_pos = lines[1].find('t=')
#                 if temp_pos != -1:
#                     raw_value = lines[1][temp_pos + 2:].strip()
#                     temp_c = float(raw_value) / 1000.0
#                     return temp_c + CALIBRATION_OFFSET
#             time.sleep(0.2)
#         except Exception:
#             time.sleep(0.2)
#     return None

# # === ADC & Voltage Conversion (Unified) ===
# def read_adc(channel):
#     """Reads the analog value from the specified channel of the MCP3008 ADC."""
#     if not (0 <= channel <= 7):
#         raise ValueError('ADC channel must be between 0 and 7')
#     r = spi.xfer2([1, (8 + channel) << 4, 0])
#     return ((r[1] & 0x03) << 8) + r[2]

# def convert_to_voltage(adc_value):
#     """Converts a 10-bit ADC value (0-1023) to voltage based on VREF."""
#     return (adc_value / 1023.0) * VREF

# # === pH Sensor ===
# PH_CHANNEL = 0
# # --- Default values, used as a fallback ---
# DEFAULT_PH_SLOPE = -5.26
# DEFAULT_PH_OFFSET = 20.32

# def read_ph():
#     """
#     Reads the pH sensor's voltage.
#     MODIFIED: Returns a temporary, realistic voltage for testing.
#     """
#     # --- TEMPORARY MODIFICATION FOR TESTING ---
#     # 1. Generate a random target pH value in the desired range (6.0 to 8.0).
#     temp_ph_value = random.uniform(5.0, 10.0)
#     # 2. Back-calculate the voltage that would produce this pH value using the inverse formula.
#     # Original Formula: pH = (slope * voltage) + offset
#     # Inverse Formula: voltage = (pH - offset) / slope
#     temp_voltage = (temp_ph_value - DEFAULT_PH_OFFSET) / DEFAULT_PH_SLOPE
#     return temp_voltage
#     # --- END OF TEMPORARY MODIFICATION ---
    
#     # Original logic below is currently bypassed.
#     # analog_value = read_adc(PH_CHANNEL)
#     # return convert_to_voltage(analog_value)

# def calculate_ph(voltage):
#     """
#     Calculates pH value from voltage using a custom formula from the database,
#     or falls back to a default formula.
#     Formula: pH = (slope * voltage) + offset
#     """
#     formula = get_calibration_formula(DEVICE_ID, 'pH')
    
#     if formula and formula.get('slope') is not None:
#         slope = formula['slope']
#         offset = formula['offset']
#     else:
#         slope = DEFAULT_PH_SLOPE
#         offset = DEFAULT_PH_OFFSET
        
#     return (slope * voltage) + offset

# # === TDS Sensor ===
# TDS_CHANNEL = 1
# # --- Default values, used as a fallback ---
# DEFAULT_TDS_SLOPE = 850.5
# DEFAULT_TDS_OFFSET = -125.2

# def read_tds():
#     """
#     Reads the TDS sensor's voltage.
#     MODIFIED: Returns a temporary, realistic voltage for testing.
#     """
#     # --- TEMPORARY MODIFICATION FOR TESTING ---
#     # 1. Generate a random target TDS value in the desired range (0 to 300).
#     temp_tds_value = random.uniform(100.0, 500.0)
#     # 2. Back-calculate the voltage that would produce this TDS value using the inverse formula.
#     # Original Formula: TDS = (slope * voltage) + offset
#     # Inverse Formula: voltage = (TDS - offset) / slope
#     temp_voltage = (temp_tds_value - DEFAULT_TDS_OFFSET) / DEFAULT_TDS_SLOPE
#     return temp_voltage
#     # --- END OF TEMPORARY MODIFICATION ---

#     # Original logic below is currently bypassed.
#     # analog_value = read_adc(TDS_CHANNEL)
#     # return convert_to_voltage(analog_value)

# def calculate_tds(voltage):
#     """
#     Calculates TDS (ppm) value from voltage using a custom formula from the database,
#     or falls back to a default formula. Ensures the result is not negative.
#     Formula: TDS = (slope * voltage) + offset
#     """
#     formula = get_calibration_formula(DEVICE_ID, 'TDS')
    
#     if formula and formula.get('slope') is not None:
#         slope = formula['slope']
#         offset = formula['offset']
#     else:
#         slope = DEFAULT_TDS_SLOPE
#         offset = DEFAULT_TDS_OFFSET
        
#     calculated_tds = (slope * voltage) + offset
#     return max(0.0, calculated_tds)

# # === Turbidity Sensor ===
# TURBIDITY_CHANNEL = 2
# # Final Calibration Range
# V_REF_HIGH = 0.6  # Voltage in clean water (adjusted)
# V_REF_LOW = 0.05  # Voltage in very turbid water (adjusted)

# def _get_stable_reading_voltage(channel, samples=50):
#     """
#     (Internal Helper) Reads multiple samples from an ADC channel,
#     sorts them, trims outliers, and returns the average voltage
#     for a more stable reading.
#     """
#     readings = []
#     for _ in range(samples):
#         readings.append(read_adc(channel))
#         time.sleep(0.02)
#     readings.sort()
#     trimmed = readings[int(0.2 * samples):int(0.8 * samples)]
#     if not trimmed:
#         return 0.0
#     avg_raw = sum(trimmed) / len(trimmed)
#     avg_voltage = (avg_raw * VREF) / 1023
#     return avg_voltage

# def _voltage_to_ntu(voltage):
#     """
#     (Internal Helper) Converts a voltage reading from the turbidity sensor to an NTU value.
#     """
#     return max(0.0, (V_REF_HIGH - voltage) * 1000.0 / (V_REF_HIGH - V_REF_LOW))

# def read_turbidity():
#     """
#     Reads the turbidity sensor's analog value, converts it to a stable voltage reading.
#     MODIFIED: Returns a temporary, realistic voltage for testing.
#     """
#     # --- TEMPORARY MODIFICATION FOR TESTING ---
#     # 1. Generate a random target NTU value in the desired range (0 to 50).
#     temp_ntu_value = random.uniform(0.0, 50.0)
#     # 2. Back-calculate the voltage that would produce this NTU value using the inverse formula.
#     # Original: NTU = (V_REF_HIGH - voltage) * 1000.0 / (V_REF_HIGH - V_REF_LOW)
#     # Inverse: voltage = V_REF_HIGH - (NTU * (V_REF_HIGH - V_REF_LOW) / 1000.0)
#     denominator = V_REF_HIGH - V_REF_LOW
#     if denominator == 0: return V_REF_HIGH # Avoid division by zero
#     temp_voltage = V_REF_HIGH - (temp_ntu_value * denominator / 1000.0)
#     return temp_voltage
#     # --- END OF TEMPORARY MODIFICATION ---
    
#     # Original logic below is currently bypassed.
#     # voltage = _get_stable_reading_voltage(TURBIDITY_CHANNEL)
#     # return voltage

# def calculate_turbidity(voltage_value):
#     """
#     Calculates turbidity (NTU) from the sensor's voltage reading.
#     """
#     # The original calculation logic works perfectly with the realistic voltage
#     # generated by the modified read_turbidity() function.
#     ntu = _voltage_to_ntu(voltage_value)
#     return ntu

# # === Cleanup function for SPI ===
# def close_spi():
#     """Closes the SPI bus connection."""
#     spi.close()
#     print("SPI bus closed.")
    
# sensor_reader.py
import time
import spidev
import os
import glob
# MODIFIED: Added the 'random' library for temporary values
import random
import numpy as np

from database import get_calibration_formula

try:
    from config import DEVICE_ID
except ImportError:
    print("WARNING: config.py not found or DEVICE_ID not set.")
    DEVICE_ID = "default-device-id"

# === Global SPI Setup ===
spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 1000000
VREF = 3.3

# === Temp Sensor (DS18B20) ===
# This sensor is digital and doesn't use the ADC or the new calibration model system.
base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28*')
if device_folder:
    device_folder = device_folder[0]
    device_file = device_folder + '/w1_slave'
else:
    print("WARNING: DS18B20 device folder not found. Temperature readings may fail.")
    device_file = None

CALIBRATION_OFFSET = -1.69

def read_temp():
    """Reads temperature from the DS18B20 sensor."""
    if device_file is None:
        return None
    max_retries = 3
    for _ in range(max_retries):
        try:
            with open(device_file, 'r') as f:
                lines = f.readlines()
            if len(lines) >= 2 and 'YES' in lines[0]:
                temp_pos = lines[1].find('t=')
                if temp_pos != -1:
                    raw_value = lines[1][temp_pos + 2:].strip()
                    temp_c = float(raw_value) / 1000.0
                    return temp_c + CALIBRATION_OFFSET
            time.sleep(0.2)
        except Exception:
            time.sleep(0.2)
    return None

# === ADC & Voltage Conversion (Unified) ===
def read_adc(channel):
    """Reads the analog value from the specified channel of the MCP3008 ADC."""
    if not (0 <= channel <= 7):
        raise ValueError('ADC channel must be between 0 and 7')
    r = spi.xfer2([1, (8 + channel) << 4, 0])
    return ((r[1] & 0x03) << 8) + r[2]

def convert_to_voltage(adc_value):
    """Converts a 10-bit ADC value (0-1023) to voltage based on VREF."""
    return (adc_value / 1023.0) * VREF

# === pH Sensor ===
PH_CHANNEL = 0
# --- Default values, used as a fallback ---
DEFAULT_PH_SLOPE = -5.26
DEFAULT_PH_OFFSET = 20.32

def read_ph():
    """Reads the pH sensor's voltage."""
    analog_value = read_adc(PH_CHANNEL)
    return convert_to_voltage(analog_value)

def calculate_ph(voltage):
    """
    Calculates pH value from voltage using a custom formula from the database,
    or falls back to a default formula.
    Formula: pH = (slope * voltage) + offset
    """
    formula = get_calibration_formula(DEVICE_ID, 'pH')
    
    if formula and formula.get('slope') is not None:
        # Use the custom formula from the database
        slope = formula['slope']
        offset = formula['offset']
    else:
        # Use the hardcoded default formula
        slope = DEFAULT_PH_SLOPE
        offset = DEFAULT_PH_OFFSET
        
    return (slope * voltage) + offset

# === TDS Sensor ===
TDS_CHANNEL = 1
# --- Default values, used as a fallback ---
DEFAULT_TDS_SLOPE = 850.5
DEFAULT_TDS_OFFSET = -125.2

def read_tds():
    """Reads the TDS sensor's voltage."""
    analog_value = read_adc(TDS_CHANNEL)
    return convert_to_voltage(analog_value)

def calculate_tds(voltage):
    """
    Calculates TDS (ppm) value from voltage using a custom formula from the database,
    or falls back to a default formula. Ensures the result is not negative.
    Formula: TDS = (slope * voltage) + offset
    """
    # --- TEMPORARY MODIFICATION FOR TESTING ---
    # This line overrides the actual calculation and returns a random float
    # between 0.0 and 1000.0 for demonstration purposes.
    # To revert to actual readings, comment out or delete the line below.
    #return random.uniform(0.0, 300.0)
    # --- END OF TEMPORARY MODIFICATION ---
    
    # Original calculation logic
    formula = get_calibration_formula(DEVICE_ID, 'TDS')
    
    if formula and formula.get('slope') is not None:
        slope = formula['slope']
        offset = formula['offset']
    else:
        slope = DEFAULT_TDS_SLOPE
        offset = DEFAULT_TDS_OFFSET
        
    calculated_tds = (slope * voltage) + offset
    return max(0.0, calculated_tds)

# === Turbidity Sensor ===
TURBIDITY_CHANNEL = 3
# Final Calibration Range
V_REF_HIGH = 2.795  # Voltage in clean water (adjusted)
V_REF_LOW = 0.05  # Voltage in very turbid water (adjusted)

def _get_stable_reading_voltage(channel, samples=50):
    """
    (Internal Helper) Reads multiple samples from an ADC channel,
    sorts them, trims outliers, and returns the average voltage
    for a more stable reading.
    """
    readings = []
    for _ in range(samples):
        readings.append(read_adc(channel))
        time.sleep(0.02)
    readings.sort()
    trimmed = readings[int(0.2 * samples):int(0.8 * samples)]
    if not trimmed:
        return 0.0
    avg_raw = sum(trimmed) / len(trimmed)
    avg_voltage = (avg_raw * VREF) / 1023
    return avg_voltage

def _voltage_to_ntu(voltage):
    """
    (Internal Helper) Converts a voltage reading from the turbidity sensor to an NTU value.
    Modified to give slightly larger values by scaling up.
    """
    return max(0.0, ((V_REF_HIGH - voltage) * 1000.0 / (V_REF_HIGH - V_REF_LOW)) * 1.2)


def read_turbidity():
    """
    Reads the turbidity sensor's analog value, converts it to a stable voltage reading.
    """
    voltage = _get_stable_reading_voltage(TURBIDITY_CHANNEL)
    return voltage

def calculate_turbidity(voltage_value):
    """
    Calculates turbidity (NTU) from the sensor's voltage reading.
    """
    # --- TEMPORARY MODIFICATION FOR TESTING ---
    # This line overrides the actual calculation and returns a random float
    # between 0.0 and 1000.0 for demonstration purposes.
    # To revert to actual readings, comment out or delete the line below.
    # return random.uniform(0.0, 50.0)
    # --- END OF TEMPORARY MODIFICATION ---
    
    # Original calculation logic
    ntu = _voltage_to_ntu(voltage_value)
    return ntu

# === Cleanup function for SPI ===
def close_spi():
    """Closes the SPI bus connection."""
    spi.close()
    print("SPI bus closed.")