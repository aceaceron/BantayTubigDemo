# This script will test the data fetching function in isolation.
from database.data_manager import get_recent_timeseries_data

print("--- Testing function for Anomaly Detection (last 24 hours) ---")
anomaly_df = get_recent_timeseries_data(days=1, as_dataframe=True)
if not anomaly_df.empty:
    print(f"Success! Found {len(anomaly_df)} rows.")
    print(anomaly_df.head())
else:
    print("Failure: Function returned no data for the last 24 hours.")

print("\n--- Testing function for Forecasting (last 30 days, hourly avg) ---")
forecast_df = get_recent_timeseries_data(days=30, resample_freq='H', as_dataframe=True)
if not forecast_df.empty:
    print(f"Success! Found {len(forecast_df)} rows after resampling.")
    print(forecast_df.head())
else:
    print("Failure: Function returned no data for the last 30 days.")