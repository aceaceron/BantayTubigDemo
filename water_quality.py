# water_quality.py
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score
from sklearn.model_selection import train_test_split
import sqlite3
import datetime
import os

from database import DB_LOCK, DB_PATH, get_all_thresholds_as_dict

# --- Global Model & Feature Importance Storage ---
MODEL_FILE = 'bantaytubig_model.joblib'
model = None 
feature_importances = {}

FEATURE_NAMES = ['temperature', 'ph', 'tds', 'turbidity']
CLASS_NAMES = ['Good', 'Average', 'Poor', 'Bad'] 

# <<< --- THIS ENTIRE FUNCTION HAS BEEN REWRITTEN FOR ROBUSTNESS --- >>>
def _decide_with_static_rules(temp_val, ph_val, tds_val, turb_val, thresholds):
    """
    Decides water quality using robust rules fetched from the database.
    This version safely handles any number of ranges per category.
    """
    print("Executing fallback: Deciding quality with robust rules from DATABASE.")
    
    def is_in_any_range(value, ranges):
        """Helper function to check if a value falls into any of a list of ranges."""
        if value is None or not ranges:
            return False
        for r in ranges:
            min_lim, max_lim = r.get('min_value'), r.get('max_value')
            # Check if the value is within the defined min and max for this range
            if (min_lim is None or value >= min_lim) and \
               (max_lim is None or value <= max_lim):
                return True
        return False

    quality = 'Unknown'
    
    try:
        if is_in_any_range(ph_val, thresholds.get('pH', {}).get('Bad', [])) or \
           is_in_any_range(temp_val, thresholds.get('Temperature', {}).get('Bad', [])) or \
           is_in_any_range(tds_val, thresholds.get('TDS', {}).get('Bad', [])) or \
           is_in_any_range(turb_val, thresholds.get('Turbidity', {}).get('Bad', [])):
            quality = 'Bad'
        elif is_in_any_range(ph_val, thresholds.get('pH', {}).get('Poor', [])) or \
             is_in_any_range(temp_val, thresholds.get('Temperature', {}).get('Poor', [])) or \
             is_in_any_range(tds_val, thresholds.get('TDS', {}).get('Poor', [])) or \
             is_in_any_range(turb_val, thresholds.get('Turbidity', {}).get('Poor', [])):
            quality = 'Poor'
        elif is_in_any_range(ph_val, thresholds.get('pH', {}).get('Average', [])) or \
             is_in_any_range(temp_val, thresholds.get('Temperature', {}).get('Average', [])) or \
             is_in_any_range(tds_val, thresholds.get('TDS', {}).get('Average', [])) or \
             is_in_any_range(turb_val, thresholds.get('Turbidity', {}).get('Average', [])):
            quality = 'Average'
        elif is_in_any_range(ph_val, thresholds.get('pH', {}).get('Good', [])) and \
             is_in_any_range(temp_val, thresholds.get('Temperature', {}).get('Good', [])) and \
             is_in_any_range(tds_val, thresholds.get('TDS', {}).get('Good', [])) and \
             is_in_any_range(turb_val, thresholds.get('Turbidity', {}).get('Good', [])):
            quality = 'Good'

    except Exception as e:
        print(f"ERROR during rule-based decision: {e}")
        quality = 'Unknown'

    probabilities = {name: (1.0 if name == quality else 0.0) for name in CLASS_NAMES}
    if quality == 'Unknown':
        return { "quality": "Unknown", "confidence": "Rule-Based (Error)", "probabilities": {name: 0 for name in CLASS_NAMES} }
    else:
        return { "quality": quality, "confidence": "Rule-Based", "probabilities": probabilities }

