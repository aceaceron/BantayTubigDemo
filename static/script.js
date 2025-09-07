/**
 * @file script.js
 * @description This script handles the dynamic functionality of the BantayTubig dashboard,
 * including fetching data, updating charts and gauges, handling user interactions for AI analysis,
 * and managing the sidebar navigation.
 */

// --- GLOBAL VARIABLES & CONFIGURATION ---

// Maximum number of data points to display on the charts at any given time.
const maxDataPoints = 20;

// Arrays to store the data for the charts.
const labels = [];
const tempData = [];
const phData = [];
const tdsData = [];
const turbData = [];

// Global instances for the Chart.js charts.
let tempChart, phChart, tdsChart, turbChart;

// Configuration object for the gauges. This will be populated with data fetched from the server.
let gaugeConfigs = {};

// Interval ID for periodically updating the dashboard.
let dashboardInterval = null;

// --- INITIALIZATION ---


/**
 * Initializes the dashboard when the DOM is fully loaded.
 * Fetches threshold data from the server, sets up gauge configurations,
 * creates the gauges and charts, and starts the periodic data update.
 */
async function init() {
    try {
        const response = await fetch('/analytics/thresholds');
        if (!response.ok) {
            throw new Error('Failed to fetch threshold data.');
        }
        const thresholds = await response.json();

        // Populate the gaugeConfigs object with the fetched threshold data.
        setupGaugeConfigs(thresholds);

        // Create the gauge and chart elements on the page.
        createGauges();
        initializeCharts();

        // Perform the initial data fetch and update.
        updateDashboard();

        // Set up an interval to automatically update the dashboard every 2 seconds.
        dashboardInterval = setInterval(updateDashboard, 2000);

    } catch (error) {
        console.error('Initialization error:', error);
        // In a real application, you might want to display an error message to the user.
    }
    setupGlobalNavigation();
}

// Add an event listener to call the init function once the DOM is ready.
document.addEventListener('DOMContentLoaded', init);

// --- GAUGE CONFIGURATION & CREATION ---

/**
 * Populates the global `gaugeConfigs` object with settings for each gauge
 * based on the threshold values fetched from the server.
 * @param {object} thresholds - An object containing the min/max threshold values for each parameter.
 */
function setupGaugeConfigs(thresholds) {
    gaugeConfigs = {
        temp: {
            id: 'gauge-temp',
            min: thresholds.TEMP_AVERAGE_MIN,
            max: thresholds.TEMP_AVERAGE_MAX + 5,
            unit: '',
            thresholds: [
                { value: thresholds.TEMP_AVERAGE_MIN, colorClass: 'bad' },
                { value: thresholds.TEMP_GOOD_MIN, colorClass: 'average' },
                { value: thresholds.TEMP_GOOD_MAX, colorClass: 'good' },
                { value: thresholds.TEMP_AVERAGE_MAX, colorClass: 'average' },
                { value: thresholds.TEMP_AVERAGE_MAX + 5, colorClass: 'bad' }
            ]
        },
        ph: {
            id: 'gauge-ph',
            min: 0,
            max: 14,
            unit: '',
            thresholds: [
                { value: thresholds.PH_POOR_MIN, colorClass: 'bad' },
                { value: thresholds.PH_AVERAGE_MIN, colorClass: 'poor' },
                { value: thresholds.PH_GOOD_MIN, colorClass: 'average' },
                { value: thresholds.PH_GOOD_MAX, colorClass: 'good' },
                { value: thresholds.PH_AVERAGE_MAX, colorClass: 'average' },
                { value: thresholds.PH_POOR_MAX, colorClass: 'poor' },
                { value: 14.0, colorClass: 'bad' }
            ]
        },
        tds: {
            id: 'gauge-tds',
            min: 0,
            max: thresholds.TDS_POOR_MAX + 200,
            unit: '',
            thresholds: [
                { value: thresholds.TDS_GOOD_MAX, colorClass: 'good' },
                { value: thresholds.TDS_AVERAGE_MAX, colorClass: 'average' },
                { value: thresholds.TDS_POOR_MAX, colorClass: 'poor' },
                { value: thresholds.TDS_POOR_MAX + 200, colorClass: 'bad' }
            ]
        },
        turb: {
            id: 'gauge-turb',
            min: 0,
            max: thresholds.TURB_BAD_THRESHOLD,
            unit: '',
            thresholds: [
                { value: thresholds.TURB_GOOD_MAX, colorClass: 'good' },
                { value: thresholds.TURB_AVERAGE_MAX, colorClass: 'average' },
                { value: thresholds.TURB_POOR_MAX, colorClass: 'poor' },
                { value: thresholds.TURB_BAD_THRESHOLD, colorClass: 'bad' }
            ]
        }
    };
}

