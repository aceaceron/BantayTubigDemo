# database/data_manager.py
"""
Manages the insertion and retrieval of sensor measurements and environmental data.
"""
import sqlite3
import pandas as pd
from .config import DB_PATH, DB_LOCK
from datetime import datetime, timedelta

def insert_measurement(timestamp, temperature, ph, ph_voltage, tds, tds_voltage, turbidity, turbidity_voltage, water_quality):
    """
    Inserts a new sensor measurement into the 'measurements' table and returns the ID of the new row.
    """
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO measurements (timestamp, temperature, ph, ph_voltage, tds, tds_voltage, turbidity, turbidity_voltage, water_quality)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (timestamp, temperature, ph, ph_voltage, tds, tds_voltage, turbidity, turbidity_voltage, water_quality))
        last_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return last_id

def insert_environmental_context(measurement_id, hour_of_day, day_of_week, month_of_year, rainfall_mm, 
                                 air_temp_c, wind_speed_kph, pressure_mb, days_since_calibration):
    """
    Inserts a new row of contextual data into the 'environmental_context' table,
    linked to a specific measurement by its ID.
    """
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO environmental_context (
                measurement_id, hour_of_day, day_of_week, month_of_year, rainfall_mm, 
                air_temp_c, wind_speed_kph, pressure_mb, days_since_calibration
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (measurement_id, hour_of_day, day_of_week, month_of_year, rainfall_mm, 
              air_temp_c, wind_speed_kph, pressure_mb, days_since_calibration))
        conn.commit()
        conn.close()

def get_latest_data():
    """
    Fetches the single most recent measurement from the database.
    Returns the data as a dictionary or None if the table is empty.
    """
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM measurements ORDER BY timestamp DESC LIMIT 1')
        row = cursor.fetchone()
        conn.close()
    return dict(row) if row else None


# This helper function provides the AI with the most recent environmental data (weather, etc.).
# It finds the "latest" context entry by retrieving the one with the highest ID,
# since new data is always inserted with an incrementing ID.
def get_context_for_latest_measurement():
    """
    Fetches the most recent environmental context entry from the database.
    """
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        # Order by ID DESC to get the latest one recorded
        cursor.execute('SELECT * FROM environmental_context ORDER BY id DESC LIMIT 1')
        row = cursor.fetchone()
        conn.close()
    return dict(row) if row else None     


def summarize_context_for_range(start_date, end_date):
    """
    Fetches and summarizes environmental data for a given date range.
    """
    if not start_date or not end_date:
        return {}
        
    query = """
        SELECT
            AVG(e.rainfall_mm) as avg_rainfall,
            AVG(e.air_temp_c) as avg_air_temp,
            AVG(e.wind_speed_kph) as avg_wind_speed
        FROM environmental_context e
        JOIN measurements m ON e.measurement_id = m.id
        WHERE m.timestamp BETWEEN ? AND ?
    """
    try:
        with DB_LOCK:
            conn = sqlite3.connect(DB_PATH)
            end_date_inclusive = f"{end_date.split(' to ')[-1].strip()} 23:59:59"
            start_date_inclusive = f"{start_date.split(' to ')[0].strip()} 00:00:00"
            
            # Use pandas to easily calculate averages, which handles missing values correctly
            df = pd.read_sql_query(query, conn, params=(start_date_inclusive, end_date_inclusive))
            conn.close()

        if df.empty:
            return {}
            
        summary = df.iloc[0].to_dict()
        return summary
    except Exception as e:
        print(f"Error summarizing context data: {e}")
        return {}
    

def get_latest_reading_with_env():
    """
    Fetches the most recent measurement and joins it with the latest 
    environmental context data.
    """
    conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get the latest measurement
    latest_measurement = cursor.execute("""
        SELECT id, timestamp, temperature, ph, tds, turbidity, water_quality
        FROM measurements ORDER BY timestamp DESC LIMIT 1
    """).fetchone()

    if not latest_measurement:
        return None

    measurement_dict = dict(latest_measurement)

    # Get the latest environmental context associated with that measurement
    env_context = cursor.execute("""
        SELECT rainfall_mm, air_temp_c
        FROM environmental_context WHERE measurement_id = ?
    """, (measurement_dict['id'],)).fetchone()

    measurement_dict['env_context'] = dict(env_context) if env_context else {}
    
    conn.close()
    return measurement_dict


