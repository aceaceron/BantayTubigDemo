# ml_models/rca.py
import pandas as pd

def find_correlations(anomaly, sensor_context_df, env_context):
    """
    Analyzes correlations between an anomalous parameter and other data.
    """
    suggestions = []
    if sensor_context_df.empty:
        return suggestions

    try:
        # Combine all data into one DataFrame for correlation analysis
        df = sensor_context_df.copy()
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('timestamp')

        # Add environmental data if available
        if env_context and env_context.get('rainfall_mm') is not None:
            df['rainfall'] = env_context.get('rainfall_mm', 0)
        
        # Calculate the correlation matrix
        corr_matrix = df.corr()
        
        # Get correlations for the anomalous parameter
        anomaly_correlations = corr_matrix[anomaly['parameter']].drop(anomaly['parameter']).abs().sort_values(ascending=False)

        for param, corr_value in anomaly_correlations.head(2).items():
            if corr_value > 0.5: # Only suggest strong correlations
                suggestions.append({
                    "correlated_parameter": param.replace('_', ' ').title(),
                    "correlation_score": int(corr_value * 100)
                })

    except Exception as e:
        print(f"Error in RCA: {e}")

    # Format into human-readable strings
    ranked_list = []
    for suggestion in suggestions:
        ranked_list.append(
            f"{suggestion['correlated_parameter']} (Correlation: {suggestion['correlation_score']}%)"
        )
        
    if not ranked_list:
        return ["No strong correlations found."]
        
    return ranked_list