/**
 * Creates all the SVG gauges defined in the `gaugeConfigs` object.
 */
function createGauges() {
    for (const key in gaugeConfigs) {
        const config = gaugeConfigs[key];
        createGauge(config.id, config.min, config.max, config.unit);
    }
}

/**
 * Creates a single SVG half-ring gauge and appends it to the specified parent element.
 * @param {string} parentId - The ID of the div element to append the gauge to.
 * @param {number} minVal - The minimum value of the gauge.
 * @param {number} maxVal - The maximum value of the gauge.
 * @param {string} unit - The unit to display (e.g., '°C', 'ppm').
 */
function createGauge(parentId, minVal, maxVal, unit) {
    const parent = document.getElementById(parentId);
    if (!parent) {
        console.error(`Parent element with ID '${parentId}' not found for gauge.`);
        return;
    }

    const radius = 70;
    const strokeWidth = 15;
    const circumference = Math.PI * radius;
    const viewBoxSize = radius * 2 + strokeWidth;

    // Create the main SVG element.
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("viewBox", `0 0 ${viewBoxSize} ${viewBoxSize / 2 + strokeWidth / 2}`);
    svg.setAttribute("class", "gauge-svg");

    // Create the background arc of the gauge.
    const backgroundArc = document.createElementNS("http://www.w3.org/2000/svg", "path");
    backgroundArc.setAttribute("class", "gauge-arc-bg");
    backgroundArc.setAttribute("d", `M ${strokeWidth / 2},${radius + strokeWidth / 2} A ${radius},${radius} 0 0 1 ${radius * 2 + strokeWidth / 2},${radius + strokeWidth / 2}`);
    svg.appendChild(backgroundArc);

    // Create the progress arc that will show the current value.
    const progressArc = document.createElementNS("http://www.w3.org/2000/svg", "path");
    progressArc.setAttribute("class", "gauge-arc-progress");
    progressArc.setAttribute("d", `M ${strokeWidth / 2},${radius + strokeWidth / 2} A ${radius},${radius} 0 0 1 ${radius * 2 + strokeWidth / 2},${radius + strokeWidth / 2}`);
    progressArc.style.strokeDasharray = `0 ${circumference}`; // Initialize with 0 progress.
    svg.appendChild(progressArc);

    // Create the text element to display the value inside the gauge.
    const valueText = document.createElementNS("http://www.w3.org/2000/svg", "text");
    valueText.setAttribute("class", "gauge-value");
    valueText.setAttribute("x", viewBoxSize / 2);
    valueText.setAttribute("y", radius + strokeWidth / 2 - 10);
    valueText.textContent = `-- ${unit}`; // Initial display.
    svg.appendChild(valueText);

    parent.appendChild(svg);
}

// --- CHART INITIALIZATION & UPDATES ---

/**
 * Initializes all the Chart.js line charts on the dashboard.
 */