def get_summarized_data_for_range(start_date, end_date):
    """
    Fetches all data within a date range and computes a summary
    (averages and most common quality).
    """
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT temperature, ph, tds, turbidity, water_quality
        FROM measurements WHERE DATE(timestamp) BETWEEN ? AND ?
    """
    # Use pandas to easily read and aggregate the data
    df = pd.read_sql_query(query, conn, params=(start_date, end_date))
    conn.close()

    if df.empty:
        return None

    summary = {
        'avg_temp': df['temperature'].mean(),
        'avg_ph': df['ph'].mean(),
        'avg_tds': df['tds'].mean(),
        'avg_turb': df['turbidity'].mean(),
        'most_common_quality': df['water_quality'].mode()[0] if not df['water_quality'].mode().empty else 'N/A'
    }

    # Format the numbers to two decimal places
    for key in ['avg_temp', 'avg_ph', 'avg_tds', 'avg_turb']:
        if pd.notna(summary[key]):
            summary[key] = round(summary[key], 2)
            
    return summary


def get_recent_timeseries_data(days=7, resample_freq=None, as_dataframe=False, end_time=None):
    """
    Fetches time-series data from the last X days.
    This version is more robust against timestamp format errors.
    """
    conn = sqlite3.connect(DB_PATH)
    
    end_date = pd.to_datetime(end_time) if end_time else datetime.now()
    start_date = end_date - timedelta(days=days)
    
    query = "SELECT timestamp, temperature, ph, tds, turbidity FROM measurements WHERE timestamp BETWEEN ? AND ?"
    
    try:
        df = pd.read_sql_query(query, conn, params=(start_date.strftime("%Y-%m-%d %H:%M:%S"), end_date.strftime("%Y-%m-%d %H:%M:%S")))
    finally:
        conn.close()

    if df.empty:
        print(f"Warning: No data found in the database between {start_date} and {end_date}.")
        return pd.DataFrame() if as_dataframe else []

    # This is the crucial change:
    # 'errors="coerce"' will turn any unreadable timestamp into 'NaT' (Not a Time)
    # instead of crashing. We can then remove these bad rows.
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    df.dropna(subset=['timestamp'], inplace=True)

    if df.empty:
        print("Warning: Data was found, but timestamps could not be parsed.")
        return pd.DataFrame() if as_dataframe else []

    df.set_index('timestamp', inplace=True)

    if resample_freq:
        df = df.resample(resample_freq).mean()
        df.dropna(inplace=True)
        df.reset_index(inplace=True)

    return df if as_dataframe else df.to_dict('records')

def get_thresholds_for_dashboard():
    """
    Fetches thresholds from the database and formats them into a flat
    dictionary required by the dashboard's JavaScript gauges.
    """
    threshold_map = {}
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM water_quality_thresholds").fetchall()
        conn.close()

    for row in rows:
        param = row['parameter_name'].upper()
        level = row['quality_level'].upper()
        
        # This logic mimics the structure of the old threshold_config.py file
        if param == 'PH':
            if level == 'GOOD':
                threshold_map['PH_GOOD_MIN'] = row['min_value']
                threshold_map['PH_GOOD_MAX'] = row['max_value']
            elif level == 'AVERAGE':
                if row['range_identifier'] == 'low':
                    threshold_map['PH_AVERAGE_MIN'] = row['min_value']
                elif row['range_identifier'] == 'high':
                    threshold_map['PH_AVERAGE_MAX'] = row['max_value']
            elif level == 'POOR':
                if row['range_identifier'] == 'low':
                    threshold_map['PH_POOR_MIN'] = row['min_value']
                elif row['range_identifier'] == 'high':
                    threshold_map['PH_POOR_MAX'] = row['max_value']
        elif param == 'TDS':
            if level == 'GOOD':
                threshold_map['TDS_GOOD_MAX'] = row['max_value']
            elif level == 'AVERAGE':
                threshold_map['TDS_AVERAGE_MAX'] = row['max_value']
            elif level == 'POOR':
                threshold_map['TDS_POOR_MAX'] = row['max_value']
        elif param == 'TURBIDITY':
            if level == 'GOOD':
                threshold_map['TURB_GOOD_MAX'] = row['max_value']
            elif level == 'AVERAGE':
                threshold_map['TURB_AVERAGE_MAX'] = row['max_value']
            elif level == 'POOR':
                threshold_map['TURB_POOR_MAX'] = row['max_value']
            # Add a conceptual bad threshold for the gauge's max value
            threshold_map['TURB_BAD_THRESHOLD'] = 500.0 
        elif param == 'TEMPERATURE':
            if level == 'GOOD':
                threshold_map['TEMP_GOOD_MIN'] = row['min_value']
                threshold_map['TEMP_GOOD_MAX'] = row['max_value']
            elif level == 'AVERAGE':
                if row['range_identifier'] == 'low':
                    threshold_map['TEMP_AVERAGE_MIN'] = row['min_value']
                elif row['range_identifier'] == 'high':
                    threshold_map['TEMP_AVERAGE_MAX'] = row['max_value']

    return threshold_map