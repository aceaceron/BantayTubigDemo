# config.py
import sqlite3
import json

# --- Device Configuration ---
DEVICE_ID = "dev-1"

# Default coordinates for Jose Panganiban, used as a fallback.
DEFAULT_LATITUDE = 14.156453
DEFAULT_LONGITUDE = 122.827182

def get_device_location_from_db(device_id, db_path='bantaytubig.db'):
    """
    Connects to the database and fetches the coordinates for a specific device.
    Returns (latitude, longitude) or default values if not found.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT location FROM devices WHERE id = ?", (device_id,))
        result = cursor.fetchone()
        conn.close()

        if result:
            location_data = json.loads(result[0])
            lat_str, lon_str = location_data['coordinates'].split(',')
            return float(lat_str), float(lon_str)
        else:
            print(f"WARNING: Device ID '{device_id}' not found. Using default coordinates.")
            return DEFAULT_LATITUDE, DEFAULT_LONGITUDE
    except Exception as e:
        print(f"WARNING: Could not fetch coordinates from database. Error: {e}. Using default coordinates.")
        return DEFAULT_LATITUDE, DEFAULT_LONGITUDE

# --- Main Configuration Variables ---
DEVICE_LATITUDE, DEVICE_LONGITUDE = get_device_location_from_db(DEVICE_ID)

print(f"Config loaded for device '{DEVICE_ID}' at Location: {DEVICE_LATITUDE}, {DEVICE_LONGITUDE}")