function initializeCharts() {
    const commonChartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            x: {
                type: 'time',
                time: {
                    unit: 'minute',
                    displayFormats: { minute: 'HH:mm' }
                },
                title: { display: true, text: 'Time' }
            },
            y: {
                beginAtZero: false,
                title: { display: true, text: 'Value' }
            }
        },
        plugins: {
            legend: { display: false }
        }
    };

    // Initialize Temperature Chart
    const tempCanvas = document.getElementById('tempChart');
    if (tempCanvas) {
        tempChart = new Chart(tempCanvas, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Temperature (°C)',
                    data: tempData,
                    borderColor: 'rgb(255, 99, 132)',
                    tension: 0.1,
                    fill: false
                }]
            },
            options: { ...commonChartOptions, scales: { y: { title: { display: true, text: 'Temperature (°C)' } } } }
        });
    }

    // Initialize pH Chart
    const phCanvas = document.getElementById('phChart');
    if (phCanvas) {
        phChart = new Chart(phCanvas, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'pH',
                    data: phData,
                    borderColor: 'rgb(54, 162, 235)',
                    tension: 0.1,
                    fill: false
                }]
            },
            options: { ...commonChartOptions, scales: { y: { min: 0, max: 14, title: { display: true, text: 'pH Value' } } } }
        });
    }

    // Initialize TDS Chart
    const tdsCanvas = document.getElementById('tdsChart');
    if (tdsCanvas) {
        tdsChart = new Chart(tdsCanvas, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'TDS (ppm)',
                    data: tdsData,
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1,
                    fill: false
                }]
            },
            options: { ...commonChartOptions, scales: { y: { title: { display: true, text: 'TDS (ppm)' } } } }
        });
    }

    // Initialize Turbidity Chart
    const turbCanvas = document.getElementById('turbChart');
    if (turbCanvas) {
        turbChart = new Chart(turbCanvas, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Turbidity (NTU)',
                    data: turbData,
                    borderColor: 'rgb(255, 159, 64)',
                    tension: 0.1,
                    fill: false
                }]
            },
            options: { ...commonChartOptions, scales: { y: { min: 0, max: gaugeConfigs.turb.max, title: { display: true, text: 'Turbidity (NTU)' } } } }
        });
    }
}

/**
 * Updates the charts with new data points.
 * @param {object} data - The latest sensor data from the server.
 */
function updateCharts(data) {
    const timestamp = new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });

    // Add new data to the chart arrays.
    labels.push(timestamp);
    tempData.push(data.temperature === 'Error' ? null : parseFloat(data.temperature));
    phData.push(parseFloat(data.ph));
    tdsData.push(parseFloat(data.tds));
    turbData.push(parseFloat(data.turbidity));

    // Remove the oldest data point if the maximum number of points is exceeded.
    if (labels.length > maxDataPoints) {
        labels.shift();
        tempData.shift();
        phData.shift();
        tdsData.shift();
        turbData.shift();
    }

    // Update all charts to reflect the new data.
    if (tempChart) tempChart.update();
    if (phChart) phChart.update();
    if (tdsChart) tdsChart.update();
    if (turbChart) turbChart.update();
}

// --- DASHBOARD DATA FETCHING & UI UPDATES ---

/**
 * Fetches the latest data from the server and updates all dashboard components.
 */
function updateDashboard() {
    fetch('/analytics/latest')
        .then(response => response.json())
        .then(data => {
            // Update the timestamp display.
            updateTimestamp(data.timestamp);

            // Update all the gauges with the new values.
            if (Object.keys(gaugeConfigs).length > 0) {
                updateGauge(gaugeConfigs.temp.id, data.temperature, gaugeConfigs.temp.min, gaugeConfigs.temp.max, gaugeConfigs.temp.unit, gaugeConfigs.temp.thresholds);
                updateGauge(gaugeConfigs.ph.id, data.ph, gaugeConfigs.ph.min, gaugeConfigs.ph.max, gaugeConfigs.ph.unit, gaugeConfigs.ph.thresholds);
                updateGauge(gaugeConfigs.tds.id, data.tds, gaugeConfigs.tds.min, gaugeConfigs.tds.max, gaugeConfigs.tds.unit, gaugeConfigs.tds.thresholds);
                updateGauge(gaugeConfigs.turb.id, data.turbidity, gaugeConfigs.turb.min, gaugeConfigs.turb.max, gaugeConfigs.turb.unit, gaugeConfigs.turb.thresholds);
            }

            // Update the water quality status and explanation text.
            updateWaterQualityInfo(data);

            // Update the charts with the new data.
            updateCharts(data);
        })
        .catch(error => console.error('Error fetching latest data:', error));
}

/**
 * Updates a single SVG gauge with a new value and color.
 * @param {string} gaugeId - The ID of the gauge container.
 * @param {number|string} value - The current value to display.
 * @param {number} minVal - The minimum value of the gauge scale.
 * @param {number} maxVal - The maximum value of the gauge scale.
 * @param {string} unit - The unit to display.
 * @param {Array<object>} thresholds - An array of threshold objects ({ value, colorClass }).
 */
