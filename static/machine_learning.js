// static/machine_learning.js

/**
 * ------------------------------------------------------------------------
 * UNIVERSAL SIDEBAR & HEADER SCRIPT
 * ------------------------------------------------------------------------
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

// This event listener ensures that the entire script runs only after the
// HTML document has been fully loaded and parsed.
document.addEventListener('DOMContentLoaded', function () {

    // --- GLOBAL TOAST NOTIFICATION SETUP ---
    const { showToast, svgSuccess, svgError } = setupToastNotifications();

    // --- TABS LOGIC ---
    const tabLinks = document.querySelectorAll('.tab-link');
    const tabContents = document.querySelectorAll('.tab-content');
    tabLinks.forEach(link => {
        link.addEventListener('click', () => {
            tabLinks.forEach(l => l.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            link.classList.add('active');
            const tabId = link.dataset.tab;
            document.getElementById(tabId).classList.add('active');
        });
    });

    // --- CHART & FORECASTING LOGIC ---
    const charts = {}; // Object to hold the created chart instances.

    // --- INITIALIZE GLOBAL NAVIGATION ---
    setupGlobalNavigation();

    // Creates a single line chart instance with specific options.
    function createChart(canvasId, label) {
        // Find the canvas element in the document
        const canvas = document.getElementById(canvasId);
        // If the canvas doesn't exist, stop to prevent errors.
        if (!canvas) {
            console.error(`Chart canvas with ID "${canvasId}" not found.`);
            return null;
        }
        // Get the 2D drawing context from the canvas.
        const ctx = canvas.getContext('2d');
        return new Chart(ctx, {
            type: 'line',
            data: { datasets: [] },
            options: {
                responsive: true,
                maintainAspectRatio: false, // Helps with resizing in hidden tabs
                plugins: { title: { display: true, text: label } },
                scales: { x: { type: 'time', time: { unit: 'hour' } } },
            },
        });
    }

    // Fetches forecast data from the API and updates the charts.
    async function loadForecasts() {
    try {
        const response = await fetch('/api/ml/forecasts');
        const data = await response.json();

        const isDataEmpty = Object.values(data).every(arr => arr.length === 0);

        if (isDataEmpty) {
            // MODIFIED: Updated the toast message to be more specific.
            showToast("No Forecast: More data needed to learn patterns.", svgError);
            console.warn("Forecast API returned empty data arrays. The model may need more historical readings to train.");
            return;
        }

        for (const param in data) {
            if (!charts[param]) {
                charts[param] = createChart(`${param}ForecastChart`, `${param.toUpperCase()} Forecast`);
            }
            
            if (!charts[param]) continue;

            const chartData = data[param].map(d => ({ x: new Date(d.timestamp), y: d.forecast_value }));
            const lowerBound = data[param].map(d => ({ x: new Date(d.timestamp), y: d.lower_bound }));
            const upperBound = data[param].map(d => ({ x: new Date(d.timestamp), y: d.upper_bound }));

            charts[param].data.datasets = [
                { label: 'Forecast', data: chartData, borderColor: 'rgb(75, 192, 192)', tension: 0.1 },
                { label: 'Confidence Interval', data: upperBound, fill: '-1', backgroundColor: 'rgba(75, 192, 192, 0.2)', borderColor: 'transparent' },
                { label: 'Confidence Interval (hidden)', data: lowerBound, fill: false, borderColor: 'transparent' },
            ];
            charts[param].update();
        }
    } catch (error) {
        console.error('Failed to load forecast data:', error);
        showToast("An error occurred while loading forecasts.", svgError);
    }
}

    // --- ANOMALY ANNOTATION LOGIC ---
    // (This section remains the same)
    async function loadAnomalies() {
        const container = document.getElementById('annotation-container');
        const noEventsMessage = document.getElementById('no-anomalies-message');
        try {
            const response = await fetch('/api/ml/anomalies');
            const anomalies = await response.json();
            noEventsMessage.style.display = anomalies.length === 0 ? 'block' : 'none';
            container.innerHTML = '';
            anomalies.forEach(event => {
                const card = document.createElement('div');
                card.className = 'annotation-card';
                card.innerHTML = `
                    <div class="annotation-details">
                        <h3>Event Detected: ${event.parameter.toUpperCase()} Anomaly</h3>
                        <div class="detail-item"><strong>Time:</strong> ${new Date(event.timestamp).toLocaleString()}</div>
                        <div class="detail-item"><strong>Value:</strong> ${event.value.toFixed(2)}</div>
                        <div class="detail-item"><strong>Type:</strong> ${event.type}</div>
                        <div class="detail-item"><strong>AI-Suggested Causes:</strong>
                            <ul class="rca-list">${event.rca_suggestions.map(s => `<li>${s}</li>`).join('')}</ul>
                        </div>
                    </div>
                    <form class="annotation-form" data-id="${event.id}">
                        <div class="form-group"><label>What was the cause?</label><select name="label" required><option value="">-- Select --</option><option>Pollution Event</option><option>Sensor Maintenance</option><option>Heavy Rainfall</option><option>False Positive</option><option>Other</option></select></div>
                        <div class="form-group"><label>Comments</label><textarea name="comments" rows="2"></textarea></div>
                        <button type="submit" class="action-button">Submit Feedback</button>
                    </form>`;
                container.appendChild(card);
            });
        } catch (error) {
            console.error('Failed to load anomalies:', error);
        }
    }

    // --- EVENT LISTENERS ---
    document.getElementById('annotation-container').addEventListener('submit', async function (e) {
        // (This section remains the same)
        if (e.target.classList.contains('annotation-form')) {
            e.preventDefault();
            const form = e.target;
            const data = {
                anomaly_id: parseInt(form.dataset.id),
                label: form.querySelector('[name="label"]').value,
                comments: form.querySelector('[name="comments"]').value,
            };
            try {
                const response = await fetch('/api/ml/annotate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
                const result = await response.json();
                if (response.ok) {
                    form.closest('.annotation-card').style.display = 'none';
                    showToast(result.message, svgSuccess);
                } else {
                    showToast(`Error: ${result.message}`, svgError);
                }
            } catch (error) {
                showToast(`Error: ${error.message}`, svgError);
                console.error('Failed to submit annotation:', error);
            }
        }
    });

    // --- LIVE & HISTORICAL ANALYSIS LOGIC ---
    const datePicker = flatpickr("#dateRangePicker", { mode: "range", dateFormat: "Y-m-d" });
    const generateBtn = document.getElementById('generateAnalysisBtn');
    const historicalContainer = document.getElementById('historical-reasoning-container');

    async function loadCurrentAnalysis() {
        // (This section remains the same)
        try {
            const response = await fetch('/api/ml/current_analysis');
            const data = await response.json();
            document.getElementById('ai-reasoning').innerHTML = data.reasoning || "Not available.";
            document.getElementById('ai-suggestions').innerHTML = data.suggestions || "Not available.";
            document.getElementById('ai-other-uses').innerHTML = data.other_uses || "Not available.";
        } catch (error) {
            console.error('Failed to load current analysis:', error);
            document.getElementById('ai-reasoning').textContent = "Error loading analysis.";
        }
    }

    generateBtn.addEventListener('click', async () => {
        // (This section remains the same)
        const selectedDates = datePicker.selectedDates;
        if (selectedDates.length < 2) {
            alert("Please select a start and end date.");
            return;
        }
        historicalContainer.innerHTML = "<p>Generating AI summary, please wait...</p>";
        const payload = {
            start_date: selectedDates[0].toISOString().split('T')[0],
            end_date: selectedDates[1].toISOString().split('T')[0],
        };
        try {
            const response = await fetch('/api/ml/historical_reasoning', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
            const data = await response.json();
            historicalContainer.innerHTML = data.html;
        } catch (error) {
            console.error('Failed to generate historical reasoning:', error);
            historicalContainer.innerHTML = "<p>An error occurred. Please try again.</p>";
        }
    });

    // --- INITIALIZATION ---
    loadCurrentAnalysis();
    loadForecasts();
    loadAnomalies();
});

// --- HELPER FUNCTION FOR TOAST NOTIFICATIONS ---
function setupToastNotifications() {
    // (This section remains the same)
    const toastModal = document.getElementById('toastModal');
    const toastIcon = document.getElementById('toastIcon');
    const toastMessage = document.getElementById('toastMessage');
    const svgSuccess = `<svg viewBox="0 0 24 24" fill="none" stroke="#28a745" stroke-width="3"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>`;
    const svgError = `<svg viewBox="0 0 24 24" fill="none" stroke="#dc3545" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>`;
    const showToast = (message, icon, duration = 3000) => {
        if (!toastModal) return;
        toastMessage.textContent = message;
        toastIcon.innerHTML = icon;
        toastModal.classList.add('show');
        setTimeout(() => toastModal.classList.remove('show'), duration);
    };
    return { showToast, svgSuccess, svgError };
}