# water_quality.py
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score
from sklearn.model_selection import train_test_split
import sqlite3
import datetime
import os

# Import all thresholds from the centralized config file
from threshold_config import (
    PH_GOOD_MIN, PH_GOOD_MAX, PH_AVERAGE_MIN, PH_AVERAGE_MAX, PH_POOR_MIN, PH_POOR_MAX,
    TDS_GOOD_MAX, TDS_AVERAGE_MAX, TDS_POOR_MAX,
    TURB_GOOD_MAX, TURB_AVERAGE_MAX, TURB_POOR_MAX, TURB_BAD_THRESHOLD,
    TEMP_GOOD_MIN, TEMP_GOOD_MAX, TEMP_AVERAGE_MIN, TEMP_AVERAGE_MAX
)

try:
    from database import DB_LOCK, DB_PATH
except ImportError:
    print("Warning: 'database.py' or DB_LOCK not found. Assuming no database lock is needed for this script's execution.")
    class MockDBLock:
        def __enter__(self):
            pass
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass
    DB_LOCK = MockDBLock()
    DB_PATH = 'bantaytubig.db'

# --- Global Model & Feature Importance Storage ---
MODEL_FILE = 'bantaytubig_model.joblib'
model = None 
feature_importances = {} # Dictionary to store feature names and their importance

# --- Feature names must match the order of columns in the DataFrame ---
FEATURE_NAMES = ['temperature', 'ph', 'tds', 'turbidity']

def predict_water_quality(temp, ph, tds, turbidity):
    """
    Predicts the water quality (Good, Average, Poor, Bad, or Unknown) based on sensor readings,
    applying predefined thresholds.
    """
    temp_val, ph_val, tds_val, turb_val = None, None, None, None
    if temp is not None and temp != "Error":
        try: temp_val = float(temp)
        except ValueError: pass
    if ph is not None:
        try: ph_val = float(ph)
        except (ValueError, TypeError): pass
    if tds is not None:
        try: tds_val = float(tds)
        except (ValueError, TypeError): pass
    if turbidity is not None:
        try: turb_val = float(turbidity)
        except (ValueError, TypeError): pass

    if ph_val is None or temp_val is None or tds_val is None or turb_val is None: 
        return 'Unknown'

    # (Your original static rules are preserved here)
    if ph_val < PH_POOR_MIN or ph_val > PH_POOR_MAX: return 'Bad'
    if temp_val < TEMP_AVERAGE_MIN or temp_val > TEMP_AVERAGE_MAX: return 'Bad'
    if tds_val > TDS_POOR_MAX: return 'Bad'
    if turb_val > TURB_POOR_MAX: return 'Bad'
    if (ph_val >= PH_POOR_MIN and ph_val < PH_AVERAGE_MIN) or \
       (ph_val > PH_AVERAGE_MAX and ph_val <= PH_POOR_MAX): return 'Poor'
    if (temp_val >= TEMP_AVERAGE_MIN and temp_val < TEMP_GOOD_MIN) or \
       (temp_val > TEMP_GOOD_MAX and temp_val <= TEMP_AVERAGE_MAX): return 'Poor'
    if tds_val > TDS_AVERAGE_MAX and tds_val <= TDS_POOR_MAX: return 'Poor'
    if turb_val > TURB_AVERAGE_MAX and turb_val <= TURB_POOR_MAX: return 'Poor'
    if (ph_val >= PH_AVERAGE_MIN and ph_val < PH_GOOD_MIN) or \
       (ph_val > PH_GOOD_MAX and ph_val <= PH_AVERAGE_MAX): return 'Average'
    if tds_val > TDS_GOOD_MAX and tds_val <= TDS_AVERAGE_MAX: return 'Average'
    if turb_val > TURB_GOOD_MAX and turb_val <= TURB_AVERAGE_MAX: return 'Average'
    if tds_val == 0.00: return 'Good'
    if (PH_GOOD_MIN <= ph_val <= PH_GOOD_MAX and
        TDS_GOOD_MAX >= tds_val >= 0 and
        turb_val <= TURB_GOOD_MAX and
        TEMP_GOOD_MIN <= temp_val <= TEMP_GOOD_MAX): return 'Good'

    # Fallback to ML model
    features = pd.DataFrame([[temp_val, ph_val, tds_val, turb_val]], columns=FEATURE_NAMES)
    if model is None or not hasattr(model, 'predict'):
        print("Warning: ML model not loaded or trained. Relying solely on static thresholds.")
        return 'Unknown'
    try:
        predicted_label = model.predict(features)[0]
        label_map = {0: 'Good', 1: 'Average', 2: 'Poor', 3: 'Bad'} 
        return label_map.get(predicted_label, 'Unknown')
    except Exception as e:
        print(f"Error during ML prediction: {e}")
        return 'Unknown'


def train_decision_tree():
    """
    Trains a Random Forest Classifier and captures feature importances.
    """
    global model, feature_importances
    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Training model...")

    try:
        with DB_LOCK:
            conn = sqlite3.connect(DB_PATH)
            df = pd.read_sql_query("SELECT * FROM measurements", conn)
            conn.close()

        df = df.dropna(subset=['water_quality'])
        df = df[df['water_quality'].isin(['Good', 'Average', 'Poor', 'Bad'])]
        if df.empty:
            print("No valid labeled data for training.")
            return

        for col in FEATURE_NAMES:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df = df.dropna(subset=FEATURE_NAMES) 
        if df.empty:
            print("No valid numerical data after cleaning.")
            return

        label_map_inverse = {'Good': 0, 'Average': 1, 'Poor': 2, 'Bad': 3}
        df['water_quality_numeric'] = df['water_quality'].map(label_map_inverse)
        X = df[FEATURE_NAMES] 
        y = df['water_quality_numeric']

        if len(X) < 10:
            print("Not enough data to split for training.")
            return

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
        clf = RandomForestClassifier(random_state=42)
        clf.fit(X_train, y_train)

        # --- CAPTURE FEATURE IMPORTANCE ---
        importances = clf.feature_importances_
        feature_importances = {name: score for name, score in zip(FEATURE_NAMES, importances)}
        print("Feature Importances Captured:", feature_importances)
        # --- END OF NEW CODE ---

        y_pred = clf.predict(X_test)
        print(f"Accuracy: {accuracy_score(y_test, y_pred):.2f}")
        joblib.dump(clf, MODEL_FILE)
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Model trained and saved.")
        model = clf

    except Exception as e:
        print(f"An error occurred during model training: {e}")

def get_feature_importances():
    """Returns the globally stored feature importances."""
    return feature_importances

# Initial model loading and training
try:
    if os.path.exists(MODEL_FILE):
        model = joblib.load(MODEL_FILE)
        print("Model loaded from file.")
        # --- NEW CODE: Populate feature_importances from loaded model ---
        if hasattr(model, 'feature_importances_'):
            importances = model.feature_importances_
            feature_importances.update({name: score for name, score in zip(FEATURE_NAMES, importances)})
            print("Feature importances loaded from model.")
        # --- END OF NEW CODE ---
    else:
        print("No pre-trained model found. Training initial model...")
        train_decision_tree()
except Exception as e:
    print(f"Could not load or train model on startup. Error: {e}")
    model = RandomForestClassifier(random_state=42)