def predict_water_quality(temp, ph, tds, turbidity):
    """
    Predicts water quality using the ML model primarily, but falls back to
    database-driven rules if the model is unavailable.
    """
    global model
    
    try:
        temp_val = float(temp) if temp is not None else None
        ph_val = float(ph) if ph is not None else None
        tds_val = float(tds) if tds is not None else None
        turb_val = float(turbidity) if turbidity is not None else None
    except (ValueError, TypeError, AttributeError):
        return { "quality": "Unknown", "confidence": 0, "probabilities": {name: 0 for name in CLASS_NAMES} }

    if model is None or not hasattr(model, 'predict_proba'):
        print("Model not available. Fetching fallback rules from the database...")
        thresholds = get_all_thresholds_as_dict()
        if not thresholds:
            print("ERROR: Could not fetch thresholds from the database for fallback rules.")
            return { "quality": "Unknown", "confidence": "Rule-Based (Error)", "probabilities": {name: 0 for name in CLASS_NAMES} }
        
        return _decide_with_static_rules(temp_val, ph_val, tds_val, turb_val, thresholds)
        
    try:
        features = pd.DataFrame([[temp_val, ph_val, tds_val, turb_val]], columns=FEATURE_NAMES)
        probabilities_array = model.predict_proba(features)[0]
        best_class_index = probabilities_array.argmax()
        predicted_quality = CLASS_NAMES[best_class_index]
        confidence_score = probabilities_array[best_class_index]
        all_probabilities = {name: prob for name, prob in zip(CLASS_NAMES, probabilities_array)}
        
        return { "quality": predicted_quality, "confidence": confidence_score, "probabilities": all_probabilities }
    except Exception as e:
        print(f"Error during ML prediction: {e}")
        return { "quality": "Unknown", "confidence": 0, "probabilities": {name: 0 for name in CLASS_NAMES} }


def train_decision_tree():
    """
    Trains a Random Forest Classifier only if there are at least 250 samples
    for each of the four water quality categories.
    """
    global model, feature_importances
    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Attempting to train model...")

    try:
        with DB_LOCK:
            conn = sqlite3.connect(DB_PATH)
            df = pd.read_sql_query("SELECT * FROM measurements", conn)
            conn.close()

        df = df.dropna(subset=['water_quality'])
        df = df[df['water_quality'].isin(CLASS_NAMES)]
        if df.empty:
            print("No valid labeled data found.")
            return

        MIN_SAMPLES_PER_CLASS = 250
        class_counts = df['water_quality'].value_counts()
        
        missing_classes = [name for name in CLASS_NAMES if name not in class_counts.index]
        underrepresented_classes = {name: count for name, count in class_counts.items() if count < MIN_SAMPLES_PER_CLASS}

        if missing_classes or underrepresented_classes:
            print("--- Training Requirement Not Met ---")
            if missing_classes:
                print(f"The following classes have no data: {missing_classes}")
            if underrepresented_classes:
                print(f"The following classes have fewer than {MIN_SAMPLES_PER_CLASS} samples:")
                for name, count in underrepresented_classes.items():
                    print(f"  - {name}: {count} samples")
            print("Model training aborted.")
            return
        
        print(f"Data validation passed: All {len(CLASS_NAMES)} classes have at least {MIN_SAMPLES_PER_CLASS} samples.")
        
        for col in FEATURE_NAMES:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df = df.dropna(subset=FEATURE_NAMES) 
        if df.empty:
            print("No valid numerical data after cleaning.")
            return

        label_map_inverse = {name: i for i, name in enumerate(CLASS_NAMES)}
        df['water_quality_numeric'] = df['water_quality'].map(label_map_inverse)
        
        df = df.dropna(subset=['water_quality_numeric'])
        df['water_quality_numeric'] = df['water_quality_numeric'].astype(int)

        X = df[FEATURE_NAMES] 
        y = df['water_quality_numeric']

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
        clf = RandomForestClassifier(random_state=42)
        clf.fit(X_train, y_train)

        importances = clf.feature_importances_
        feature_importances = {name: score for name, score in zip(FEATURE_NAMES, importances)}
        print("Feature Importances Captured:", feature_importances)

        y_pred = clf.predict(X_test)
        print(f"Accuracy: {accuracy_score(y_test, y_pred):.2f}")
        
        joblib.dump(clf, MODEL_FILE)
        
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Model trained and saved successfully.")
        model = clf

    except Exception as e:
        print(f"An error occurred during model training: {e}")

def get_feature_importances():
    """Returns the globally stored feature importances."""
    return feature_importances

try:
    if os.path.exists(MODEL_FILE):
        model = joblib.load(MODEL_FILE)
        print("Model loaded from file.")
        if hasattr(model, 'feature_importances_'):
            importances = model.feature_importances_
            feature_importances.update({name: score for name, score in zip(FEATURE_NAMES, importances)})
            print("Feature importances loaded from model.")
    else:
        print("No pre-trained model found. Training initial model...")
        train_decision_tree()
except Exception as e:
    print(f"Could not load or train model on startup. Error: {e}")
    model = None