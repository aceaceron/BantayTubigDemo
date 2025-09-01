import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score
from sklearn.model_selection import train_test_split
import sqlite3
import datetime
import os # Import os for file checking

# Assuming 'database.py' exists and provides DB_LOCK
try:
    from database import DB_LOCK
except ImportError:
    print("Warning: 'database.py' or DB_LOCK not found. Assuming no database lock is needed for this script's execution.")
    class MockDBLock:
        def __enter__(self):
            pass
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass
    DB_LOCK = MockDBLock()


# --- Global Model Loading ---
MODEL_FILE = 'water_quality_model.joblib'
model = None # Initialize model to None
try:
    if os.path.exists(MODEL_FILE):
        model = joblib.load(MODEL_FILE)
    else:
        # If model file doesn't exist, we'll try to train it later or use default for prediction
        model = RandomForestClassifier(random_state=42) # Initialize for potential training
except Exception as e:
    model = RandomForestClassifier(random_state=42) # Fallback


# --- Define Water Quality Thresholds ---
# pH:
PH_GOOD_MIN = 6.5
PH_GOOD_MAX = 8.5
PH_AVERAGE_MIN = 6.0
PH_AVERAGE_MAX = 9.0
PH_POOR_MIN = 5.0
PH_POOR_MAX = 10.0

# Temperature (in Celsius):
TEMP_GOOD_MIN = 10.0
TEMP_GOOD_MAX = 30.0
TEMP_AVERAGE_MIN = 5.0
TEMP_AVERAGE_MAX = 40.0 # Note: Your JS had 35.0 for bad threshold. Aligning for consistency if possible.
TEMP_POOR_MIN = 35.0 # Adjusted based on your JS for consistency with 'Bad' threshold

# TDS (in ppm):
TDS_GOOD_MIN = 0
TDS_GOOD_MAX = 150
TDS_AVERAGE_MAX = 300
TDS_POOR_MAX = 500

def predict_water_quality(temp, ph, tds):
    """
    Predicts the water quality (Good, Average, Poor, Bad, or Unknown) based on sensor readings,
    applying predefined thresholds, and then using the trained model for finer classification
    within acceptable ranges.
    """

    temp_val = None
    if temp is not None and temp != "Error":
        try:
            temp_val = float(temp)
        except ValueError:
            temp_val = None # Ensure it's None if conversion fails
    
    ph_val = None
    if ph is not None:
        try:
            ph_val = float(ph)
        except (ValueError, TypeError):
            ph_val = None

    tds_val = None
    if tds is not None:
        try:
            tds_val = float(tds)
        except (ValueError, TypeError):
            tds_val = None

    # --- Apply Threshold-based Rules First (strictest conditions first) ---

    if ph_val is not None and (ph_val < PH_POOR_MIN or ph_val > PH_POOR_MAX):
    
        return 'Bad'
    if temp_val is not None and (temp_val < TEMP_AVERAGE_MIN or temp_val >= TEMP_POOR_MIN):
        return 'Bad'
    if tds_val is not None and tds_val > TDS_POOR_MAX:
        return 'Bad'
    
    if ph_val is not None and ((ph_val >= PH_POOR_MIN and ph_val < PH_AVERAGE_MIN) or (ph_val > PH_AVERAGE_MAX and ph_val <= PH_POOR_MAX)):
        return 'Poor'
    if temp_val is not None and (temp_val > TEMP_GOOD_MAX and temp_val < TEMP_POOR_MIN):
        return 'Poor'
    if tds_val is not None and (tds_val > TDS_AVERAGE_MAX and tds_val <= TDS_POOR_MAX):
        return 'Poor'

    if ph_val is not None and ((ph_val >= PH_AVERAGE_MIN and ph_val < PH_GOOD_MIN) or (ph_val > PH_GOOD_MAX and ph_val <= PH_AVERAGE_MAX)):
        return 'Average'
    if temp_val is not None and (temp_val < TEMP_GOOD_MIN or (temp_val > TEMP_GOOD_MAX and temp_val <= TEMP_AVERAGE_MAX)):
        return 'Average'
    if tds_val is not None and (tds_val > TDS_GOOD_MAX and tds_val <= TDS_AVERAGE_MAX):
        return 'Average'

    # --- Explicit rule for TDS=0.00:
    if tds_val == 0.00:
        return 'Good'

    # --- If no hard threshold triggered, use ML model for 'Good' or finer distinctions ---
    if ph_val is None or temp_val is None or tds_val is None:
        return 'Unknown' # Cannot predict with ML if any core value is missing

    features = pd.DataFrame([[temp_val, ph_val, tds_val]], columns=['temperature', 'ph', 'tds'])

    if model is None or not hasattr(model, 'predict'):
        return 'Unknown'
    if not hasattr(model, 'estimators_') or not model.estimators_:
        return 'Unknown'

    try:
        predicted_label = model.predict(features)[0]
        label_map = {0: 'Good', 1: 'Average', 2: 'Poor'}
        ml_prediction = label_map.get(predicted_label, 'Unknown')
        return ml_prediction

    except Exception as e:
        return 'Unknown'

