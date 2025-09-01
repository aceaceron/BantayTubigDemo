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
    llm_model = genai.GenerativeModel('gemini-2.5-flash')
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
    Analyze the following water quality data, classified as '{water_quality_prediction}'.
    Provide: 1. A concise reasoning for the classification. 2. Specific suggestions. 3. Possible other uses.
    The output MUST be in JSON format with keys: "reasoning", "suggestions", "other_uses".
    The values must be in TagLish, followed by an italicized English translation in a new paragraph.
    Use HTML tags like <b> and <i>.

    Data: Temp: {temp}°C, pH: {pH}, TDS: {TDS} ppm, Turbidity: {turb} NTU.
    """)
    
    if env_context:
        prompt_text += f"\nEnvironmental Context: Air Temp: {env_context.get('air_temp_c')}°C, Rainfall: {env_context.get('rainfall_mm')} mm."

    try:
        response = llm_model.generate_content(prompt_text)
        json_str = response.text.strip().replace('```json', '').replace('```', '').strip()
        return json.loads(json_str)
    except Exception as e:
        return { "reasoning": f"Error generating AI analysis: {e}" }

# --- FEATURE 2: HISTORICAL REASONING (from llm_reasoning.py) ---
def generate_historical_reasoning(primary_range, primary_summary, device_location="Jose Panganiban", device_water_source="River"):
    """
    Generates a contextual analysis of summarized historical water quality data.
    """
    if not LLM_ENABLED:
        return "<p>AI analysis is currently unavailable.</p>"

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
        return response.text
    except Exception as e:
        return f"<p>Error: {e}</p>"