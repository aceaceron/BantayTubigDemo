# weather_api.py
import requests
import json

def get_weather_data(lat, lon):
    """
    Fetches current weather data from the OpenWeatherMap API.
    Returns a dictionary with the required environmental context data.
    """
    # --- Your OpenWeatherMap API key is now included ---
    api_key = "fe70b33e2fe0970d115190bc23fbd4a4"
    
    # API endpoint for current weather data
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        data = response.json()

        # Extract the required information, providing defaults if a key is missing
        rainfall = data.get('rain', {}).get('1h', 0.0) # Rainfall in the last hour
        
        weather_context = {
            "rainfall_mm": float(rainfall),
            "air_temp_c": data.get('main', {}).get('temp'),
            "wind_speed_kph": data.get('wind', {}).get('speed', 0.0) * 3.6, # Convert m/s to kph
            "pressure_mb": data.get('main', {}).get('pressure')
        }
        return weather_context

    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather data: {e}")
        # Return default values on failure
        return {
            "rainfall_mm": 0.0, "air_temp_c": None, "wind_speed_kph": None, "pressure_mb": None
        }
