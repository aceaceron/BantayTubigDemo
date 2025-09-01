# In ml_models/forecasting.py
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
# MODIFIED: Import the updated database function
from database import get_recent_timeseries_data, save_forecast

def generate_forecasts():
    """
    Fetches historical data, trains a forecasting model for each parameter,
    and saves the forecast to the database.
    """
    parameters_to_forecast = ['temperature', 'ph', 'tds', 'turbidity']
    
    for param in parameters_to_forecast:
        try:
            # MODIFICATION: We now fetch 30 days of data, resampled to HOURLY averages.
            # This is much more efficient than using thousands of raw data points.
            df = get_recent_timeseries_data(days=30, resample_freq='H', as_dataframe=True)
            
            if df.empty or len(df) < 50: # Need enough data to forecast
                print(f"Not enough data to forecast {param}. Skipping.")
                continue

            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.set_index('timestamp')
            
            # Since data is already resampled, we may not need to interpolate.
            # This model is now trained on stable hourly trends.
            model = ARIMA(df[param], order=(5, 1, 0)) # p,d,q orders can be tuned
            model_fit = model.fit()
            
            # Forecast the next 24 hours
            forecast_result = model_fit.get_forecast(steps=24)
            forecast_df = forecast_result.summary_frame()
            forecast_df.reset_index(inplace=True)
            forecast_df.rename(columns={'index': 'timestamp', 'mean': 'forecast_value',
                                        'mean_ci_lower': 'lower_bound', 'mean_ci_upper': 'upper_bound'}, inplace=True)

            save_forecast(param, forecast_df)
            print(f"Successfully generated and saved forecast for {param}.")

        except Exception as e:
            print(f"Error forecasting {param}: {e}")