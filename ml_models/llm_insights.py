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

# ==============================================================================
# === ON-DEMAND DEMO FORECASTS =================================================
# ==============================================================================
# This function generates live forecasts for the user interface demos.

def generate_demo_forecasts(source='continuous_30d'):
    """
    Generates a forecast on-the-fly for demonstration purposes.
    
    How it works:
    1. This function is triggered by the API when a user selects a "Demo" option
       on the "Forecasting" tab. Its results are NOT saved to the database.
    2. It fetches 30 days of historical data as a baseline.
    3. It checks the 'source' argument to determine the demo type:
       - 'continuous_30d': Uses the data as-is to show the model's performance
         under ideal conditions.
       - 'non_continuous_7d': Artificially removes a chunk of data to simulate
         a sensor outage, showing how the model handles missing information.
    4. It cleans the data by interpolating (filling in) gaps and enforcing a
       regular hourly frequency, which is critical for the model's stability.
    5. It trains a new ARIMA model on this prepared demo data and generates a forecast.
    6. The final forecast is returned directly to the API to be displayed on the chart.
    """
    parameters = ['temperature', 'ph', 'tds', 'turbidity']
    forecasts = {'temp': [], 'ph': [], 'tds': [], 'turbidity': []}
    param_map_short = {'temperature': 'temp', 'ph': 'ph', 'tds': 'tds', 'turbidity': 'turbidity'}

    for param in parameters:
        try:
            df = get_recent_timeseries_data(days=30, resample_freq='h', as_dataframe=True)
            if df.empty or len(df) < 50:
                print(f"Not enough base data for demo forecast: {param}")
                continue

            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.set_index('timestamp')

            # If the demo is for non-continuous data, create an artificial gap.
            if source == 'non_continuous_7d':
                if len(df) > 100:
                    start_drop = len(df) // 4
                    end_drop = start_drop * 3
                    df.iloc[start_drop:end_drop] = None
            
            # --- Data Cleaning and Preparation ---
            # Interpolate to fill any major gaps in the time series.
            df[param] = df[param].interpolate(method='time')

            # Enforce a regular hourly frequency on the index. This is crucial for
            # the model to understand the time intervals correctly.
            df = df.asfreq('h')
            
            # Interpolate again to fill any minor gaps that `asfreq` might have created.
            df[param] = df[param].interpolate(method='time')
            df.dropna(subset=[param], inplace=True)

            # Train a new model on the prepared demo data.
            model = ARIMA(df[param], order=(5, 1, 0))
            model_fit = model.fit()
            forecast_result = model_fit.get_forecast(steps=24)
            
            forecast_df = forecast_result.summary_frame()
            forecast_df.reset_index(inplace=True)
            forecast_df.rename(columns={'index': 'timestamp', 'mean': 'forecast_value',
                                        'mean_ci_lower': 'lower_bound', 'mean_ci_upper': 'upper_bound'}, inplace=True)
            
            # Format the data to be sent back to the frontend.
            short_name = param_map_short[param]
            forecast_df['timestamp'] = forecast_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
            forecasts[short_name] = forecast_df.to_dict('records')

        except Exception as e:
            print(f"Error generating demo forecast for {param} ('{source}'): {e}")
            continue
    
    return forecasts
