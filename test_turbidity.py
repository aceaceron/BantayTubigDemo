# test_turbidity_v2.py
# A standalone script to test the turbidity sensor (DFRobot Gravity: Analog Turbidity Sensor).
# This script reads the sensor's raw ADC value, converts it to voltage, then calculates
# the final turbidity in NTU.

import time
import spidev

# ==============================================================================
# SENSOR AND HARDWARE CONFIGURATION
# ==============================================================================

# --- Global SPI Setup ---
# This section initializes the SPI communication with the MCP3008 ADC.
spi = spidev.SpiDev()
spi.open(0, 0)  # Open SPI bus 0, device 0
spi.max_speed_hz = 1000000  # Set SPI speed to 1MHz
VREF = 3.3  # Reference voltage for the ADC. Assumes the Pi's 3.3V pin is used.

# --- Turbidity Sensor Configuration ---
TURBIDITY_CHANNEL = 3  # ADC channel connected to the turbidity sensor's signal pin (e.g., CH3)

# --- Calibration Values ---
# IMPORTANT: These values should be fine-tuned by testing with known liquids.
# V_REF_HIGH is the voltage in completely clear water (ideally 0 NTU).
# V_REF_LOW is the voltage in a very opaque/turbid liquid.
V_REF_HIGH = 2.78 # Example: Voltage measured in clean, clear water.
V_REF_LOW = 0.05   # Example: Voltage measured in very turbid water.


# ==============================================================================
# CORE FUNCTIONS
# ==============================================================================

def read_adc(channel):
    """
    Reads the raw analog value (0-1023) from the specified ADC channel.
    
    Args:
        channel (int): The ADC channel to read (0-7).
        
    Returns:
        int: The 10-bit raw ADC value.
    """
    if not (0 <= channel <= 7):
        raise ValueError('ADC channel must be between 0 and 7')
    # The command to send to the MCP3008 to read from the specified channel
    r = spi.xfer2([1, (8 + channel) << 4, 0])
    # Process the 3-byte response to get the 10-bit ADC value
    adc_out = ((r[1] & 3) << 8) + r[2]
    return adc_out

def get_sensor_readings(channel, samples=50):
    """
    Reads multiple samples from an ADC channel to get stable readings.
    It sorts the readings, trims outliers, and returns the average raw
    ADC value and the corresponding voltage.
    
    Args:
        channel (int): The ADC channel to read.
        samples (int): The number of samples to take.
        
    Returns:
        tuple: A tuple containing (stable_voltage, stable_raw_adc_value).
    """
    readings = []
    for _ in range(samples):
        readings.append(read_adc(channel))
        time.sleep(0.02)  # Wait 20ms between samples for the reading to settle

    # Sort readings to easily trim outliers
    readings.sort()
    
    # Remove the bottom 20% and top 20% of readings to discard noise
    trim_count = int(0.2 * samples)
    trimmed_readings = readings[trim_count:-trim_count]

    if not trimmed_readings:
        # Fallback in case trimming results in an empty list (e.g., with few samples)
        avg_raw = sum(readings) / len(readings) if readings else 0
    else:
        avg_raw = sum(trimmed_readings) / len(trimmed_readings)

    # Convert the average raw ADC value to voltage
    avg_voltage = (avg_raw * VREF) / 1023.0
    return avg_voltage, avg_raw

def calculate_turbidity_from_voltage(voltage):
    """
    Converts a voltage reading from the turbidity sensor to a Nephelometric
    Turbidity Unit (NTU) value.
    
    Args:
        voltage (float): The voltage reading from the sensor.
        
    Returns:
        float: The calculated turbidity in NTU.
    """
    # Ensure the voltage is within the calibrated range for a meaningful calculation
    voltage = max(V_REF_LOW, min(V_REF_HIGH, voltage))

    # The formula maps the voltage range [V_REF_LOW, V_REF_HIGH] to an NTU range [1000, 0].
    ntu = (V_REF_HIGH - voltage) * 1000.0 / (V_REF_HIGH - V_REF_LOW)

    # The final value should not be negative
    return max(0.0, ntu)


# ==============================================================================
# MAIN TEST EXECUTION
# ==============================================================================

if __name__ == "__main__":

    try:
        while True:
            # Step 1: Get stable readings (voltage and raw ADC) from the sensor
            sensor_voltage, raw_adc_value = get_sensor_readings(TURBIDITY_CHANNEL)

            # Step 2: Calculate the NTU value from the measured voltage
            ntu_value = calculate_turbidity_from_voltage(sensor_voltage)

            # Step 3: Display all the results in a clear, aligned format
            print(f"Raw ADC: {raw_adc_value:<4.0f} | Voltage: {sensor_voltage:.4f} V | Turbidity: {ntu_value:.2f} NTU")

            # Wait for 2 seconds before taking the next reading
            time.sleep(2)

    except KeyboardInterrupt:
        # Handle the user pressing Ctrl+C
        print("\n🛑 Test stopped by user.")
    except Exception as e:
        # Catch any other unexpected errors
        print(f"\nAn error occurred: {e}")
    finally:
        # This block will run whether the script exits normally or via an error
        spi.close()
        print("🔌 SPI connection closed. Exiting.")