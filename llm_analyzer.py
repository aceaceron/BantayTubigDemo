# llm_analyzer.py
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
    llm_model = genai.GenerativeModel('gemini-2.5-flash') # Updated to a newer model for better JSON compliance
    LLM_ENABLED = True
    print("Gemini LLM for analyzing configured successfully.")
except (ValueError, Exception) as e:
    print(f"Warning: Gemini LLM not configured. Detailed explanations will be static. Error: {e}")
    LLM_ENABLED = False
    llm_model = None

# MODIFIED: This function is now safer and handles non-string inputs.
def to_markdown(text):
    """
    Formats text for display, safely handling any non-string inputs from the LLM.
    """
    # 1. Check if the input 'text' is a string.
    if not isinstance(text, str):
        # 2. If it's not (e.g., it's a dictionary), convert it to its string representation.
        text = str(text)
    
    # 3. Now that we're sure it's a string, we can safely use .replace().
    return text.replace('**', '<strong>', 1).replace('**', '</strong>', 1)


def generate_llm_analysis(temp, pH, TDS, turb, water_quality_prediction, env_context=None):
    """
    Calls the LLM to get a detailed reasoning, Tagalog translation,
    suggestions, and other uses for water quality, in JSON format.
    """
    if not LLM_ENABLED or llm_model is None:
        return {
            "reasoning": "LLM is not configured or failed to initialize.",
            "tagalog_translation": "Ang LLM ay hindi naka-configure o nabigo sa pag-initialize.",
            "suggestions": "Please ensure GEMINI_API_KEY is set and valid.",
            "suggestions_tl": "Mangyaring tiyakin na ang GEMINI_API_KEY ay nakatakda at balido.",
            "other_uses": "N/A",
            "other_uses_tl": "N/A"
        }

    # Handle potential None or "Error" values gracefully for the prompt
    temp_str = f"{temp}°C" if temp is not None and temp != 'Error' else "not available"
    ph_str = f"{pH}" if pH is not None else "not available"
    tds_str = f"{TDS} ppm" if TDS is not None else "not available"
    turb_str = f"{turb}" if turb is not None else "not available"

    prompt_text = textwrap.dedent(f"""
    Analyze the following water quality parameters and provide a concise, detailed explanation for why the water quality is classified as '{water_quality_prediction}'.
    Then, provide specific suggestions for improvement or maintenance based on these parameters.
    Additionally, list possible other uses for water with these characteristics.
    Finally, provide a TagLish translation for the reasoning, suggestions, and other uses.

    For any bold text, use HTML <strong> tags instead of markdown asterisks (e.g., <strong>this</strong>).

    The output MUST be in JSON format.
    Use the following exact keys: "reasoning", "tagalog_translation", "suggestions", "suggestions_tl", "other_uses", "other_uses_tl".
    The values for each key should be strings (plain text or HTML).

    Water Quality Parameters:
    Temperature (Temp): {temp_str}
    pH: {ph_str}
    Total Dissolved Solids (TDS): {tds_str}
    Turbidity (Turb): {turb_str}
    Predicted Water Quality: {water_quality_prediction}
    """)

    # Dynamically add environmental context to the prompt if it exists
    if env_context:
        prompt_text += "\n\nConsider the following recent environmental conditions in your analysis:\n"
        if env_context.get('air_temp_c') is not None:
            prompt_text += f"- Air Temperature: {env_context['air_temp_c']:.1f}°C\n"
        if env_context.get('rainfall_mm') is not None and env_context['rainfall_mm'] > 0:
            prompt_text += f"- Recent Rainfall: {env_context['rainfall_mm']:.1f} mm\n"
        if env_context.get('days_since_calibration') is not None:
            prompt_text += f"- Days Since Last Sensor Calibration: {env_context['days_since_calibration']}\n"

    try:
        response = llm_model.generate_content(prompt_text)
        llm_output_text = response.text
    
        # Robustly parse the JSON output
        if llm_output_text.strip().startswith('```json'):
            json_str = llm_output_text.strip()[7:-3].strip()
        else:
            json_str = llm_output_text.strip()

        parsed_output = json.loads(json_str)

        # Apply to_markdown, which can now safely handle unexpected data types
        return {
            "reasoning": to_markdown(parsed_output.get("reasoning", "N/A")),
            "tagalog_translation": to_markdown(parsed_output.get("tagalog_translation", "N/A")),
            "suggestions": to_markdown(parsed_output.get("suggestions", "N/A")),
            "suggestions_tl": to_markdown(parsed_output.get("suggestions_tl", "N/A")),
            "other_uses": to_markdown(parsed_output.get("other_uses", "N/A")),
            "other_uses_tl": to_markdown(parsed_output.get("other_uses_tl", "N/A"))
        }
    except json.JSONDecodeError as jde:
        # ... (error handling remains the same)
        return { "reasoning": f"Error: LLM output was not valid JSON. {jde}" }
    except Exception as e:
        # ... (error handling remains the same)
        return { "reasoning": f"Error generating LLM analysis: {e}" }