function updateGauge(gaugeId, value, minVal, maxVal, unit, thresholds) {
    const gaugeElement = document.getElementById(gaugeId);
    if (!gaugeElement) return;

    const progressArc = gaugeElement.querySelector('.gauge-arc-progress');
    const valueTextInsideGauge = gaugeElement.querySelector('.gauge-value');
    if (!progressArc || !valueTextInsideGauge) return;

    let displayValue = parseFloat(value);
    if (isNaN(displayValue)) {
        valueTextInsideGauge.textContent = `-- ${unit}`;
        progressArc.style.strokeDasharray = `0 ${Math.PI * 70}`;
        progressArc.className.baseVal = 'gauge-arc-progress'; // Reset color
        return;
    }

    // Calculate the progress and update the arc.
    const clampedValue = Math.max(minVal, Math.min(maxVal, displayValue));
    const progress = (clampedValue - minVal) / (maxVal - minVal);
    const radius = 70;
    const circumference = Math.PI * radius;
    const dashLength = progress * circumference;
    progressArc.style.strokeDasharray = `${dashLength} ${circumference - dashLength}`;

    // Format and update the value text.
    let formattedValue = (gaugeId === 'gauge-ph' || gaugeId === 'gauge-turb') ? displayValue.toFixed(2) :
                         (gaugeId === 'gauge-tds') ? displayValue.toFixed(0) : displayValue.toFixed(1);
    valueTextInsideGauge.textContent = `${formattedValue} ${unit}`;

    // Determine and apply the color class based on thresholds.
    let colorClass = 'bad';
    if (thresholds && thresholds.length > 0) {
        thresholds.sort((a, b) => a.value - b.value);
        for (let i = 0; i < thresholds.length; i++) {
            if (clampedValue <= thresholds[i].value) {
                colorClass = thresholds[i].colorClass;
                break;
            }
            if (i === thresholds.length - 1 && clampedValue > thresholds[i].value) {
                colorClass = thresholds[i].colorClass;
            }
        }
    }
    progressArc.className.baseVal = `gauge-arc-progress ${colorClass}`;
}

/**
 * Updates the ML prediction details, but only if the user has enabled it in the settings.
 * @param {object} data - The full data object from the server.
 */
function updatePredictionDetails(data) {
    const shouldShowConfidence = localStorage.getItem('showMlConfidence') !== 'false';

    // Get all relevant UI elements
    const qualityText = document.getElementById('water_quality');
    const mlContainer = document.getElementById('mlConfidenceContainer');
    const modeText = document.getElementById('decisionMode');
    
    // Get the parent card element that will have the animated border
    const cardElement = qualityText.closest('.card');

    // --- 1. Initial Data Validation ---
    if (!data || data.quality === 'Unknown' || data.confidence === undefined) {
        qualityText.textContent = data.quality || 'Unknown';
        qualityText.className = 'value';
        if (mlContainer) mlContainer.style.display = 'none';
        if (modeText) modeText.style.display = 'none';
        // Remove animation classes if data is invalid
        if (cardElement) cardElement.className = 'card'; 
        return;
    }

    // --- 2. Update the main quality text and color ---
    const qualityClass = data.quality.toLowerCase();
    qualityText.textContent = data.quality;
    qualityText.className = `value water-quality-${qualityClass}`;
    
    // --- 3. Logic to show either the ML Confidence Bar or the Rule-Based Mode Text ---

    if (typeof data.confidence === 'number' && shouldShowConfidence) {
        // --- A. ML Model is used ---
        if (modeText) modeText.style.display = 'none';
        if (mlContainer) mlContainer.style.display = 'block';

        // Add the glowing border animation class
        if (cardElement) {
            // We only need to add the main class now
            cardElement.classList.add('ml-active-border');
        }
        
        // Update the confidence bar details
        const percentageText = document.getElementById('confidencePercentage');
        const progressBar = document.getElementById('confidenceProgressBar');
        const breakdownContainer = document.getElementById('predictionBreakdown');
        const confidencePercent = (data.confidence * 100).toFixed(0);
        
        percentageText.textContent = `${confidencePercent}%`;
        progressBar.style.width = `${confidencePercent}%`;
        progressBar.className = `progress-bar-fill ${qualityClass}`;

        let breakdownHTML = 'Prediction Breakdown: ';
        const probabilities = data.probabilities || {};
        const sortedProbs = Object.entries(probabilities).sort((a, b) => b[1] - a[1]);
        
        breakdownHTML += sortedProbs.map(([name, prob]) => 
            `${name}: <strong>${(prob * 100).toFixed(0)}%</strong>`
        ).join(', ');
        breakdownContainer.innerHTML = breakdownHTML;

    } else {
        // --- B. Rule-Based decision is used (or ML view is off) ---
        if (mlContainer) mlContainer.style.display = 'none'; 
        
        // Remove the glowing border animation class
        if (cardElement) {
            cardElement.classList.remove('ml-active-border');
        }

        if (typeof data.confidence === 'string') {
            if (modeText) {
                modeText.textContent = `Mode: ${data.confidence}`;
                modeText.style.display = 'block';
            }
        } else {
            if (modeText) modeText.style.display = 'none';
        }
    }
}
/**
 * The main function that receives data from the server and updates all
 * quality-related sections of the dashboard.
 * @param {object} data - The full, flat data object from the /analytics/latest API endpoint.
 */
