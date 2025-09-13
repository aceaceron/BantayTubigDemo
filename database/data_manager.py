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

def get_recent_timeseries_data(days=None, hours=None, end_time=None, resample_freq=None, as_dataframe=False):
    """
    Fetches recent time-series data from the measurements table.
    
    """
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        
        # Determine the time window for the query
        if end_time is None:
            end_time = datetime.now()
        # Ensure end_time is a datetime object before doing calculations
        elif isinstance(end_time, str):
            end_time = datetime.fromisoformat(end_time)
        # -----------------------
        
        if hours:
            start_time = end_time - timedelta(hours=hours)
        elif days:
            start_time = end_time - timedelta(days=days)
        else:
            start_time = end_time - timedelta(days=1)

        query = "SELECT timestamp, temperature, ph, tds, turbidity FROM measurements WHERE timestamp BETWEEN ? AND ? ORDER BY timestamp ASC"
        
        if as_dataframe:
            df = pd.read_sql_query(query, conn, params=(start_time, end_time))
            if resample_freq and not df.empty:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df.set_index('timestamp').resample(resample_freq).mean().interpolate(method='time').reset_index()
            return df
        else:
            cursor = conn.cursor()
            cursor.execute(query, (start_time, end_time))
            return cursor.fetchall()
            
    except sqlite3.Error as e:
        print(f"Database error in get_recent_timeseries_data: {e}")
        return pd.DataFrame() if as_dataframe else []
    finally:
        if conn:
            conn.close()

def get_environmental_context_for_anomaly(anomaly_timestamp):
    """
    Finds the closest environmental context reading to a given anomaly timestamp.
    
    """
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row 
        cursor = conn.cursor()

        # This query now JOINS the tables to order by the correct timestamp
        query = """
            SELECT ec.rainfall_mm, ec.air_temp_c
            FROM environmental_context AS ec
            JOIN measurements AS m ON ec.measurement_id = m.id
            ORDER BY ABS(strftime('%s', m.timestamp) - strftime('%s', ?))
            LIMIT 1
        """
        
        cursor.execute(query, (anomaly_timestamp,))
        result = cursor.fetchone()

        return dict(result) if result else {}

    except sqlite3.Error as e:
        print(f"Database error in get_environmental_context_for_anomaly: {e}")
        return {}
    finally:
        if conn:
            conn.close()


def get_annotated_anomalies():
    """
    Fetches a history of all anomalies that have been annotated.
    
    It joins the anomalies, annotations, and users tables to create a
    comprehensive log entry for each reviewed event.
    """
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row 
        cursor = conn.cursor()

        # This query JOINS the three relevant tables to get all necessary info
        query = """
            SELECT
                anom.id,
                anom.timestamp,
                anom.parameter,
                anom.value,
                anom.anomaly_type,
                ann.label,
                ann.comments,
                ann.timestamp as annotated_at,
                usr.full_name as annotated_by
            FROM ml_anomalies AS anom
            JOIN ml_annotations AS ann ON anom.id = ann.anomaly_id
            JOIN users AS usr ON ann.user_id = usr.id
            WHERE anom.is_annotated = 1
            ORDER BY ann.timestamp DESC
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        # Convert list of Row objects to list of dictionaries
        return [dict(row) for row in results]

    except sqlite3.Error as e:
        print(f"Database error in get_annotated_anomalies: {e}")
        return []
    finally:
        if conn:
            conn.close()

def save_annotation(anomaly_id, user_id, label, comments):
    """
    Saves a user's annotation feedback to the database.

    This function performs two critical steps:
    1. Inserts the feedback (label, comments) into the 'ml_annotations' table.
    2. Updates the original anomaly in the 'ml_anomalies' table to mark it
       as 'is_annotated', which removes it from the pending queue and makes
       it appear in the history.
    """
    with DB_LOCK:
        conn = None
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Step 1: Insert the new annotation record
            cursor.execute("""
                INSERT INTO ml_annotations (anomaly_id, user_id, label, comments, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (anomaly_id, user_id, label, comments, datetime.now()))
            
            # Step 2: Update the original anomaly's status
            cursor.execute("""
                UPDATE ml_anomalies
                SET is_annotated = 1
                WHERE id = ?
            """, (anomaly_id,))
            
            conn.commit()
            print(f"Successfully saved annotation for anomaly_id: {anomaly_id}")

        except sqlite3.Error as e:
            print(f"Database error in save_annotation: {e}")
        finally:
            if conn:
                conn.close()