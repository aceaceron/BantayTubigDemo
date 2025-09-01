# ml_models/anomaly_detection.py
import pandas as pd
from sklearn.ensemble import IsolationForest
from database import get_recent_timeseries_data

def detect_anomalies():
    """
    Uses an Isolation Forest model as a 'digital twin' to detect
    unusual deviations in the latest sensor readings.
    """
    anomalies = []
    
    try:
        # 1. Fetch the last 24 hours of data to establish a 'normal' baseline
        df = get_recent_timeseries_data(hours=24, as_dataframe=True)
        if df.empty or len(df) < 20:
            return [] # Not enough data

        # Select features for the model
        features = ['temperature', 'ph', 'tds', 'turbidity']
        df_features = df[features].dropna()

        # 2. Train the Isolation Forest model
        # Contamination='auto' is a good starting point
        model = IsolationForest(contamination='auto', random_state=42)
        model.fit(df_features)

        # 3. Check the most recent data point
        latest_reading = df_features.iloc[-1:].copy()
        prediction = model.predict(latest_reading)
        decision_score = model.decision_function(latest_reading)

        # -1 indicates an anomaly
        if prediction[0] == -1:
            severity = abs(decision_score[0]) # A simple severity score
            
            # Determine which parameter deviated the most
            mean_values = df_features.mean()
            deviation = (latest_reading.iloc[0] - mean_values).abs()
            most_deviated_param = deviation.idxmax()
            value = latest_reading.iloc[0][most_deviated_param]

            # Identify if it's a positive or negative event
            anomaly_type = "Improvement" if value < mean_values[most_deviated_param] and most_deviated_param == 'turbidity' else "Issue"

            anomalies.append({
                "timestamp": df.iloc[-1]['timestamp'],
                "parameter": most_deviated_param,
                "value": value,
                "severity": round(severity, 3),
                "type": anomaly_type
            })
            
    except Exception as e:
        print(f"Error during anomaly detection: {e}")
        
    return anomalies