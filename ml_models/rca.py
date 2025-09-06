# ml_models/rca.py
import pandas as pd

def find_correlations(anomaly, sensor_context_df, env_context):
    """
    Analyzes correlations between an anomalous parameter and other data.
    """
    suggestions = []
    if sensor_context_df.empty:
        return ["No contextual sensor data available."]

    try:
        # --- Step 1: Perform Correlation Analysis on Sensor Data ---
        df = sensor_context_df.copy()
        # Drop non-numeric columns before correlation
        df_numeric = df.select_dtypes(include=['number'])
        
        corr_matrix = df_numeric.corr()
        
        if anomaly['parameter'] in corr_matrix:
            anomaly_correlations = corr_matrix[anomaly['parameter']].drop(anomaly['parameter']).abs().sort_values(ascending=False)

            for param, corr_value in anomaly_correlations.head(2).items():
                if corr_value > 0.5: # Only suggest strong correlations
                    suggestions.append({
                        "correlated_parameter": param.replace('_', ' ').title(),
                        "correlation_score": int(corr_value * 100)
                    })

    except Exception as e:
        print(f"Error in RCA correlation: {e}")

    # --- Step 2: Format the correlation suggestions ---
    ranked_list = []
    for suggestion in suggestions:
        ranked_list.append(
            f"{suggestion['correlated_parameter']} (Correlation: {suggestion['correlation_score']}%)"
        )
        
    # --- Step 3: Add Rule-Based Suggestions for Environmental Data ---
    # Instead of correlating a single value, we check it against a threshold.
    if env_context and env_context.get('rainfall_mm', 0) > 1.0: # e.g., if rainfall > 1.0mm
        ranked_list.append("Event occurred during a period of rainfall.")
        
    if not ranked_list:
        return ["No strong correlations or significant environmental factors found."]
        
    return ranked_list