def get_detailed_water_analysis(temp, ph, tds):
    """
    Predicts water quality and generates detailed, dynamic explanations
    including reasoning, consumability, other uses, and suggestions.
    This logic integrates the rule-based explanations from your frontend.
    """
    quality = predict_water_quality(temp, ph, tds)

    # Ensure temp, ph, tds are properly converted to floats for explanation logic
    temp_val = float(temp) if temp is not None and (isinstance(temp, (int, float)) or (isinstance(temp, str) and temp.replace('.', '', 1).isdigit())) else None
    ph_val = float(ph) if ph is not None and (isinstance(ph, (int, float)) or (isinstance(ph, str) and ph.replace('.', '', 1).isdigit())) else None
    tds_val = float(tds) if tds is not None and (isinstance(tds, (int, float)) or (isinstance(tds, str) and tds.replace('.', '', 1).isdigit())) else None

    reason = ""
    consumable = "Status: Unknown"
    other_uses = ""
    suggestion = ""
    notes = ""
    title_text = "Water Quality Details: "
    reason_tl = ""
    consumable_tl = ""
    other_uses_tl = ""
    suggestion_tl = ""
    notes_tl = ""
    title_text_tl = "Mga Detalye ng Kalidad ng Tubig: "


    # Define ideal ranges for explanation (from JS)
    ideal_temp = {"min": 20, "max": 30}
    ideal_ph = {"min": 6.5, "max": 8.5}
    ideal_tds = {"min": 0, "max": 300}

    issues = []
    issues_tl = [] # Tagalog translations for issues

    # --- Dynamic Issue Detection (Moved from index.html JS) ---
    # These generate specific points for the explanation based on current values.

    if ph_val is not None:
        if ph_val < PH_POOR_MIN or ph_val > PH_POOR_MAX:
            issues.append(f"pH ({ph_val:.2f}) is critically low (highly acidic) or high (highly alkaline).")
            issues_tl.append(f"Ang pH ({ph_val:.2f}) ay kritikal na mababa (lubhang acidic) o mataas (lubhang alkaline).")
        elif (ph_val >= PH_POOR_MIN and ph_val < PH_AVERAGE_MIN) or (ph_val > PH_AVERAGE_MAX and ph_val <= PH_POOR_MAX):
            issues.append(f"pH ({ph_val:.2f}) is significantly low (acidic) or high (alkaline).")
            issues_tl.append(f"Ang pH ({ph_val:.2f}) ay lubhang mababa (acidic) o mataas (alkaline).")
        elif (ph_val >= PH_AVERAGE_MIN and ph_val < PH_GOOD_MIN) or (ph_val > PH_GOOD_MAX and ph_val <= PH_AVERAGE_MAX):
            issues.append(f"pH ({ph_val:.2f}) is slightly off the ideal range.")
            issues_tl.append(f"Ang pH ({ph_val:.2f}) ay bahagyang wala sa ideal na saklaw.")

    if temp_val is not None:
        # Note: Your JS used 35.0 for bad and 30.0 for good max
        if temp_val < TEMP_AVERAGE_MIN: # Below 5.0
            issues.append(f"Temperature ({temp_val:.1f}°C) is dangerously cold.")
            issues_tl.append(f"Ang Temperatura ({temp_val:.1f}°C) ay mapanganib na malamig.")
        elif temp_val >= TEMP_POOR_MIN: # >= 35.0
             issues.append(f"Temperature ({temp_val:.1f}°C) is dangerously hot.")
             issues_tl.append(f"Ang Temperatura ({temp_val:.1f}°C) ay mapanganib na mainit.")
        elif temp_val > TEMP_GOOD_MAX and temp_val < TEMP_POOR_MIN: # 30.0 < temp < 35.0
            issues.append(f"Temperature ({temp_val:.1f}°C) is uncomfortably hot.")
            issues_tl.append(f"Ang Temperatura ({temp_val:.1f}°C) ay hindi kumportable na mainit.")
        elif temp_val < TEMP_GOOD_MIN: # < 10.0
            issues.append(f"Temperature ({temp_val:.1f}°C) is quite cold.")
            issues_tl.append(f"Ang Temperatura ({temp_val:.1f}°C) ay medyo malamig.")
        elif quality.lower() == 'good' and (temp_val < ideal_temp["min"] or temp_val > ideal_temp["max"]):
            issues.append(f"Temperature ({temp_val:.1f}°C) is outside the comfortable drinking range ({ideal_temp['min']}-{ideal_temp['max']}°C).")
            issues_tl.append(f"Ang Temperatura ({temp_val:.1f}°C) ay nasa labas ng komportableng saklaw ng pag-inom ({ideal_temp['min']}-{ideal_temp['max']}°C).")


    if tds_val is not None:
        if tds_val > TDS_POOR_MAX:
            issues.append(f"TDS ({tds_val:.0f} ppm) is excessively high, indicating severe contamination.")
            issues_tl.append(f"Ang TDS ({tds_val:.0f} ppm) ay labis na mataas, na nagpapahiwatig ng matinding kontaminasyon.")
        elif tds_val > TDS_AVERAGE_MAX and tds_val <= TDS_POOR_MAX:
            issues.append(f"TDS ({tds_val:.0f} ppm) is high, suggesting considerable impurities.")
            issues_tl.append(f"Ang TDS ({tds_val:.0f} ppm) ay mataas, na nagpapahiwatig ng malaking karumihan.")
        elif tds_val > TDS_GOOD_MAX and tds_val <= TDS_AVERAGE_MAX:
            issues.append(f"TDS ({tds_val:.0f} ppm) is moderately elevated.")
            issues_tl.append(f"Ang TDS ({tds_val:.0f} ppm) ay katamtamang mataas.")

    # --- Generate Explanations based on Quality and Detected Issues ---
    if quality.lower() == 'good':
        reason = "The water quality is <strong>Good</strong>! All key parameters are within healthy and desirable ranges."
        reason_tl = "Ang kalidad ng tubig ay <strong>Maganda</strong>! Lahat ng pangunahing parametro ay nasa malusog at kanais-nais na mga saklaw."
        notes = "Notes: Ideal for drinking, excellent for general household use, cooking, and most plant watering."
        notes_tl = "Mga Tala: Mainam para sa pag-inom, napakahusay para sa pangkalahatang gamit sa bahay, pagluluto, at karamihan sa pagdidilig ng halaman."
        if issues:
            reason += " <em>However, minor observations include:</em> " + " ".join(issues)
            reason_tl += " <em>Gayunpaman, ang mga maliit na obserbasyon ay kinabibilangan ng:</em> " + " ".join(issues_tl)
        consumable = "Consumability: <strong>Likely Consumable</strong> for drinking. Always confirm with local standards."
        consumable_tl = "Pagiging Inumin: <strong>Malamang na Inumin</strong> para sa pag-inom. Laging kumpirmahin sa lokal na pamantayan."
        other_uses = "Other Uses: Excellent for general household use, cooking, and most plant watering."
        other_uses_tl = "Iba pang Gamit: Napakahusay para sa pangkalahatang gamit sa bahay, pagluluto, at pagdidilig ng karamihan sa mga halaman."
        suggestion = "Maintain regular monitoring. No immediate action required."
        suggestion_tl = "Panatilihin ang regular na pagsubaybay. Walang agarang aksyon na kailangan."
        title_text += "Good ✅"
        title_text_tl = "Maganda ✅"

    elif quality.lower() == 'average':
        reason = "The water quality is <strong>Average</strong>. While generally acceptable, some parameters are slightly outside optimal ranges."
        reason_tl = "Ang kalidad ng tubig ay <strong>Katamtaman</strong>. Bagama't karaniwang katanggap-tanggap, ang ilang parametro ay bahagyang wala sa optimal na saklaw."
        if issues:
            reason += " Specific concerns: " + " ".join(issues)
            reason_tl += " Mga partikular na alalahanin: " + " ".join(issues_tl)
        notes = "Notes: Potentially consumable for drinking, but monitor closely. Generally suitable for washing, cleaning, and many plants."
        notes_tl = "Mga Tala: Posibleng inumin, ngunit mahigpit na subaybayan. Karaniwang angkop para sa paghuhugas, paglilinis, at maraming halaman."
        consumable = "Consumability: <strong>Potentially Consumable</strong> for drinking, but monitor closely, especially if TDS is high or pH is imbalanced. May affect taste."
        consumable_tl = "Pagiging Inumin: <strong>Posibleng Inumin</strong> para sa pag-inom, ngunit mahigpit na subaybayan, lalo na kung mataas ang TDS o hindi balanse ang pH. Maaaring makaapekto sa lasa."
        other_uses = "Other Uses: Generally suitable for washing, cleaning, and many plants. Some sensitive plants might prefer more balanced water."
        other_uses_tl = "Iba pang Gamit: Karaniwang angkop para sa paghuhugas, paglilinis, at maraming halaman. Ang ilang sensitibong halaman ay maaaring mas gusto ang mas balanseng tubig."
        suggestion = "Consider checking your water source or basic filtration. If pH is off, check for mineral buildup or source contamination. If TDS is high, consider a simple filter."
        suggestion_tl = "Pag-isipan ang pag-check ng iyong pinagmulan ng tubig o basic na pagsala. Kung ang pH ay hindi tama, suriin para sa pagdami ng mineral o kontaminasyon ng pinagmulan. Kung mataas ang TDS, isaalang-alang ang isang simpleng filter."
        title_text += "Average ⚠️"
        title_text_tl = "Katamtaman ⚠️"

    elif quality.lower() == 'poor':
        reason = "The water quality is <strong>Poor</strong>. Critical parameters are significantly out of acceptable ranges, making it potentially unsafe or unsuitable for many uses."
        reason_tl = "Ang kalidad ng tubig ay <strong>Mahina</strong>. Ang mga kritikal na parametro ay malaki ang paglihis mula sa katanggap-tanggap na saklaw, na ginagawang posibleng hindi ligtas o hindi angkop para sa maraming gamit."
        if issues:
            reason += " Major issues: " + " ".join(issues)
            reason_tl += " Mga pangunahing isyu: " + " ".join(issues_tl)
        notes = "Notes: Not consumable for drinking or cooking. Limited use for general washing, and caution is advised even for hardy outdoor plants."
        notes_tl = "Mga Tala: Hindi inumin o angkop sa pagluluto. Limitado ang gamit para sa pangkalahatang paghuhugas, at pinapayuhan ang pag-iingat kahit para sa matitibay na halaman sa labas."
        consumable = "Consumability: <strong>NOT Consumable</strong> for drinking or cooking. Avoid ingestion."
        consumable_tl = "Pagiging Inumin: <strong>HINDI Inumin</strong> para sa pag-inom o pagluluto. Iwasan ang paglunok."
        other_uses = "Other Uses: <strong>Limited.</strong> May be unsuitable even for general washing. Could potentially be used for hardy outdoor plants if not excessively contaminated, but caution is advised. Avoid sensitive applications."
        other_uses_tl = "Iba pang Gamit: <strong>Limitado.</strong> Maaaring hindi angkop kahit para sa pangkalahatang paghuhugas. Posibleng magamit para sa matitibay na halaman sa labas kung hindi labis na kontaminado, ngunit pinapayuhan ang pag-iingat. Iwasan ang mga sensitibong aplikasyon."
        suggestion = "Immediate action is recommended. Investigate the source of contamination. Consider advanced filtration systems (e.g., reverse osmosis if TDS is very high) or sourcing water from elsewhere. Consult a water treatment specialist if issues persist."
        suggestion_tl = "Inirerekomenda ang agarang aksyon. Imbestigahan ang pinagmulan ng kontaminasyon. Pag-isipan ang mga advanced na sistema ng pagsala (hal. reverse osmosis kung napakataas ng TDS) o pagkuha ng tubig mula sa ibang lugar. Kumonsulta sa isang espesyalista sa paggamot ng tubig kung magpapatuloy ang mga isyu."
        title_text += "Poor ❌"
        title_text_tl = "Mahina ❌"

    elif quality.lower() == 'bad':
        reason = "The water quality is <strong>BAD</strong>. This indicates severe contamination or extreme conditions that make the water highly dangerous and unusable."
        reason_tl = "Ang kalidad ng tubig ay <strong>MASAMA</strong>. Nagpapahiwatig ito ng matinding kontaminasyon o matinding kondisyon na nagiging dahilan upang maging lubhang mapanganib at hindi magamit ang tubig."
        if issues:
            reason += " Critical problems: " + " ".join(issues)
            reason_tl += " Mga kritikal na problema: " + " ".join(issues_tl)
        else:
            reason += " Further investigation is urgently needed."
            reason_tl += " Agad na kailangan ang karagdagang imbestigasyon."

        notes = "Notes: Absolutely not consumable. Extremely limited use, may require professional hazardous material handling. Urgent action required."
        notes_tl = "Mga Tala: Ganap na hindi inumin. Lubhang limitado ang gamit, maaaring mangailangan ng propesyonal na paghawak ng mapanganib na materyal. Agarang aksyon ang kinakailangan."
        consumable = "Consumability: <strong>ABSOLUTELY NOT CONSUMABLE</strong>. DO NOT DRINK OR USE FOR COOKING. Direct contact should be minimized."
        consumable_tl = "Pagiging Inumin: <strong>GANAP NA HINDI INUMIN</strong>. HUWAG INUMIN O GAMITIN PARA SA PAGLULUTO. Ang direktang kontak ay dapat iwasan."
        other_uses = "Other Uses: <strong>EXTREMELY LIMITED.</strong> Unsuitable for any use that involves human or animal contact, or plant irrigation. May require professional hazardous material handling if contamination is severe."
        other_uses_tl = "Iba pang Gamit: <strong>LUBHANG LIMITADO.</strong> Hindi angkop para sa anumang gamit na kinasasangkutan ng kontak ng tao o hayop, o pagdidilig ng halaman. Maaaring mangailangan ng propesyonal na paghawak ng mapanganib na materyal kung matindi ang kontaminasyon."
        suggestion = "🛑 <strong>URGENT ACTION REQUIRED.</strong> Isolate the water source immediately. Do not use this water for any purpose. Contact water authorities or a professional water treatment service for immediate assessment and remediation. Ensure personal safety."
        suggestion_tl = "🛑 <strong>AGARANG AKSYON ANG KINAKAILANGAN.</strong> Agad na ihiwalay ang pinagmulan ng tubig. Huwag gamitin ang tubig na ito sa anumang layunin. Makipag-ugnayan sa mga awtoridad sa tubig o isang propesyonal na serbisyo sa paggamot ng tubig para sa agarang pagtatasa at remedyo. Siguraduhin ang personal na kaligtasan."
        title_text += "Bad ⛔"
        title_text_tl = "Masama ⛔"

    else: # Unknown quality
        reason = "Water quality status is currently <strong>Unknown</strong> or not determined by the system."
        reason_tl = "Ang status ng kalidad ng tubig ay kasalukuyang <strong>Hindi Alam</strong> o hindi natukoy ng sistema."
        notes = "Notes: Status unknown. Cannot determine without valid sensor data."
        notes_tl = "Mga Tala: Hindi alam ang status. Hindi matukoy nang walang balidong data ng sensor."
        consumable = "Consumability: <strong>Unknown.</strong> Cannot determine without valid sensor data."
        consumable_tl = "Pagiging Inumin: <strong>Hindi Alam.</strong> Hindi matukoy nang walang balidong data ng sensor."
        other_uses = "Other Uses: Unknown."
        other_uses_tl = "Iba pang Gamit: Hindi Alam."
        suggestion = "Ensure all sensors are connected and functioning. Check training data for the model and the backend server."
        suggestion_tl = "Siguraduhin na konektado at gumagana ang lahat ng sensor. Suriin ang data ng pagsasanay para sa modelo at ang backend server."
        title_text += "Unknown ❓"
        title_text_tl = "Hindi Alam ❓"

    return {
        "quality": quality,
        "reason": reason,
        "reason_tl": reason_tl,
        "consumableStatus": consumable,
        "consumableStatus_tl": consumable_tl,
        "otherUses": other_uses,
        "otherUses_tl": other_uses_tl,
        "suggestion": suggestion,
        "suggestion_tl": suggestion_tl,
        "notes": notes,
        "notes_tl": notes_tl,
        "title_text": title_text,
        "title_text_tl": title_text_tl
    }

