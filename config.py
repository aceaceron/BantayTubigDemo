# config.py
import sqlite3
import json

# --- Device Configuration ---
# A unique identifier for the physical hardware device.
# This ID is sent with heartbeats and used to associate sensor data
# and logs with the correct physical unit in a multi-device setup.
DEVICE_ID = "dev-1"

# --- Temporary Session Management ---
# This is a simple, non-production way to simulate a logged-in user.
# In a real-world application, this would be replaced by a proper
# session management system (e.g., Flask-Login) that uses secure cookies.
# The user ID of the person "logged in" to the web interface. This
# is used for audit logging to track who performed which action.
CURRENT_USER_ID = 1 # Default to a system admin or a known user ID

# Default coordinates for Labo, Camarines Norte, used as a fallback.
DEFAULT_LATITUDE = 14.154352
DEFAULT_LONGITUDE = 122.828524

def set_current_user_id(user_id):
    """Updates the global variable for the current user's ID."""
    global CURRENT_USER_ID
    CURRENT_USER_ID = user_id

def get_device_location_from_db(device_id, db_path='bantaytubig.db'):
    """
    Connects to the database and fetches the coordinates for a specific device.
    Returns (latitude, longitude) or default values if not found.
    """
    try:
        # Connect to the SQLite database.
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Query the database for the location of the specified device.
        cursor.execute("SELECT location FROM devices WHERE id = ?", (device_id,))
        result = cursor.fetchone()
        conn.close()

        if result:
            # The result is a JSON string: '{"province":..., "coordinates":"lat, lon"}'
            location_data = json.loads(result[0])
            
            # Split the "coordinates" string into latitude and longitude.
            lat_str, lon_str = location_data['coordinates'].split(',')
            
            # Convert to float and return the values.
            return float(lat_str), float(lon_str)
        else:
            # Handle case where the device ID is not found.
            print(f"WARNING: Device ID '{device_id}' not found. Using default coordinates.")
            return DEFAULT_LATITUDE, DEFAULT_LONGITUDE

    except Exception as e:
        # Handle other potential errors (DB file not found, bad data format, etc.).
        print(f"WARNING: Could not fetch coordinates from database. Error: {e}. Using default coordinates.")
        return DEFAULT_LATITUDE, DEFAULT_LONGITUDE

# --- Main Configuration Variables ---
# Call the function to dynamically load the coordinates.
DEVICE_LATITUDE, DEVICE_LONGITUDE = get_device_location_from_db(DEVICE_ID)

# You can keep other static config variables here if needed.
print(f"Config loaded for device '{DEVICE_ID}' at Location: {DEVICE_LATITUDE}, {DEVICE_LONGITUDE}")