function updateWaterQualityInfo(data) {

    // 1. Update the ML prediction display (which reads the localStorage setting).
    updatePredictionDetails(data);

    // 2. Update the static analysis text.
    document.getElementById('qualityExplanationTitle').textContent = data.title_text || "Water Quality Details";
    document.getElementById('qualityReason').innerHTML = data.reason || "Loading details...";
    document.getElementById('consumableStatus').textContent = `Consumable Status: ${data.consumableStatus || 'N/A'}`;
    document.getElementById('otherUses').textContent = `Other Uses: ${data.otherUses || 'N/A'}`;
    document.getElementById('qualitySuggestion').textContent = `Suggestion: ${data.suggestion || 'N/A'}`;

    // Update Tagalog translations.
    document.getElementById('qualityExplanationTitleTL').textContent = data.title_text_tl || "Mga Detalye ng Kalidad ng Tubig";
    document.getElementById('qualityReasonTL').innerHTML = data.reason_tl || "Loading Tagalog details...";
    document.getElementById('consumableStatusTL').textContent = `Katayuan ng Pagkain: ${data.consumableStatus_tl || 'Hindi Matukoy'}`;
    document.getElementById('otherUsesTL').textContent = `Iba Pang Gamit: ${data.otherUses_tl || 'Hindi Matukoy'}`;
    document.getElementById('qualitySuggestionTL').textContent = `Mungkahi: ${data.suggestion_tl || 'Hindi Matutukoy'}`;
    
    // 3. Update the static analysis icons.
    updateAnalysisIcons(data);
}
/**
 * Updates the timestamp display on the dashboard.
 * @param {string} timestampISO - The ISO 8601 timestamp string from the server.
 */
function updateTimestamp(timestampISO) {
    const dateObj = new Date(timestampISO);
    const formattedDate = dateObj.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
    const formattedTime = dateObj.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true });
    document.getElementById('timestamp').textContent = `Last Updated: ${formattedDate} at ${formattedTime}`;
}


// Add this new function to your script.js file
function updateAnalysisIcons(analysisData) {
    const iconsContainer = document.getElementById('analysisIcons');
    if (!iconsContainer) return;

    // --- 1. Reset all icons by hiding them ---
    document.querySelectorAll('.status-icon, .usage-icon').forEach(icon => {
        icon.style.display = 'none';
    });
    
    // --- 2. Show the correct drinkability status icon ---
    const drinkableIconId = 'icon-' + analysisData.drinkable_icon;
    const drinkableIcon = document.getElementById(drinkableIconId);
    if (drinkableIcon) {
        drinkableIcon.style.display = 'block';
    }

    // --- 3. Show all applicable "other uses" icons ---
    const otherUsesContainer = document.getElementById('otherUsesIconsContainer');
    if (analysisData.other_uses_icons && analysisData.other_uses_icons.length > 0) {
        analysisData.other_uses_icons.forEach(iconName => {
            const usageIconId = 'icon-' + iconName;
            const usageIcon = document.getElementById(usageIconId);
            if (usageIcon) {
                usageIcon.style.display = 'block';
            }
        });
        otherUsesContainer.style.display = 'block';
    } else {
        otherUsesContainer.style.display = 'none';
    }

    // --- 4. Finally, show the main container ---
    iconsContainer.style.display = 'flex';
}

