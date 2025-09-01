# threshold_config.py

# --- pH Thresholds ---
# pH values are typically 0-14.
# Good: 6.5 to 8.5
# Average: 6.0 to <6.5 OR >8.5 to 9.0
# Poor: 4.0 to <6.0 OR >9.0 to 10.0
# Bad: <4.0 OR >10.0
PH_GOOD_MIN = 6.5
PH_GOOD_MAX = 8.5
PH_AVERAGE_MIN = 6.0 # Lower bound for average (e.g., 6.0 to <6.5)
PH_AVERAGE_MAX = 9.0 # Upper bound for average (e.g., >8.5 to 9.0)
PH_POOR_MIN = 4.0    # Lower bound for poor (e.g., 4.0 to <6.0)
PH_POOR_MAX = 10.0   # Upper bound for poor (e.g., >9.0 to 10.0)
# pH values outside PH_POOR_MIN and PH_POOR_MAX are considered 'Bad'

# --- TDS Thresholds (in ppm) ---
# Total Dissolved Solids.
# Good: <= 400 ppm
# Average: >400 ppm to <=700 ppm
# Poor: >700 ppm to <=1000 ppm
# Bad: >1000 ppm
TDS_GOOD_MAX = 400
TDS_AVERAGE_MAX = 700
TDS_POOR_MAX = 1000

# --- Turbidity Thresholds (in NTU) ---
# Nephelometric Turbidity Units.
# Good: <= 5.0 NTU
# Average: >5.0 NTU to <=50.0 NTU
# Poor: >50.0 NTU to <=200.0 NTU
# Bad: >200.0 NTU
TURB_GOOD_MAX = 5.0
TURB_AVERAGE_MAX = 50.0
TURB_POOR_MAX = 200.0
# Note: TURB_BAD_THRESHOLD is not explicitly used for classification in Python,
# but it's kept here as a conceptual max for 'Bad' and for JS gauge max.
TURB_BAD_THRESHOLD = 500.0

# --- Temperature Thresholds (in Celsius) ---
# Good: 5.0°C to 25.0°C
# Average: 0.0°C to <5.0°C OR >25.0°C to 35.0°C
# Bad: <0.0°C OR >35.0°C
TEMP_GOOD_MIN = 5.0
TEMP_GOOD_MAX = 30.0
TEMP_AVERAGE_MIN = 0.0 # Lower bound for average (e.g., 0.0 to <5.0)
TEMP_AVERAGE_MAX = 35.0 # Upper bound for average (e.g., >25.0 to 35.0)
# Temperature values outside TEMP_AVERAGE_MIN and TEMP_AVERAGE_MAX are considered 'Bad'