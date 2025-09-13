# ml_models/main_processor.py
from datetime import datetime
from . import forecasting, anomaly_detection, rca
from database import get_recent_timeseries_data, log_anomaly, get_environmental_context_for_anomaly

def run_ml_analysis():
    """
    The main function to run the entire ML pipeline, now with user-friendly logging.
    """
    print("\n----- Starting Periodic ML Analysis -----")

    # 1. Generate and save new forecasts
    print("Step 1: Generating forecasts...")
    forecasting.generate_forecasts()

    # 2. Detect anomalies using the digital twin model
    print("\nStep 2: Detecting anomalies...")
    detected_anomalies = anomaly_detection.detect_anomalies()
    
    if not detected_anomalies:
        print("  [INFO] No new potential anomalies found.")
    else:
        print(f"  [INFO] Found {len(detected_anomalies)} new potential anomalies.")
        # 3. For each anomaly, perform Root Cause Analysis (RCA) and log
        print("\nStep 3: Analyzing and logging new anomalies...")
        for anomaly in detected_anomalies:
            # Convert the timestamp string into a proper datetime object
            timestamp = datetime.fromisoformat(anomaly['timestamp'])
            
            parameter = anomaly['parameter']
            
            env_context = get_environmental_context_for_anomaly(timestamp)
            sensor_context = get_recent_timeseries_data(hours=1, end_time=timestamp, as_dataframe=True)
            rca_suggestions = rca.find_correlations(anomaly, sensor_context, env_context)
            
            anomaly['rca_suggestions'] = rca_suggestions
            
            log_anomaly(
                timestamp=timestamp, # Pass the datetime object
                parameter=anomaly['parameter'],
                value=anomaly['value'],
                severity=anomaly['severity'],
                anomaly_type=anomaly['type'],
                rca_suggestions=rca_suggestions
            )
            # The .strftime() method will now work correctly on the datetime object
            print(f"  -> Logged '{parameter}' anomaly from {timestamp.strftime('%Y-%m-%d %H:%M')}.")

    print("----- ML Analysis Complete -----\n")