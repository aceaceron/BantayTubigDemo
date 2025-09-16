import os
import google.generativeai as genai
import textwrap

# --- Configuration ---
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
    print("Gemini LLM for reasoning configured successfully.")
except Exception as e:
    print(f"Warning: Gemini LLM for reasoning not configured. Error: {e}")
    LLM_ENABLED = False


def generate_reasoning_for_range(primary_range, primary_summary, device_location, device_water_source, 
                                 primary_context_summary, 
                                 comparison_range=None, comparison_summary=None, 
                                 comparison_context_summary=None):
    """
    Generates a contextual analysis of summarized water quality data,
    including summarized environmental data.
    """
    if not LLM_ENABLED:
        return "<p>AI analysis is currently unavailable.</p>"

    prompt = f"""
        Bilang isang data analyst para sa BantayTubig, ipaliwanag mo sa akin ang mga summarized na data.
        
        Isaalang-alang mo ang mga sumusunod:
        - Lokasyon: <b>{device_location}</b>
        - Pinagmumulan ng Tubig: <b>{device_water_source}</b>
        - Panahon (Weather): I-search mo ang posibleng panahon sa lokasyon base sa mga petsa.
    """
    
    if primary_context_summary:
        prompt += "\nKondisyon ng Kapaligiran (Average):\n"
        if primary_context_summary.get('avg_rainfall') is not None:
            prompt += f"- Ulan: <b>{primary_context_summary['avg_rainfall']:.2f} mm</b>\n"
        if primary_context_summary.get('avg_air_temp') is not None:
            prompt += f"- Temperatura ng Hangin: <b>{primary_context_summary['avg_air_temp']:.1f}°C</b>\n"

    prompt += f"""
        Pangunahing Saklaw ng Petsa: <b>{primary_range}</b>
        - Average na Sensor Temp: <b>{primary_summary.get('avg_temp', 'N/A')}°C</b>
        - Average na pH: <b>{primary_summary.get('avg_ph', 'N/A')}</b>
        - Average na TDS: <b>{primary_summary.get('avg_tds', 'N/A')} ppm</b>
        - Average na Turbidity: <b>{primary_summary.get('avg_turb', 'N/A')} NTU</b>
        - Pinakamadalas na Kalidad: <b>{primary_summary.get('most_common_quality', 'N/A')}</b>
    """

    if comparison_range and comparison_summary:
        prompt += f"\nIkumpara mo ito sa:\n"
        if comparison_context_summary:
            prompt += "\nKondisyon ng Kapaligiran (Average):\n"
            if comparison_context_summary.get('avg_rainfall') is not None:
                prompt += f"- Ulan: <b>{comparison_context_summary['avg_rainfall']:.2f} mm</b>\n"
            if comparison_context_summary.get('avg_air_temp') is not None:
                prompt += f"- Temperatura ng Hangin: <b>{comparison_context_summary['avg_air_temp']:.1f}°C</b>\n"
        
        prompt += f"""
            Saklaw ng Petsa para sa Paghahambing: <b>{comparison_range}</b>
            - Average na Sensor Temp: <b>{comparison_summary.get('avg_temp', 'N/A')}°C</b>
            - Average na pH: <b>{comparison_summary.get('avg_ph', 'N/A')}</b>
            - Average na TDS: <b>{comparison_summary.get('avg_tds', 'N/A')} ppm</b>
            - Average na Turbidity: <b>{comparison_summary.get('avg_turb', 'N/A')} NTU</b>
            - Pinakamadalas na Kalidad: <b>{comparison_summary.get('most_common_quality', 'N/A')}</b>
            
            Ipaliwanag mo ang posibleng dahilan ng pagkakaiba o pagkakatulad.
        """

    prompt += """
        \nMahalagang Paalala:
        - Maging direkta at madaling maintindihan ang iyong paliwanag.
        - Gamitin ang HTML tags na <b> para sa pag-bold ng text.
        - I-format ang sagot gamit ang HTML paragraphs <p>.
        - Magbigay ka ng pagsusuri sa TagLish, na sinusundan ng italicized na pagsasalin sa Ingles sa hiwalay na paragraph.
    """

    try:
        response = llm_model.generate_content(textwrap.dedent(prompt))
        
        # Safely handle the response from the LLM to prevent errors.
        llm_output = response.text
        
        # 1. Check if the output from the AI is a string.
        if not isinstance(llm_output, str):
            # 2. If it's not (e.g., it's a dictionary), convert it to its string representation.
            llm_output = str(llm_output)
            
        # 3. Now that we're sure it's a string, we can safely perform replacements.
        return llm_output.replace('**', '<b>').replace('**', '</b>')
        
    except Exception as e:
        print(f"Error calling LLM for reasoning: {e}")
        return f"<p>Nagkaroon ng error sa pag-generate ng pagsusuri.</p><p><em>An error occurred while generating the reasoning.</em></p><p><em>Error: {e}</em></p>"