# ml_models/main_processor.py
from . import forecasting, anomaly_detection, rca
from database import get_recent_timeseries_data, log_anomaly, get_environmental_context_for_anomaly

def run_ml_analysis():
    """
    The main function to run the entire ML pipeline.
    This should be called by a scheduled background task.
    """
    print("Starting periodic ML analysis...")

    # 1. Generate and save new forecasts
    forecasting.generate_forecasts()
    print("-> Forecasting models updated.")

    # 2. Detect anomalies using the digital twin model
    detected_anomalies = anomaly_detection.detect_anomalies()
    print(f"-> Found {len(detected_anomalies)} new potential anomalies.")

    # 3. For each anomaly, perform Root Cause Analysis (RCA)
    for anomaly in detected_anomalies:
        timestamp = anomaly['timestamp']
        parameter = anomaly['parameter']
        
        # Get environmental data around the time of the anomaly
        env_context = get_environmental_context_for_anomaly(timestamp)
        
        # Get sensor data around the time of the anomaly
        sensor_context = get_recent_timeseries_data(hours=1, end_time=timestamp)

        # Perform correlation analysis
        rca_suggestions = rca.find_correlations(anomaly, sensor_context, env_context)
        
        anomaly['rca_suggestions'] = rca_suggestions
        
        # 4. Log the anomaly with its RCA suggestions to the database
        log_anomaly(
            timestamp=anomaly['timestamp'],
            parameter=anomaly['parameter'],
            value=anomaly['value'],
            severity=anomaly['severity'],
            anomaly_type=anomaly['type'],
            rca_suggestions=rca_suggestions
        )
        print(f"-> Logged anomaly for '{parameter}' with RCA suggestions.")

    print("ML analysis complete.")