# --- The train_decision_tree function (now trains RandomForest) remains the same ---
def train_decision_tree():
    """
    Trains a Random Forest Classifier using data from 'water_quality.db'
    and saves the trained model to 'water_quality_model.joblib'.
    """
    db_path = 'water_quality.db'
    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Training model...")

    try:
        with DB_LOCK:
            conn = sqlite3.connect(db_path)
            query = "SELECT timestamp, temperature, ph, tds, turbidity, water_quality FROM measurements"
            df = pd.read_sql_query(query, conn)
            conn.close()

        initial_rows = len(df)
        df = df.dropna(subset=['water_quality'])
        df = df[df['water_quality'].isin(['Good', 'Average', 'Poor'])]

        if df.empty:
            print("No valid labeled data ('Good', 'Average', 'Poor') found for training.")
            print("Model will not be updated. Please add labeled data to water_quality.db.")
            return
        
        for col in ['temperature', 'ph', 'tds']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df = df.dropna(subset=['temperature', 'ph', 'tds'])

        if df.empty:
            print("No valid numerical sensor data after cleaning. Model will not be updated.")
            return

        label_map_inverse = {'Good': 0, 'Average': 1, 'Poor': 2}
        df['water_quality_numeric'] = df['water_quality'].map(label_map_inverse)

        X = df[['temperature', 'ph', 'tds']]
        y = df['water_quality_numeric']

        if len(X) < 2:
            print("Not enough labeled data to split for training. Need at least 2 samples.")
            print("Model will not be updated. Please add more labeled data.")
            return

        test_size_val = 0.2 if len(X) > 5 else (1 if len(X) == 2 else 0.5)
        stratify_val = y if len(y.unique()) > 1 else None
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size_val, random_state=42, stratify=stratify_val)

        clf = RandomForestClassifier(random_state=42)
        clf.fit(X_train, y_train)

        y_pred = clf.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        print(f"Accuracy: {accuracy:.2f}")
        print("Classification Report:")
        try:
            print(classification_report(y_test, y_pred, target_names=['Good', 'Average', 'Poor'], zero_division=0))
        except ValueError as e:
            print(f"Could not generate full classification report: {e}")
            print("This might happen if only one class is present in the test set.")

        joblib.dump(clf, MODEL_FILE)
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Model trained and saved successfully to {MODEL_FILE}.")

        global model
        model = clf

    except sqlite3.OperationalError as e:
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Database locked during training: {e}. Skipping this training cycle.")
    except Exception as e:
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] An error occurred during model training: {e}")
        print("Please ensure your 'water_quality.db' has enough valid, labeled data.")