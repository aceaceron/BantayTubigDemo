/**
 * ------------------------------------------------------------------------
 * UNIVERSAL SIDEBAR & HEADER SCRIPT
 * ------------------------------------------------------------------------
 * This section contains the logic for the sidebar navigation menu and
 * the dynamic timestamp, which are present on all pages.
 */

/**
 * Toggles the visibility of the sidebar navigation menu.
 * On smaller screens, it also changes the hamburger icon to an 'X'.
 */
function toggleMenu() {
    const sidebar = document.getElementById('sidebarMenu');
    const menuIcon = document.querySelector('.menu-icon');

    sidebar.classList.toggle('open');

    // On smaller screens, toggle the icon between hamburger and 'X'.
    if (window.innerWidth <= 992) {
        menuIcon.classList.toggle('active');
        if (menuIcon.classList.contains('active')) {
            menuIcon.innerHTML = "&#10006;"; // 'X' icon
        } else {
            menuIcon.innerHTML = "&#9776;"; // Hamburger icon
        }
    }
}

// Global click listener to close the sidebar when clicking outside of it.
document.addEventListener('click', function(event) {
    const sidebar = document.getElementById('sidebarMenu');
    const menuIcon = document.querySelector('.menu-icon');

    if (!sidebar.contains(event.target) && !menuIcon.contains(event.target)) {
        sidebar.classList.remove('open');

        // Reset the icon on smaller screens if the sidebar is closed.
        if (window.innerWidth <= 992 && menuIcon.classList.contains('active')) {
            menuIcon.classList.remove('active');
            menuIcon.innerHTML = "&#9776;";
        }
    }
});

/**
 * ------------------------------------------------------------------------
 * ANALYTICS PAGE SCRIPT
 * ------------------------------------------------------------------------
 * This script handles all functionality for the Analytics & Reports page,
 * including data fetching, chart rendering, filtering, and report generation.
 */
