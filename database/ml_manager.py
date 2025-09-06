# database/ml_manager.py
import sqlite3
import json
import pandas as pd
from .config import DB_PATH

def log_anomaly(timestamp, parameter, value, severity, anomaly_type, rca_suggestions):
    """Logs a detected anomaly to the database."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        INSERT INTO ml_anomalies (timestamp, parameter, value, severity, anomaly_type, rca_suggestions)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (timestamp, parameter, value, severity, anomaly_type, json.dumps(rca_suggestions)))
    conn.commit()
    conn.close()

def save_forecast(parameter, forecast_df):
    """Deletes old forecasts and saves the new one."""
    conn = sqlite3.connect(DB_PATH)
    # Clear old forecasts for this parameter
    conn.execute("DELETE FROM ml_forecasts WHERE parameter = ?", (parameter,))
    # Save new forecast
    forecast_df['parameter'] = parameter
    forecast_df.to_sql('ml_forecasts', conn, if_exists='append', index=False)
    conn.close()
    
def get_latest_forecasts():
    """Gets the most recent forecast for each parameter."""
    conn = sqlite3.connect(DB_PATH)
    forecasts = {}
    params = ['temperature', 'ph', 'tds', 'turbidity']
    for p in params:
        df = pd.read_sql_query("SELECT timestamp, forecast_value, lower_bound, upper_bound FROM ml_forecasts WHERE parameter = ? ORDER BY timestamp", conn, params=(p,))
        forecasts[p] = df.to_dict('records')
    conn.close()
    return forecasts

def get_unannotated_anomalies():
    """Fetches anomalies that have not yet been labeled by a user."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ml_anomalies WHERE is_annotated = 0 ORDER BY timestamp DESC")
    anomalies_raw = cursor.fetchall()
    anomalies = []
    for row in anomalies_raw:
        anomaly = dict(row)
        anomaly['rca_suggestions'] = json.loads(anomaly['rca_suggestions'])
        anomalies.append(anomaly)
    conn.close()
    return anomalies
