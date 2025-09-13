// static/machine_learning.js

/**
 * ========================================================================
 * UNIVERSAL SIDEBAR & HEADER SCRIPT
 * Manages the slide-out navigation menu.
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

/**
 * ========================================================================
 * MAIN EXECUTION BLOCK
 * This is the primary function that runs after the entire HTML page
 * has been loaded and is ready.
 * ========================================================================
 */
document.addEventListener('DOMContentLoaded', function () {
    
    // ========================================================================
    // === SETUP AND INITIALIZATION ===========================================
    // ========================================================================

    // Initialize the real-time connection to the server.
    const socket = io();
    socket.on('connect', () => console.log('Socket.IO connected successfully.'));

    // Set up the toast notification system for user feedback.
    const { showToast, svgSuccess, svgError } = setupToastNotifications();

    // Store chart instances to manage their state and updates.
    const charts = {};
    
    // Set up universal page elements like the sidebar.
    setupGlobalNavigation();

    // Set up the logic for switching between the different tabs.
    const tabLinks = document.querySelectorAll('.tab-link');
    const tabContents = document.querySelectorAll('.tab-content');
    tabLinks.forEach(link => {
        link.addEventListener('click', () => {
            // This is your existing code to handle switching the active tab
            tabLinks.forEach(l => l.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            link.classList.add('active');
            document.getElementById(link.dataset.tab).classList.add('active');

            // If the clicked tab is the 'Live Analysis' tab, then call its specific function.
            if (link.dataset.tab === 'live') {
                loadCurrentAnalysis();
            }
            else if (link.dataset.tab === 'history') {
                loadAnnotationHistory();
            }
        });
    });

    // ========================================================================
    // === TAB: DECISION MODE =================================================
    // ======================================================================== 

    function setupDecisionModeToggle() {
        const modeBtnThresholds = document.getElementById('modeBtnThresholds');
        const modeBtnML = document.getElementById('modeBtnML');
        const { showToast, svgError, svgSuccess } = setupToastNotifications();

        const setActiveMode = (mode) => {
            if (mode === 'ML') {
                modeBtnML.classList.add('active');
                modeBtnThresholds.classList.remove('active');
            } else {
                modeBtnThresholds.classList.add('active');
                modeBtnML.classList.remove('active');
            }
        };

        // Check model status first
        fetch('/api/ml/status')
            .then(res => res.json())
            .then(statusData => {
                if (!statusData.is_model_available) {
                    // --- FIX: Use class instead of disabled attribute ---
                    modeBtnML.classList.add('disabled');
                    modeBtnML.title = "ML model cannot be used until there is enough data for training.";
                } else {
                    // Ensure it's not disabled if the model IS available
                    modeBtnML.classList.remove('disabled');
                }
            })
            .catch(err => console.error("Error fetching ML status:", err));

        // Load the current decision mode setting
        fetch('/api/ml/decision_mode')
            .then(res => res.json())
            .then(data => {
                setActiveMode(data.mode);
            })
            .catch(err => console.error("Error loading decision mode:", err));

        // Consolidated event listener
        [modeBtnThresholds, modeBtnML].forEach(btn => {
            btn.addEventListener('click', () => {
                // --- FIX: Check for the .disabled class ---
                if (btn.classList.contains('disabled')) {
                    // If it's the disabled-styled ML button, show the toast.
                    if (btn.id === 'modeBtnML') {
                        showToast("Machine learning decision mode disabled: Insufficient data for training.", svgError, 5000);
                    }
                    return; // Stop further execution
                }

                // If not disabled, proceed with saving the new mode.
                const newMode = btn.dataset.mode;
                setActiveMode(newMode);
                
                fetch('/api/ml/decision_mode', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ mode: newMode })
                })
                .then(res => res.json())
                .then(data => {
                    showToast(data.message, svgSuccess);
                })
                .catch(err => console.error("Error saving decision mode:", err));
            });
        });
    }

    // ========================================================================
    // === TAB: LIVE ANALYSIS =================================================
    // ========================================================================

    /**
     * Kicks off the AI analysis process.
     * How it works:
     * 1. Displays the skeleton loader to show that analysis is in progress.
     * 2. Emits a 'request_analysis' event to the server via Socket.IO,
     * telling it to start the time-consuming analysis in the background.
     * 3. This function finishes immediately, preventing the UI from freezing.
     */
    function loadCurrentAnalysis() {
        const elements = {
            reasoningLoader: document.getElementById('ai-reasoning-loader'),
            suggestionsLoader: document.getElementById('ai-suggestions-loader'),
            otherUsesLoader: document.getElementById('ai-other-uses-loader'),
        };
        // Show skeleton loaders to indicate that work is starting.
        Object.values(elements).forEach(el => { if (el) el.style.display = 'block'; });
        
        socket.emit('request_analysis');
        console.log("Requested AI analysis via Socket.IO.");
    }

    /**
     * Listens for the 'analysis_result' event pushed from the server.
     * How it works:
     * 1. This listener is always active, waiting for the server.
     * 2. When the server finishes the background task, it emits the result.
     * 3. This function receives the data, populates the HTML paragraphs with
     * the AI-generated text, and hides the skeleton loaders.
     */
    socket.on('analysis_result', function(data) {
        console.log("Received analysis result:", data);
        const elements = {
            reasoningP: document.getElementById('ai-reasoning'),
            suggestionsP: document.getElementById('ai-suggestions'),
            otherUsesP: document.getElementById('ai-other-uses'),
            reasoningLoader: document.getElementById('ai-reasoning-loader'),
            suggestionsLoader: document.getElementById('ai-suggestions-loader'),
            otherUsesLoader: document.getElementById('ai-other-uses-loader')
        };
        elements.reasoningP.innerHTML = data.reasoning || "Not available.";
        elements.suggestionsP.innerHTML = data.suggestions || "Not available.";
        elements.otherUsesP.innerHTML = data.other_uses || "Not available.";
        Object.values(elements).forEach(el => {
            if (el) el.style.display = el.classList.contains('skeleton-loader') ? 'none' : 'block';
        });
    });

    // ========================================================================
    // === TAB: HISTORICAL SUMMARY ============================================
    // ========================================================================

    const datePicker = flatpickr("#dateRangePicker", { mode: "range", dateFormat: "Y-m-d" });
    const generateBtn = document.getElementById('generateAnalysisBtn');
    const historicalContainer = document.getElementById('historical-reasoning-container');

    function formatDateLocal(date) {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }

    /**
     * Fires when the "Generate Summary" button is clicked.
     * How it works:
     * 1. Gets the start and end dates from the date picker.
     * 2. Sends these dates to the '/api/ml/historical_reasoning' endpoint.
     * 3. The server returns an AI-generated summary as HTML, which is then
     * injected into the reasoning container.
     */
    generateBtn.addEventListener('click', async () => {
        const selectedDates = datePicker.selectedDates;
        if (selectedDates.length < 2) {
            showToast("Please select a start and end date.", svgError);
            return;
        }
        historicalContainer.innerHTML = "<p>Generating AI summary, please wait...</p>";

        const payload = {
            start_date: formatDateLocal(selectedDates[0]),
            end_date: formatDateLocal(selectedDates[1]),
        };

        try {
            const response = await fetch('/api/ml/historical_reasoning', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                throw new Error(`Server returned ${response.status}`);
            }

            const data = await response.json();
            historicalContainer.innerHTML = data.html;
        } catch (error) {
            console.error('Failed to generate historical reasoning:', error);

            // 🔥 Toast alert for no internet / failed communication
            if (!navigator.onLine) {
                showToast("No internet connection. Please reconnect.", svgError);
            } else {
                showToast("Unable to communicate with the AI service.", svgError);
            }

            historicalContainer.innerHTML = "<p>An error occurred. Please try again.</p>";
        }
    });



    // ========================================================================
    // === TAB: FORECASTING ===================================================
    // ========================================================================

    /**
     * A helper function to create a single Chart.js line chart instance.
     */
    function createChart(canvasId, label) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return null;
        const ctx = canvas.getContext('2d');
        return new Chart(ctx, {
            type: 'line', data: { datasets: [] },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { title: { display: true, text: label } },
                scales: { 
                    x: { type: 'time', time: { unit: 'hour' } },
                    y: { beginAtZero: false }
                },
            },
        });
    }

    /**
     * Fetches forecast data and updates the charts.
     * How it works:
     * 1. Checks which forecast source is selected (Standard or Demo).
     * 2. Fetches the appropriate data from the '/api/ml/forecasts' endpoint.
     * 3. Dynamically calculates the best Y-axis range to "zoom in" on the data.
     * 4. Updates the chart datasets with the new forecast line and confidence interval.
     */
    // Fetches forecast data and now includes DYNAMIC Y-AXIS SCALING
    async function loadForecasts() {
        const selectedSource = document.querySelector('input[name="forecastSource"]:checked').value;
        showToast("Generating new forecast demo...", svgSuccess);

        try {
            const response = await fetch(`/api/ml/forecasts?source=${selectedSource}`);
            const data = await response.json();
            const isDataEmpty = Object.values(data).every(arr => arr.length === 0);

            if (isDataEmpty) {
                showToast("No Forecast: More data needed for this source.", svgError);
                console.warn("Forecast API returned empty data for the selected source.");
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

                const allYValues = [
                    ...chartData.map(p => p.y),
                    ...lowerBound.map(p => p.y),
                    ...upperBound.map(p => p.y)
                ].filter(v => v !== null && !isNaN(v));

                if (allYValues.length > 0) {
                    const dataMin = Math.min(...allYValues);
                    const dataMax = Math.max(...allYValues);
                    const range = dataMax - dataMin;
                    
                    const buffer = range > 0.1 ? range * 0.15 : 0.5;
                    
                    let yAxisMin = dataMin - buffer;
                    let yAxisMax = dataMax + buffer;

                    if (param === 'ph') {
                        yAxisMin = Math.max(0, yAxisMin);
                        yAxisMax = Math.min(14, yAxisMax);
                    } else {
                        yAxisMin = Math.max(0, yAxisMin);
                    }

                    charts[param].options.scales.y.min = yAxisMin;
                    charts[param].options.scales.y.max = yAxisMax;
                }

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


    /**
     * Fires when the user selects a different forecast data source.
     */
    document.querySelectorAll('input[name="forecastSource"]').forEach(radio => {
        radio.addEventListener('change', loadForecasts);
    });

    // ========================================================================
    // === TABS: PENDING REVIEW & ANNOTATION HISTORY ==========================
    // ========================================================================

    /**
     * Fetches unannotated anomalies and displays them as cards for user review.
     * How it works:
     * 1. Fetches a list of events from the '/api/ml/anomalies' endpoint.
     * 2. Clears any existing cards from the container.
     * 3. If there are events, it loops through them and dynamically creates
     * an HTML card for each one, then appends it to the page.
     * 4. If there are no events, it displays the "No new events" message.
     */
    
    // --- ANOMALY ANNOTATION LOGIC ---
    async function loadAnomalies() {
        const container = document.getElementById('annotation-container');
        const noEventsMessage = document.getElementById('no-anomalies-message');
        try {
            const response = await fetch('/api/ml/anomalies');
            const anomalies = await response.json();
            
            container.innerHTML = '';
            
            if (anomalies.length === 0) {
                noEventsMessage.style.display = 'block';
            } else {
                noEventsMessage.style.display = 'none';
                anomalies.forEach(event => {
                    // Create the new swipe wrapper structure
                    const swipeContainer = document.createElement('div');
                    swipeContainer.className = 'swipe-container';

                    const card = document.createElement('div');
                    card.className = 'annotation-card';
                    if (event.anomaly_type) card.classList.add(event.anomaly_type);

                    // === THIS IS THE FIX ===============================================
                    // The full HTML content for the card is now included.
                    card.innerHTML = `
                        <div class="annotation-details">
                            <h3>Event Detected: ${event.parameter.toUpperCase()} Anomaly</h3>
                            <div class="detail-item"><strong>Time:</strong> ${new Date(event.timestamp).toLocaleString()}</div>
                            <div class="detail-item"><strong>Value:</strong> ${event.value.toFixed(2)}</div>
                            <div class="detail-item"><strong>Type:</strong> ${event.anomaly_type}</div>
                            <div class="detail-item"><strong>AI-Suggested Causes:</strong>
                                <ul class="rca-list">${event.rca_suggestions.map(s => `<li>${s}</li>`).join('')}</ul>
                            </div>
                        </div>
                        <form class="annotation-form" data-id="${event.id}">
                            <div class="form-group">
                                <label>Ano ang sanhi?<br><i>What was the cause?</i></label>
                                <select name="label" required>
                                    <option value="" disabled selected>-- Select the primary cause --</option>
                                    <optgroup label="Environmental Causes">
                                        <option value="Heavy Rainfall / Runoff">Heavy Rainfall / Runoff</option>
                                        <option value="Algal Bloom">Algal Bloom</option>
                                        <option value="Sediment Stir-up">Sediment Stir-up (Natural)</option>
                                    </optgroup>
                                    <optgroup label="Contamination Events">
                                        <option value="Industrial Discharge">Industrial Discharge</option>
                                        <option value="Agricultural Runoff">Agricultural Runoff</option>
                                        <option value="Sewage Contamination">Sewage Contamination</option>
                                    </optgroup>
                                    <optgroup label="System & Sensor Events">
                                        <option value="Sensor Maintenance">Sensor Maintenance / Cleaning</option>
                                        <option value="Sensor Malfunction">Sensor Malfunction / Error</option>
                                        <option value="Calibration Event">Calibration Event</option>
                                    </optgroup>
                                    <optgroup label="Validation">
                                        <option value="False Positive">False Positive (Normal Fluctuation)</option>
                                        <option value="Confirmed Anomaly (Unknown Cause)">Confirmed Anomaly (Unknown Cause)</option>
                                    </optgroup>
                                    <option value="Other">Other (Specify in comments)</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label>Comments</label>
                                <textarea name="comments" rows="2" placeholder="Provide additional details..."></textarea>
                            </div>
                            <button type="submit" class="action-button">Submit Feedback</button>
                        </form>
                    `;
                    // ===================================================================

                    const revealBg = document.createElement('div');
                    revealBg.className = 'swipe-reveal-background';
                    revealBg.innerHTML = `<span>✅</span> Mark as False Positive`;
                    
                    swipeContainer.appendChild(revealBg);
                    swipeContainer.appendChild(card);
                    container.appendChild(swipeContainer);

                    // --- Swipe Event Handling Logic ---
                    let isSwiping = false;
                    let startX = 0;
                    let swipeDistance = 0;
                    const swipeThreshold = card.offsetWidth / 2;

                    function onSwipeStart(e) {
                        if (e.target.closest('form')) return;
                        isSwiping = true;
                        startX = e.pageX || e.touches[0].pageX;
                        card.style.transition = 'none';
                        card.classList.add('swiping');
                        document.addEventListener('mousemove', onSwipeMove);
                        document.addEventListener('touchmove', onSwipeMove);
                        document.addEventListener('mouseup', onSwipeEnd);
                        document.addEventListener('touchend', onSwipeEnd);
                    }

                    function onSwipeMove(e) {
                        if (!isSwiping) return;
                        const currentX = e.pageX || e.touches[0].pageX;
                        swipeDistance = currentX - startX;
                        if (swipeDistance < 0) swipeDistance = 0;
                        card.style.transform = `translateX(${swipeDistance}px)`;
                    }

                    function onSwipeEnd() {
                        if (!isSwiping) return;
                        isSwiping = false;
                        card.classList.remove('swiping');
                        
                        if (swipeDistance > swipeThreshold) {
                            submitQuickAnnotation(event.id, 'False Positive', card);
                        } else {
                            card.style.transition = 'transform 0.3s ease';
                            card.style.transform = 'translateX(0px)';
                        }
                        
                        document.removeEventListener('mousemove', onSwipeMove);
                        document.removeEventListener('touchmove', onSwipeMove);
                        document.removeEventListener('mouseup', onSwipeEnd);
                        document.removeEventListener('touchend', onSwipeEnd);
                    }

                    card.addEventListener('mousedown', onSwipeStart);
                    card.addEventListener('touchstart', onSwipeStart);
                });
            }
        } catch (error) {
            console.error('Failed to load pending anomalies:', error);
        }
    }

    /**
     * Helper function to submit an annotation without a form.
     */
    async function submitQuickAnnotation(anomalyId, label, cardElement) {
        const data = { anomaly_id: anomalyId, label: label, comments: "Annotated via swipe action." };
        try {
            const response = await fetch('/api/ml/annotate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            const result = await response.json();
            if (response.ok) {
                // Animate card out and remove it
                cardElement.style.transition = 'transform 0.3s ease, opacity 0.3s ease';
                cardElement.style.transform = 'translateX(100%)';
                cardElement.style.opacity = '0';
                setTimeout(() => {
                    cardElement.parentElement.remove();
                    loadAnnotationHistory(); // Refresh history
                }, 300);
                showToast(`Event marked as ${label}.`, svgSuccess);
            } else {
                throw new Error(result.message);
            }
        } catch (error) {
            showToast(`Error: ${error.message}`, svgError);
            // If submission fails, snap card back to place
            cardElement.style.transition = 'transform 0.3s ease';
            cardElement.style.transform = 'translateX(0px)';
        }
    }

    async function loadAnnotationHistory() {
        const container = document.getElementById('history-container');
        const noHistoryMessage = document.getElementById('no-history-message');

        // Helper function to create a CSS-friendly class from a label
        function formatLabelForClass(label) {
            if (!label) return '';
            // Converts "False Positive (Normal Fluctuation)" to "label-false-positive-normal-fluctuation"
            return 'label-' + label.toLowerCase().replace(/\s*\(.*\)\s*/g, '').replace(/[\s/]+/g, '-');
        }

        try {
            const response = await fetch('/api/ml/anomalies/history');
            const history = await response.json();

            container.innerHTML = '';

            if (history.length === 0) {
                noHistoryMessage.style.display = 'block';
            } else {
                noHistoryMessage.style.display = 'none';
                history.forEach(entry => {
                    const card = document.createElement('div');
                    card.className = 'history-card';
                    
                    // Add the label as a class for color-coding
                    const labelClass = formatLabelForClass(entry.label);
                    if (labelClass) {
                        card.classList.add(labelClass);
                    }
                    
                    const userComments = entry.comments ? `<div class="user-comments">${entry.comments.replace(/</g, "&lt;").replace(/>/g, "&gt;")}</div>` : '';

                    card.innerHTML = `
                        <div class="history-event-info">
                            <div class="history-event-title">${entry.parameter.toUpperCase()} (${entry.anomaly_type})</div>
                            <div class="history-event-detail"><strong>Value:</strong> ${entry.value.toFixed(2)}</div>
                            <div class="history-event-detail"><strong>Detected On:</strong> ${new Date(entry.timestamp).toLocaleString()}</div>
                        </div>
                        <div class="history-annotation-info">
                            <div class="history-annotation-label">
                                <strong>Labeled As:</strong> <span class="annotation-label">${entry.label}</span>
                            </div>
                            <div class="history-annotation-detail">
                                <strong>Annotated By:</strong> ${entry.annotated_by || 'N/A'} on ${new Date(entry.annotated_at).toLocaleString()}
                            </div>
                            ${userComments}
                        </div>
                    `;
                    container.appendChild(card);
                });
            }
        } catch (error) {
            console.error('Failed to load annotation history:', error);
        }
    }

    /**
     * Fires when a user submits an annotation form.
     * How it works:
     * 1. Intercepts the form submission to prevent a page reload.
     * 2. Packages the anomaly ID, selected label, and comments into JSON.
     * 3. Sends this data to the '/api/ml/annotate' endpoint to be saved.
     * 4. On success, the card is hidden from view.
     */
    document.getElementById('annotation-container').addEventListener('submit', async function (e) {
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

    // ========================================================================
    // === PAGE INITIALIZATION ================================================
    // ========================================================================
    // Call the main functions to load the initial state of the page.
    loadForecasts();
    loadAnomalies();    
    loadAnnotationHistory();
    setupDecisionModeToggle();
});

/**
 * ========================================================================
 * HELPER FUNCTION: TOAST NOTIFICATIONS
 * Manages the pop-up success/error messages.
 * ========================================================================
 */
function setupToastNotifications() {
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