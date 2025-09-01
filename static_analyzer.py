# static_analyzer.py
"""
Provides detailed, static text analysis based on a given water quality classification.
This robust version is independent and does not re-evaluate thresholds, preventing errors.
"""

def get_detailed_water_analysis(temp, ph, tds, turb, predicted_quality):
    """
    Returns a dictionary of detailed textual analysis, suggestions, and icon names
    based on the provided water quality prediction. This function trusts the
    input 'predicted_quality' and does not perform its own checks.
    """
    # Start with a default dictionary for "Unknown" quality
    analysis = {
        "title_text": "Water Quality Analysis",
        "title_text_tl": "Pagsusuri sa Kalidad ng Tubig",
        "reason": "Water quality status is unknown due to insufficient or erroneous sensor data.",
        "reason_tl": "Hindi alam ang status ng kalidad ng tubig dahil sa kakulangan o maling data ng sensor.",
        "consumableStatus": "Unknown",
        "consumableStatus_tl": "Hindi Matukoy",
        "otherUses": "N/A",
        "otherUses_tl": "N/A",
        "suggestion": "Check sensor readings and system status.",
        "suggestion_tl": "Suriin ang mga pagbasa ng sensor at katayuan ng system.",
        "drinkable_icon": "unsafe",
        "other_uses_icons": ["no-contact"]
    }

    # Update the dictionary with specific text based on the predicted quality
    if predicted_quality == "Good":
        analysis.update({
            "title_text": "Good Water Quality", "title_text_tl": "Mahusay na Kalidad ng Tubig",
            "reason": "All parameters are within the optimal range, indicating the water is clean and safe.",
            "reason_tl": "Ang lahat ng parameter ay nasa loob ng pinakamainam na saklaw, na nagpapahiwatig na ang tubig ay malinis at ligtas.",
            "consumableStatus": "Potable (Safe for drinking)", "consumableStatus_tl": "Inumin (Ligtas para sa pag-inom)",
            "otherUses": "Suitable for all domestic purposes including cooking, bathing, and cleaning.",
            "otherUses_tl": "Angkop para sa lahat ng gawaing bahay kabilang ang pagluluto, paliligo, at paglilinis.",
            "suggestion": "No action needed. Continue regular monitoring.",
            "suggestion_tl": "Walang kailangang gawin. Ipagpatuloy ang regular na pag-monitor.",
            "drinkable_icon": "potable",
            "other_uses_icons": ["cooking", "bathing", "cleaning", "irrigation"]
        })
    elif predicted_quality == "Average":
        analysis.update({
            "title_text": "Average Water Quality", "title_text_tl": "Katamtamang Kalidad ng Tubig",
            "reason": "One or more parameters are slightly outside the optimal range but still within acceptable limits.",
            "reason_tl": "Isa o higit pang mga parameter ay bahagyang nasa labas ng pinakamainam na saklaw ngunit nasa loob pa rin ng mga katanggap-tanggap na limitasyon.",
            "consumableStatus": "Potable with caution (Boiling recommended)",
            "consumableStatus_tl": "Inumin nang may pag-iingat (Inirerekomenda ang pagpapakulo)",
            "otherUses": "Suitable for most domestic uses like bathing, cleaning, and irrigation.",
            "otherUses_tl": "Angkop para sa karamihan ng mga gawaing bahay tulad ng paliligo, paglilinis, at irigasyon.",
            "suggestion": "Monitor the system for any trends that might lead to poor quality.",
            "suggestion_tl": "Subaybayan ang system para sa anumang mga trend na maaaring humantong sa mahinang kalidad.",
            "drinkable_icon": "caution",
            "other_uses_icons": ["bathing", "cleaning", "irrigation", "flushing"]
        })
    elif predicted_quality == "Poor":
        analysis.update({
            "title_text": "Poor Water Quality", "title_text_tl": "Mahinang Kalidad ng Tubig",
            "reason": "Parameters have deviated significantly from the optimal range. This indicates potential contamination or issues.",
            "reason_tl": "Ang mga parameter ay malaki ang pagkakaiba sa pinakamainam na saklaw. Ito ay nagpapahiwatig ng posibleng kontaminasyon o mga isyu.",
            "consumableStatus": "Not recommended for consumption without filtration.",
            "consumableStatus_tl": "Hindi inirerekomenda para sa pagkonsumo nang walang pagsasala.",
            "otherUses": "Can be used for flushing or fire suppression. Avoid direct contact if possible.",
            "otherUses_tl": "Maaaring gamitin para sa pag-flush o pag-apula ng sunog. Iwasan ang direktang kontak kung maaari.",
            "suggestion": "Immediate investigation is required. Check for potential sources of pollution or sensor malfunction.",
            "suggestion_tl": "Kailangan ng agarang imbestigasyon. Suriin ang posibleng pinagmumulan ng polusyon o sira sa sensor.",
            "drinkable_icon": "not-recommended",
            "other_uses_icons": ["flushing", "fire-suppression", "industrial"]
        })
    elif predicted_quality == "Bad":
        analysis.update({
            "title_text": "Bad Water Quality", "title_text_tl": "Masamang Kalidad ng Tubig",
            "reason": "Parameters are at critical levels, indicating a high probability of contamination or severe issues.",
            "reason_tl": "Nasa kritikal na antas ang mga parameter, na nagpapahiwatig ng mataas na posibilidad ng kontaminasyon o malubhang isyu.",
            "consumableStatus": "Unsafe for consumption. Do not drink.",
            "consumableStatus_tl": "Hindi ligtas para sa pagkonsumo. Huwag inumin.",
            "otherUses": "Not recommended for any domestic use. Avoid all contact.",
            "otherUses_tl": "Hindi inirerekomenda para sa anumang gamit sa bahay. Iwasan ang lahat ng kontak.",
            "suggestion": "CRITICAL ALERT. Take immediate action to identify and resolve the source of contamination.",
            "suggestion_tl": "KRITIKAL NA ALERTO. Gumawa ng agarang aksyon upang matukoy at malutas ang pinagmulan ng kontaminasyon.",
            "drinkable_icon": "unsafe",
            "other_uses_icons": ["no-contact"]
        })

    return analysis