// --- AI (LLM) ANALYSIS FEATURE ---

// Get references to the UI elements for the AI analysis feature.
const returnStaticBtn = document.getElementById('returnStaticBtn');
const getLlmAnalysisBtn = document.getElementById('getLlmAnalysisBtn');
const qualityContainer = document.querySelector('.quality-explanation');
const buttonWrapper = document.querySelector('.llm-button-wrapper');

// Store the initial static HTML of the quality explanation section to restore it later.
const staticHTML = qualityContainer.innerHTML;

/**
 * Renders the UI for the LLM analysis, showing loading states.
 */
function renderLLMtoExplanation() {
    qualityContainer.innerHTML = `
        <h2>
            Malalimang Pagsusuri sa Kalidad ng Tubig Gamit ang AI
            <br><i style="font-size: small;">Detailed Water Quality Analysis with AI</i>
        </h2>
        <div class="llm-parameters">
            <h3>Parameters at Analysis Time:</h3>
            <p>Temperature: <span id="modalTemp">Loading...</span> °C</p>
            <p>pH: <span id="modalPH">Loading...</span></p>
            <p>TDS: <span id="modalTDS">Loading...</span> ppm</p>
            <p>Turbidity: <span id="modalTurb">Loading...</span> NTU</p>
        </div>
        <div class="llm-output-section"><h3>Reasoning:</h3><div id="llmReasoning"></div></div>
        <div class="llm-output-section"><h3>Pangangatwiran:</h3><div id="llmTagalogTranslation"></div></div>
        <div class="llm-output-section"><h3>Suggestions:</h3><div id="llmSuggestions"></div></div>
        <div class="llm-output-section"><h3>Mungkahi:</h3><div id="llmSuggestionsTL"></div></div>
        <div class="llm-output-section"><h3>Possible Other Uses:</h3><div id="llmOtherUses"></div></div>
        <div class="llm-output-section"><h3>Iba Pang Gamit:</h3><div id="llmOtherUsesTL"></div></div>
    `;
    // Re-append the button wrapper and toggle button visibility.
    qualityContainer.appendChild(buttonWrapper);
    getLlmAnalysisBtn.style.display = 'none';
    returnStaticBtn.style.display = 'inline-block';
}

/**
 * Fetches and displays the LLM analysis from the server.
 */
function fetchLlmAnalysis() {
    // Get the current values from the gauges.
    const currentTemp = document.getElementById(gaugeConfigs.temp.id).querySelector('.gauge-value').textContent.replace(` ${gaugeConfigs.temp.unit}`, '');
    const currentPH = document.getElementById(gaugeConfigs.ph.id).querySelector('.gauge-value').textContent.replace(` ${gaugeConfigs.ph.unit}`, '');
    const currentTDS = document.getElementById(gaugeConfigs.tds.id).querySelector('.gauge-value').textContent.replace(` ${gaugeConfigs.tds.unit}`, '');
    const currentTurb = document.getElementById(gaugeConfigs.turb.id).querySelector('.gauge-value').textContent.replace(` ${gaugeConfigs.turb.unit}`, '');
    const currentWaterQuality = document.getElementById('water_quality').textContent;

    // Update the display with the parameters used for the analysis.
    document.getElementById('modalTemp').textContent = currentTemp;
    document.getElementById('modalPH').textContent = currentPH;
    document.getElementById('modalTDS').textContent = currentTDS;
    document.getElementById('modalTurb').textContent = currentTurb;

    // Show loaders in all output sections.
    const loaderHTML = '<div class="loader"></div>';
    const targetIds = ['llmReasoning', 'llmTagalogTranslation', 'llmSuggestions', 'llmSuggestionsTL', 'llmOtherUses', 'llmOtherUsesTL'];
    targetIds.forEach(id => {
        const element = document.getElementById(id);
        if (element) element.innerHTML = loaderHTML;
    });

    // Make the API call to the server.
    fetch('/analytics/get_llm_analysis', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ temp: currentTemp, pH: currentPH, TDS: currentTDS, turb: currentTurb, water_quality: currentWaterQuality }),
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => { throw new Error(err.error || 'Unknown server error'); });
        }
        return response.json();
    })
    .then(data => {
        // Populate the UI with the analysis results.
        document.getElementById('llmReasoning').innerHTML = data.reasoning;
        document.getElementById('llmTagalogTranslation').innerHTML = data.tagalog_translation;
        document.getElementById('llmSuggestions').innerHTML = data.suggestions;
        document.getElementById('llmSuggestionsTL').innerHTML = data.suggestions_tl;
        document.getElementById('llmOtherUses').innerHTML = data.other_uses;
        document.getElementById('llmOtherUsesTL').innerHTML = data.other_uses_tl;
    })
    .catch(error => {
        console.error('Error fetching LLM analysis:', error);
        // Display an error message if the fetch fails.
        document.getElementById('llmReasoning').innerHTML = `<p style="color:red;">Error: Could not retrieve analysis. ${error.message}</p>`;
        targetIds.slice(1).forEach(id => {
            const element = document.getElementById(id);
            if (element) element.innerHTML = '';
        });
    });
}