document.addEventListener('DOMContentLoaded', function() {

    // --- GLOBAL CONFIGURATION & STATE MANAGEMENT ---

    const analysisLocation = "Labo, Camarines Norte"; // Location for AI context.
    let historicalChart, keyDriverChart; // Chart.js instances.
    let rawData = { primary: [], comparison: [] }; // Stores unfiltered data from the server.
    let filteredData = []; // Stores data after filters (date, time, interval) are applied.
    let currentPage = 1;
    const rowsPerPage = 15;
    let sortColumn = 'timestamp';
    let sortDirection = 'desc';

    // Configuration object for water quality parameters.
    const parameterConfig = {
        temperature: { label: 'Temperature (°C)', primaryColor: 'rgb(255, 99, 132)', compareColor: 'rgba(255, 99, 132, 0.4)' },
        ph: { label: 'pH', primaryColor: 'rgb(54, 162, 235)', compareColor: 'rgba(54, 162, 235, 0.4)' },
        tds: { label: 'TDS (ppm)', primaryColor: 'rgb(75, 192, 192)', compareColor: 'rgba(75, 192, 192, 0.4)' },
        turbidity: { label: 'Turbidity (NTU)', primaryColor: 'rgb(255, 159, 64)', compareColor: 'rgba(255, 159, 64, 0.4)' }
    };

    // --- DOM ELEMENT SELECTORS ---
    
    // Filter Controls
    const primaryDatePicker = document.getElementById('dateRangePicker');
    const compareDatePicker = document.getElementById('compareDateRangePicker');
    const timePickerStart = document.getElementById('timePickerStart');
    const timePickerEnd = document.getElementById('timePickerEnd');
    const intervalSelector = document.getElementById('intervalSelector');
    const checkboxes = document.querySelectorAll('input[name="parameter"]');
    const qualityCheckboxes = document.querySelectorAll('input[name="quality"]');

    // Data Display: Table & Stats
    const tableBody = document.querySelector('#historicalDataTable tbody');
    const tableHeaders = document.querySelectorAll('#historicalDataTable th');
    const statsContainer = document.getElementById('stats-container');
    
    // Pagination Controls
    const prevPageBtn = document.getElementById('prevPageBtn');
    const nextPageBtn = document.getElementById('nextPageBtn');
    const pageInfo = document.getElementById('pageInfo');

    // Report Export Buttons
    const exportPdfBtn = document.getElementById('exportPdfBtn');
    const exportCsvBtn = document.getElementById('exportCsvBtn');

    // Advanced Analytics UI
    const toggleAdvancedBtn = document.getElementById('toggleAdvancedBtn');
    const advancedFeaturesContainer = document.getElementById('advanced-features-container');
    const tempSlider = document.getElementById('temp-slider');
    const phSlider = document.getElementById('ph-slider');
    const tdsSlider = document.getElementById('tds-slider');
    const turbSlider = document.getElementById('turb-slider');
    const tempValue = document.getElementById('temp-value');
    const phValue = document.getElementById('ph-value');
    const tdsValue = document.getElementById('tds-value');
    const turbValue = document.getElementById('turb-value');
    const scenarioPrediction = document.getElementById('scenario-prediction');

    // AI Reasoning Modal UI
    const generateReasoningBtn = document.getElementById('generateReasoningBtn');
    const llmReasoningModal = document.getElementById('llmReasoningModal');
    const closeLlmModalBtn = document.getElementById('closeLlmModalBtn');
    const llmLoadingSpinner = document.getElementById('llmLoadingSpinner');
    const llmResultContainer = document.getElementById('llmResultContainer');


    // --- INITIALIZATION FUNCTIONS ---

    /**
     * Creates and configures the main historical line chart and the key driver bar chart.
     */
    function initializeCharts() {
        const histCtx = document.getElementById('historicalChart').getContext('2d');
        historicalChart = new Chart(histCtx, {
            type: 'line',
            data: { datasets: [] }, // Datasets are added dynamically
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { type: 'time', time: { unit: 'day', tooltipFormat: 'MMM dd, yyyy HH:mm' }, title: { display: true, text: 'Date' } },
                    y: { beginAtZero: false, title: { display: true, text: 'Value' } }
                },
                plugins: { legend: { position: 'top' }, tooltip: { mode: 'index', intersect: false } }
            }
        });

        const driverCtx = document.getElementById('keyDriverChart').getContext('2d');
        keyDriverChart = new Chart(driverCtx, {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: 'Parameter Influence',
                    data: [],
                    backgroundColor: ['rgba(255, 99, 132, 0.5)', 'rgba(54, 162, 235, 0.5)', 'rgba(75, 192, 192, 0.5)', 'rgba(255, 159, 64, 0.5)'],
                    borderColor: ['rgb(255, 99, 132)', 'rgb(54, 162, 235)', 'rgb(75, 192, 192)', 'rgb(255, 159, 64)'],
                    borderWidth: 1
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false }, title: { display: true, text: 'Most Influential Parameters' } },
                scales: { x: { beginAtZero: true, ticks: { callback: value => (value * 100).toFixed(0) + '%' } } }
            }
        });
    }

    /**
     * Initializes the Flatpickr instances for date and time selection.
     * Also triggers the initial data fetch for the default date range.
     */
    function initializePickers() {
        flatpickr(primaryDatePicker, {
            mode: "range",
            dateFormat: "Y-m-d",
            defaultDate: [new Date().fp_incr(-1), new Date()], // Default to yesterday and today
            onChange: (selectedDates) => {
                if (selectedDates.length === 2) fetchHistoricalData(selectedDates[0], selectedDates[1], 'primary');
            }
        });

        flatpickr(compareDatePicker, {
            mode: "range",
            dateFormat: "Y-m-d",
            onChange: (selectedDates) => {
                if (selectedDates.length === 2) fetchHistoricalData(selectedDates[0], selectedDates[1], 'comparison');
            }
        });

        flatpickr(timePickerStart, {
            enableTime: true,
            noCalendar: true,
            dateFormat: "h:i K", // 12-hour format with AM/PM
            onChange: () => processAndDisplayData('primary')
        });

        flatpickr(timePickerEnd, {
            enableTime: true,
            noCalendar: true,
            dateFormat: "h:i K",
            onChange: () => processAndDisplayData('primary')
        });

        // Initial data fetch for the default date range.
        fetchHistoricalData(new Date().fp_incr(-1), new Date(), 'primary');
    }

    /**
     * Initializes the "What-If" scenario simulator sliders and runs the initial prediction.
     */
    function initializeSimulator() {
        updateSimulatorUI();
        runScenarioPrediction();
    }


    // --- DATA FETCHING & PROCESSING ---

    /**
     * Fetches historical data from the server for a given date range and type.
     * @param {Date} startDate - The start of the date range.
     * @param {Date} endDate - The end of the date range.
     * @param {string} type - The type of data to fetch ('primary' or 'comparison').
     */
    async function fetchHistoricalData(startDate, endDate, type) {
        const start = startDate.toISOString().split('T')[0];
        const end = new Date(endDate.getTime() + 24 * 60 * 60 * 1000).toISOString().split('T')[0]; // Include the full end day.
        
        try {
            const response = await fetch(`/analytics/historical_data?start_date=${start}&end_date=${end}`);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            
            const jsonData = await response.json();
            
            // Store and parse the fetched data.
            rawData[type] = jsonData.map(row => ({
                ...row,
                temperature: parseFloat(row.temperature),
                ph: parseFloat(row.ph),
                tds: parseFloat(row.tds),
                turbidity: parseFloat(row.turbidity),
            }));

            processAndDisplayData(type);
        } catch (error) {
            console.error(`Failed to fetch ${type} data:`, error);
        }
    }

    /**
     * Fetches the feature importance data for the key driver analysis chart.
     */
    async function fetchKeyDrivers() {
        try {
            const response = await fetch('/analytics/feature_importance');
            if (!response.ok) throw new Error('Failed to load key drivers');
            const data = await response.json();
            keyDriverChart.data.labels = Object.keys(data).map(k => k.toUpperCase());
            keyDriverChart.data.datasets[0].data = Object.values(data);
            keyDriverChart.update();
        } catch (error) { 
            console.error("Error fetching key drivers:", error); 
        }
    }

    /**
     * A central function to trigger data processing and UI updates after new data is fetched or filters are changed.
     * @param {string} type - The type of data that was updated ('primary' or 'comparison').
     */
    function processAndDisplayData(type) {
        if (type === 'primary') {
            applyFilters();
            applySort();
            currentPage = 1;
            renderTable();
            calculateAndDisplayStats();
        }
        updateChartData();
    }

    /**
     * Applies time range and interval filters to the raw primary data.
     */
    function applyFilters() {
        let dataToFilter = [...rawData.primary];
        const startTimeString = timePickerStart.value;
        const endTimeString = timePickerEnd.value;

        // Apply hourly time range filter if both start and end times are set.
        if (startTimeString && endTimeString) {
            const start = parse12HourTime(startTimeString);
            const end = parse12HourTime(endTimeString);

            if (start && end) {
                const totalMinutesStart = start.hours * 60 + start.minutes;
                const totalMinutesEnd = end.hours * 60 + end.minutes;

                dataToFilter = dataToFilter.filter(row => {
                    const rowDate = new Date(row.timestamp);
                    const totalMinutesRow = rowDate.getHours() * 60 + rowDate.getMinutes();
                    return totalMinutesRow >= totalMinutesStart && totalMinutesRow <= totalMinutesEnd;
                });
            }
        }

        // Apply interval downsampling if an interval is selected.
        const interval = parseInt(intervalSelector.value, 10);
        if (interval > 1) {
            const lastTimestamps = {};
            dataToFilter = dataToFilter.filter(row => {
                const rowDate = new Date(row.timestamp);
                const minute = rowDate.getMinutes();
                if (minute % interval === 0) {
                    const key = `${rowDate.getDate()}-${rowDate.getHours()}-${minute}`;
                    if (!lastTimestamps[key]) {
                        lastTimestamps[key] = true;
                        return true;
                    }
                }
                return false;
            });
        }
        
        // Apply water quality filter.
        const selectedQualities = Array.from(qualityCheckboxes)
                                       .filter(cb => cb.checked)
                                       .map(cb => cb.value);

        if (selectedQualities.length > 0) {
            dataToFilter = dataToFilter.filter(row => {
                // Treat null or undefined quality as 'Unknown' to match the filter checkbox.
                const quality = row.water_quality || 'Unknown';
                return selectedQualities.includes(quality);
            });
        }

        filteredData = dataToFilter;
    }

    /**
     * Sorts the filtered data based on the current sort column and direction.
     */
    function applySort() {
        filteredData.sort((a, b) => {
            let valA = a[sortColumn], valB = b[sortColumn];
            if (sortColumn === 'timestamp') { 
                valA = new Date(valA); 
                valB = new Date(valB); 
            }
            if (valA < valB) return sortDirection === 'asc' ? -1 : 1;
            if (valA > valB) return sortDirection === 'asc' ? 1 : -1;
            return 0;
        });
    }


    // --- UI RENDERING & UPDATES ---

    /**
     * Renders the data table for the current page.
     */
    function renderTable() {
        tableBody.innerHTML = '';
        const start = (currentPage - 1) * rowsPerPage;
        const end = start + rowsPerPage;
        const paginatedData = filteredData.slice(start, end);

        if (paginatedData.length === 0) {
            tableBody.innerHTML = `<tr><td colspan="6">No data available for the selected filters.</td></tr>`;
        } else {
            paginatedData.forEach(row => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${new Date(row.timestamp).toLocaleString()}</td>
                    <td>${isNaN(row.temperature) ? 'N/A' : row.temperature.toFixed(2)}</td>
                    <td>${isNaN(row.ph) ? 'N/A' : row.ph.toFixed(2)}</td>
                    <td>${isNaN(row.tds) ? 'N/A' : row.tds}</td>
                    <td>${isNaN(row.turbidity) ? 'N/A' : row.turbidity.toFixed(2)}</td>
                    <td><span class="quality-badge quality-${(row.water_quality || 'unknown').toLowerCase()}">${row.water_quality || 'Unknown'}</span></td>
                `;
                tableBody.appendChild(tr);
            });
        }
        updatePaginationControls();
    }

    /**
     * Updates the main historical chart with the latest filtered and comparison data.
     */
    function updateChartData() {
        const selectedParams = Array.from(checkboxes).filter(cb => cb.checked).map(cb => cb.value);
        const newDatasets = [];

        selectedParams.forEach(key => {
            const config = parameterConfig[key];
            // Add primary dataset
            newDatasets.push({
                label: config.label + ' (Primary)',
                borderColor: config.primaryColor,
                data: filteredData.map(d => ({ x: new Date(d.timestamp), y: d[key] })),
                yAxisID: 'y',
                tension: 0.1
            });
            // Add comparison dataset if data exists
            if (rawData.comparison.length > 0) {
                newDatasets.push({
                    label: config.label + ' (Comparison)',
                    borderColor: config.compareColor,
                    borderDash: [5, 5],
                    data: rawData.comparison.map(d => ({ x: new Date(d.timestamp), y: d[key] })),
                    yAxisID: 'y',
                    tension: 0.1
                });
            }
        });

        historicalChart.data.datasets = newDatasets;
        historicalChart.update();
    }

    /**
     * Calculates and displays statistical summaries (mean, median, etc.) for the filtered data.
     */
    function calculateAndDisplayStats() {
        statsContainer.innerHTML = '';
        if (filteredData.length === 0) {
            statsContainer.innerHTML = '<p>No data to analyze.</p>';
            return;
        }
        Object.keys(parameterConfig).forEach(key => {
            const values = filteredData.map(d => d[key]).filter(v => v !== null && !isNaN(v));
            if (values.length === 0) return;

            const sum = values.reduce((a, b) => a + b, 0);
            const mean = sum / values.length;
            const stdDev = Math.sqrt(values.map(x => Math.pow(x - mean, 2)).reduce((a, b) => a + b) / values.length);
            
            statsContainer.innerHTML += `
                <div class="stat-card">
                    <h4>${parameterConfig[key].label}</h4>
                    <p><strong>Mean:</strong> ${mean.toFixed(2)}</p>
                    <p><strong>Min/Max:</strong> ${Math.min(...values).toFixed(2)} / ${Math.max(...values).toFixed(2)}</p>
                    <p><strong>Std Dev:</strong> ${stdDev.toFixed(2)}</p>
                </div>`;
        });
    }

    /**
     * Updates the text and disabled state of the pagination buttons.
     */
    function updatePaginationControls() {
        const totalPages = Math.ceil(filteredData.length / rowsPerPage);
        pageInfo.textContent = `Page ${currentPage} of ${totalPages || 1}`;
        prevPageBtn.disabled = currentPage === 1;
        nextPageBtn.disabled = currentPage === totalPages || totalPages === 0;
    }

    /**
     * Updates the sort indicator icons (▲/▼) in the table headers.
     */
    function updateSortIcons() {
        tableHeaders.forEach(header => {
            const icon = header.querySelector('.sort-icon');
            if (icon) {
                icon.textContent = header.dataset.column === sortColumn ? (sortDirection === 'asc' ? ' ▲' : ' ▼') : '';
            }
        });
    }


    // --- "WHAT-IF" SIMULATOR FUNCTIONS ---

    /**
     * Updates the displayed numerical values next to the simulator sliders.
     */
    function updateSimulatorUI() {
        if (!tempValue) return; // Exit if advanced section isn't loaded
        tempValue.textContent = parseFloat(tempSlider.value).toFixed(1);
        phValue.textContent = parseFloat(phSlider.value).toFixed(1);
        tdsValue.textContent = tdsSlider.value;
        turbValue.textContent = parseFloat(turbSlider.value).toFixed(1);
    }

    /**
     * Sends the current slider values to the server to get a predicted water quality.
     */
    async function runScenarioPrediction() {
        if (!tempSlider) return; // Exit if advanced section isn't loaded
        const scenarioData = { 
            temperature: tempSlider.value, 
            ph: phSlider.value, 
            tds: tdsSlider.value, 
            turbidity: turbSlider.value 
        };
        try {
            const response = await fetch('/analytics/predict_scenario', { 
                method: 'POST', 
                headers: { 'Content-Type': 'application/json' }, 
                body: JSON.stringify(scenarioData) 
            });
            if (!response.ok) throw new Error('Prediction request failed');
            const result = await response.json();
            
            // First, get the quality string from inside the nested object.
            const predictedQuality = result.predicted_quality.quality;

            // Now, use this correct string to update the UI.
            scenarioPrediction.textContent = predictedQuality;
            scenarioPrediction.className = `quality-badge quality-${predictedQuality.toLowerCase()}`;
        } catch (error) {
            console.error("Error running prediction:", error);
            scenarioPrediction.textContent = 'Error';
            scenarioPrediction.className = 'quality-badge quality-unknown';
        }
    }


    // --- REPORT EXPORTING FUNCTIONS ---

    /**
     * Exports the currently filtered data to a PDF file.
     */
    function exportToPDF() {
        const { jsPDF } = window.jspdf;
        const doc = new jsPDF();
        doc.text("BantayTubig - Historical Water Quality Report", 14, 16);
        doc.setFontSize(10);
        doc.text(`Date Range: ${primaryDatePicker.value}`, 14, 22);
        
        const tableColumn = ["Timestamp", "Temp (°C)", "pH", "TDS (ppm)", "Turbidity (NTU)", "Quality"];
        const tableRows = filteredData.map(item => [
            new Date(item.timestamp).toLocaleString(),
            isNaN(item.temperature) ? 'N/A' : item.temperature.toFixed(2),
            isNaN(item.ph) ? 'N/A' : item.ph.toFixed(2),
            isNaN(item.tds) ? 'N/A' : item.tds.toString(),
            isNaN(item.turbidity) ? 'N/A' : item.turbidity.toFixed(2),
            item.water_quality || 'Unknown'
        ]);

        doc.autoTable({ head: [tableColumn], body: tableRows, startY: 28 });
        doc.save(`BantayTubig_Report_${new Date().toISOString().split('T')[0]}.pdf`);
    }

    /**
     * Exports the currently filtered data to a CSV file.
     */
    function exportToCSV() {
        const csv = Papa.unparse(filteredData, { header: true });
        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement("a");
        link.href = URL.createObjectURL(blob);
        link.download = `BantayTubig_Report_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }


    // --- AI REASONING MODAL FUNCTIONS ---

    /**
     * Handles the click event for the "Generate AI Summary" button.
     * It shows the modal and fetches the reasoning from the server.
     */
    async function handleGenerateReasoning() {
        llmReasoningModal.style.display = 'flex';
        llmResultContainer.innerHTML = '';
        llmLoadingSpinner.style.display = 'block';

        try {
            const response = await fetch('/analytics/generate_reasoning', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    primary_range: primaryDatePicker.value,
                    comparison_range: compareDatePicker.value,
                    location: analysisLocation
                }),
            });

            if (!response.ok) throw new Error(`Server responded with status: ${response.status}`);
            
            const result = await response.json();
            
            // Clean the string by removing markdown code fences like ```html and ``` at the start/end.
            // Use a global regex (the 'g' flag) to remove all instances of ```html or ```
            const cleanedHtml = result.reasoning.replace(/`{3}(html)?\s*/g, '').trim();

            llmResultContainer.innerHTML = cleanedHtml;

        } catch (error) {
            console.error('Error fetching LLM reasoning:', error);
            llmResultContainer.innerHTML = `<p>Could not retrieve AI reasoning. Please try again later.</p><p><em>${error.message}</em></p>`;
        } finally {
            llmLoadingSpinner.style.display = 'none';
        }
    }

    /**
     * Closes the AI reasoning modal.
     */
    function closeModal() {
        llmReasoningModal.style.display = 'none';
    }


    // --- UTILITY FUNCTIONS ---

    /**
     * Parses a 12-hour time string (e.g., "09:30 AM") into an object with hours and minutes.
     * @param {string} timeString - The time string to parse.
     * @returns {{hours: number, minutes: number}|null}
     */
    function parse12HourTime(timeString) {
        if (!timeString) return null;
        const [time, meridian] = timeString.split(' ');
        let [hours, minutes] = time.split(':').map(Number);

        if (meridian.toUpperCase() === 'PM' && hours < 12) hours += 12;
        if (meridian.toUpperCase() === 'AM' && hours === 12) hours = 0; // Midnight case
        return { hours, minutes };
    }


    // --- EVENT LISTENERS ---

    /**
     * Attaches all necessary event listeners to the DOM elements.
     */
    function setupEventListeners() {
        // Filter change listeners
        checkboxes.forEach(cb => cb.addEventListener('change', updateChartData));
        qualityCheckboxes.forEach(cb => cb.addEventListener('change', () => processAndDisplayData('primary')));
        intervalSelector.addEventListener('change', () => processAndDisplayData('primary'));

        // Table sorting listener
        tableHeaders.forEach(header => header.addEventListener('click', (e) => {
            const newSortColumn = e.currentTarget.dataset.column;
            sortDirection = (sortColumn === newSortColumn && sortDirection === 'asc') ? 'desc' : 'asc';
            sortColumn = newSortColumn;
            processAndDisplayData('primary');
            updateSortIcons();
        }));

        // Pagination listeners
        prevPageBtn.addEventListener('click', () => { if (currentPage > 1) { currentPage--; renderTable(); } });
        nextPageBtn.addEventListener('click', () => { if (currentPage < Math.ceil(filteredData.length / rowsPerPage)) { currentPage++; renderTable(); } });

        // Export listeners
        exportPdfBtn.addEventListener('click', exportToPDF);
        exportCsvBtn.addEventListener('click', exportToCSV);
        
        // Advanced analytics toggle listener
        if (toggleAdvancedBtn) {
            toggleAdvancedBtn.addEventListener('click', () => {
                toggleAdvancedBtn.classList.toggle('open');
                advancedFeaturesContainer.style.display = toggleAdvancedBtn.classList.contains('open') ? 'flex' : 'none';
            });
        }

        // Simulator slider listeners
        [tempSlider, phSlider, tdsSlider, turbSlider].forEach(slider => {
            if (slider) {
                slider.addEventListener('input', updateSimulatorUI);
                slider.addEventListener('change', runScenarioPrediction);
            }
        });

        // AI Modal listeners
        if (generateReasoningBtn) generateReasoningBtn.addEventListener('click', handleGenerateReasoning);
        if (closeLlmModalBtn) closeLlmModalBtn.addEventListener('click', closeModal);
        if (llmReasoningModal) {
            llmReasoningModal.addEventListener('click', (event) => {
                if (event.target === llmReasoningModal) closeModal(); // Close if overlay is clicked
            });
        }
    }

    // --- SCRIPT EXECUTION START ---
    
    initializeCharts();
    initializePickers();
    fetchKeyDrivers();
    initializeSimulator();
    setupEventListeners();
});