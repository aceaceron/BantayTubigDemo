# ml_models/llm_insights.py
import os
import google.generativeai as genai
import json
import textwrap

# --- LLM Configuration ---
LLM_ENABLED = False
llm_model = None

try:
    # The API key is now hardcoded directly into the script as requested.
    GEMINI_API_KEY = "AIzaSyBv1HoaIzz4LUTL6Gxey5r37kmE8fdSyBE"
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY environment variable not set.")
    genai.configure(api_key=GEMINI_API_KEY)
    llm_model = genai.GenerativeModel('gemini-1.5-flash')
    LLM_ENABLED = True
    print("Gemini LLM for insights configured successfully.")
except Exception as e:
    print(f"Warning: Gemini LLM for insights not configured. Error: {e}")
    LLM_ENABLED = False

# --- FEATURE 1: CURRENT STATUS ANALYSIS (from llm_analyzer.py) ---
def generate_current_status_analysis(temp, pH, TDS, turb, water_quality_prediction, env_context=None):
    """
    Calls the LLM to get a detailed reasoning, suggestions, and other uses
    for the latest water quality readings.
    """
    if not LLM_ENABLED:
        return { "reasoning": "AI analysis is currently unavailable." }

    prompt_text = textwrap.dedent(f"""
    You are an AI assistant for BantayTubig, a water quality monitoring system in Jose Panganiban, Philippines.
    Analyze the following real-time water quality data, which has been classified as '{water_quality_prediction}'.
    
    Your response MUST be a valid JSON object with three keys: "reasoning", "suggestions", and "other_uses".
    
    For EACH of the three key's values, you must follow these rules precisely:
    
    1.  **First, write the complete analysis in a single, conversational Taglish paragraph.**
    2.  **Do NOT alternate between Taglish and English within this first part.** It must be a complete thought in Taglish.
    3.  **After the complete Taglish paragraph, add an HTML line break: `<br>`**
    4.  **Finally, write the complete English translation of the entire paragraph, enclosed in `<i>` tags.**
    
    **Correct Example for a value:**
    "Ang kalidad ng tubig ay <b>'Good'</b> dahil ang lahat ng sukat ay pasok sa mga ligtas na pamantayan.<br><i>The water quality is <b>'Good'</b> because all measurements are within safe standards.</i>"
    
    **Incorrect Example (DO NOT DO THIS):**
    "<b>Ang</b> <i>The</i> kalidad ng tubig ay <i>water quality is</i> <b>'Good'</b>..."
    
    CURRENT DATA:
    - Temperature: {temp}°C
    - pH: {pH}
    - TDS: {TDS} ppm
    - Turbidity: {turb} NTU
    """)
    
    if env_context:
        prompt_text += f"\nEnvironmental Context: Air Temp: {env_context.get('air_temp_c')}°C, Rainfall: {env_context.get('rainfall_mm')} mm."

    try:
        response = llm_model.generate_content(prompt_text)
        # Clean the response to remove markdown fences, just in case.
        json_str = response.text.strip().replace('```json', '').replace('```', '').strip()
        return json.loads(json_str)
    except Exception as e:
        return { "reasoning": f"Error generating AI analysis: {e}" }

# --- FEATURE 2: HISTORICAL REASONING ---
def generate_historical_reasoning(primary_range, primary_summary, device_info):
    """
    Generates a contextual analysis of summarized historical water quality data.
    """
    if not LLM_ENABLED:
        return "<p>AI analysis is currently unavailable.</p>"

    device_location = device_info.get('location', 'Unknown Location')
    device_water_source = device_info.get('water_source', 'Unknown Source')

    prompt = f"""
        Bilang isang data analyst para sa BantayTubig, ipaliwanag ang data para sa lokasyon sa <b>{device_location}</b> mula sa isang <b>{device_water_source}</b>.

        Pangunahing Saklaw ng Petsa: <b>{primary_range}</b>
        - Average na Sensor Temp: <b>{primary_summary.get('avg_temp', 'N/A')}°C</b>
        - Average na pH: <b>{primary_summary.get('avg_ph', 'N/A')}</b>
        - Average na TDS: <b>{primary_summary.get('avg_tds', 'N/A')} ppm</b>
        - Average na Turbidity: <b>{primary_summary.get('avg_turb', 'N/A')} NTU</b>
        - Pinakamadalas na Kalidad: <b>{primary_summary.get('most_common_quality', 'N/A')}</b>

        I-format ang sagot gamit ang HTML paragraphs <p>.
        Magbigay ka ng pagsusuri sa TagLish, na sinusundan ng italicized na pagsasalin sa Ingles sa hiwalay na paragraph.
    """

    try:
        response = llm_model.generate_content(textwrap.dedent(prompt))
        
        # Clean the AI's response to remove any markdown code fences.
        cleaned_text = response.text.strip().replace("```html", "").replace("```", "")
        return cleaned_text.strip()
        
    except Exception as e:
        return f"<p>Error: {e}</p>"