// Event listener for the "Get LLM Analysis" button.
getLlmAnalysisBtn.addEventListener('click', () => {
    clearInterval(dashboardInterval); // Stop periodic updates.
    renderLLMtoExplanation();
    requestAnimationFrame(fetchLlmAnalysis); // Fetch analysis on the next frame.
});

// Event listener for the "Return to Static" button.
returnStaticBtn.addEventListener('click', () => {
    qualityContainer.innerHTML = staticHTML; // Restore the original content.
    getLlmAnalysisBtn.style.display = 'inline-block';
    returnStaticBtn.style.display = 'none';
    updateDashboard(); // Refresh the static data.
    dashboardInterval = setInterval(updateDashboard, 2000); // Restart periodic updates.
});


/**
 * ========================================================================
 * UNIVERSAL SIDEBAR SCRIPT
 * Manages the slide-out navigation menu, present on all pages.
 * ========================================================================
 */
function setupGlobalNavigation() {
    const sidebar = document.getElementById('sidebarMenu');
    const menuIcon = document.querySelector('.menu-icon');
    
    menuIcon.addEventListener('click', (event) => {
        event.stopPropagation();
        sidebar.classList.toggle('open');
        if (window.innerWidth <= 992) {
            menuIcon.classList.toggle('active');
            menuIcon.innerHTML = menuIcon.classList.contains('active') ? "&#10006;" : "&#9776;";
        }
    });

    document.addEventListener('click', (event) => {
        if (!sidebar.contains(event.target) && !menuIcon.contains(event.target)) {
            sidebar.classList.remove('open');
            if (window.innerWidth <= 992 && menuIcon.classList.contains('active')) {
                menuIcon.classList.remove('active');
                menuIcon.innerHTML = "&#9776;";
            }
        }
    });
}

// Event listener to close the sidebar when clicking outside of it.
document.addEventListener('click', function(event) {
    const sidebar = document.getElementById('sidebarMenu');
    const menuIcon = document.querySelector('.menu-icon');

    if (!sidebar.contains(event.target) && !menuIcon.contains(event.target)) {
        sidebar.classList.remove('open');
        if (window.innerWidth <= 992 && menuIcon.classList.contains('active')) {
            menuIcon.classList.remove('active');
            menuIcon.innerHTML = "&#9776;";
        }
    }
});

// Add event listeners to sidebar links to handle the 'active' state.
const sidebarLinks = document.querySelectorAll('.sidebar-menu a');
sidebarLinks.forEach(link => {
    link.addEventListener('click', () => {
        sidebarLinks.forEach(l => l.classList.remove('active'));
        link.classList.add('active');

        // Automatically close the sidebar after a link is clicked on smaller screens.
        const sidebar = document.getElementById('sidebarMenu');
        const menuIcon = document.querySelector('.menu-icon');
        if (window.innerWidth <= 992 && sidebar.classList.contains('open')) {
            sidebar.classList.remove('open');
            menuIcon.classList.remove('active');
            menuIcon.innerHTML = "&#9776;";
        }
    });
});
