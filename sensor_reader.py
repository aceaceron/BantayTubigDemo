# sensor_reader.py
import random

def read_temp():
    return round(random.uniform(24.0, 30.0), 2)

def read_ph():
    return round(random.uniform(2.0, 2.5), 3)

def calculate_ph(voltage):
    return round(7 + ((2.5 - voltage) / 0.18), 2)

def read_tds():
    return round(random.uniform(0.1, 0.4), 3)

def calculate_tds(voltage):
    return round((voltage / 0.18) * 1000, 2)

def read_turbidity():
    return round(random.uniform(0, 50), 2)

def calculate_turbidity(voltage):
    return voltage  # already fake NTU

def close_spi():
    print("SPI disabled in mock mode.")
