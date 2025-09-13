# ml_models/forecasting.py

# === IMPORTS ==================================================================
# Used for powerful data manipulation and analysis, particularly for its DataFrame
# structures which are essential for handling time-series data.
import pandas as pd

# Imports the ARIMA model from the statsmodels library, a standard and powerful
# tool for time-series forecasting.
from statsmodels.tsa.arima.model import ARIMA

# Imports custom database functions to fetch historical data for model training
# and to save the final forecast results.
from database import get_recent_timeseries_data, save_forecast

import warnings
from statsmodels.tools.sm_exceptions import ValueWarning

# ==============================================================================
# === STANDARD FORECAST GENERATION =============================================
# ==============================================================================
# This function is responsible for creating the official, scheduled system forecast.

def generate_forecasts():
    """
    Creates and saves the standard 24-hour forecast for all water quality parameters.
    """
    parameters_to_forecast = ['temperature', 'ph', 'tds', 'turbidity']
    successful_params = []
    
    for param in parameters_to_forecast:
        try:
            df = get_recent_timeseries_data(days=30, resample_freq='h', as_dataframe=True)
            if df.empty or len(df) < 50:
                continue

            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.set_index('timestamp')
            
            # Suppress the verbose ValueWarning from statsmodels during model fitting
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=ValueWarning)
                model = ARIMA(df[param].dropna(), order=(5, 1, 0))
                model_fit = model.fit()
            
            forecast_result = model_fit.get_forecast(steps=24)
            forecast_df = forecast_result.summary_frame()
            forecast_df.reset_index(inplace=True)
            forecast_df.rename(columns={'index': 'timestamp', 'mean': 'forecast_value',
                                        'mean_ci_lower': 'lower_bound', 'mean_ci_upper': 'upper_bound'}, inplace=True)

            # Select only the columns that exist in your database table to prevent errors.
            columns_to_save = ['timestamp', 'forecast_value', 'lower_bound', 'upper_bound']
            forecast_df_to_save = forecast_df[columns_to_save]
            
            save_forecast(param, forecast_df_to_save)
            successful_params.append(param)

        except Exception as e:
            # Print a cleaner error message if one parameter fails
            print(f"  [ERROR] Forecasting {param}: {e}")

    # Print a single summary line instead of one for each parameter
    if successful_params:
        print(f"  [SUCCESS] Forecasts generated for: {', '.join(successful_params)}")
