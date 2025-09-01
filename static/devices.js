/**
 * ------------------------------------------------------------------------
 * UNIVERSAL SIDEBAR SCRIPT
 * ------------------------------------------------------------------------
 * This section contains the logic for the sidebar navigation menu,
 * which is intended to be used across all pages.
 */

/**
 * Sets up all event listeners and functionality for the sidebar navigation.
 */
function setupSidebar() {
    const sidebar = document.getElementById('sidebarMenu');
    const menuIcon = document.querySelector('.menu-icon');
    const sidebarLinks = document.querySelectorAll('.sidebar-menu a');

    /** Closes the sidebar and resets the menu icon on mobile. */
    const closeSidebar = () => {
        sidebar.classList.remove('open');
        if (window.innerWidth <= 992 && menuIcon.classList.contains('active')) {
            menuIcon.classList.remove('active');
            menuIcon.innerHTML = "&#9776;"; // Hamburger icon
        }
    };

    // Toggles the sidebar when the menu icon is clicked.
    menuIcon.addEventListener('click', (event) => {
        event.stopPropagation(); // Prevents the global click listener from immediately closing it.
        sidebar.classList.toggle('open');
        if (window.innerWidth <= 992) {
            menuIcon.classList.toggle('active');
            menuIcon.innerHTML = menuIcon.classList.contains('active') ? "&#10006;" : "&#9776;"; // Toggle between X and hamburger
        }
    });

    // Adds the 'active' class to a clicked link and closes the sidebar.
    sidebarLinks.forEach(link => {
        link.addEventListener('click', () => {
            sidebarLinks.forEach(l => l.classList.remove('active'));
            link.classList.add('active');
            closeSidebar();
        });
    });

    // Closes the sidebar if a click occurs outside of it.
    document.addEventListener('click', (event) => {
        if (!sidebar.contains(event.target) && !menuIcon.contains(event.target)) {
            closeSidebar();
        }
    });
}

// --- Toast Modal Elements & SVGs ---
const toastModal = document.getElementById('toastModal');
const toastIcon = document.getElementById('toastIcon');
const toastMessage = document.getElementById('toastMessage');

const svgSuccess = `<svg viewBox="0 0 24 24" fill="none" stroke="#28a745" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>`;
const svgConnecting = `<svg class="wifi-connecting-icon" viewBox="0 0 24 24" fill="none" stroke="#3498db" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.55a8 8 0 0 1 14.08 0"/><path d="M1.42 9a16 16 0 0 1 21.16 0"/><path d="M8.53 16.11a4 4 0 0 1 6.95 0"/><line x1="12" y1="20" x2="12.01" y2="20"/></svg>`;
const svgError = `<svg viewBox="0 0 24 24" fill="none" stroke="#dc3545" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>`;

/**
 * Displays a toast notification and hides it after a set duration.
 * This function is now globally available to any script loaded after this one.
 * @param {string} message The message to display.
 * @param {string} icon The SVG string for the icon.
 * @param {number} duration The time in milliseconds before the toast hides.
 */
function showToastModal(message, icon, duration = 3000) {
    if (!toastModal) {
        console.error('Toast modal element not found in the DOM.');
        return;
    }
    
    toastMessage.textContent = message;
    toastIcon.innerHTML = icon;

    toastModal.classList.add('show');

    setTimeout(() => {
        toastModal.classList.remove('show');
    }, duration);
}

/**
 * ------------------------------------------------------------------------
 * DEVICES PAGE SCRIPT
 * ------------------------------------------------------------------------
 * This script handles all functionality for the Device & Sensor Management page.
 */
document.addEventListener('DOMContentLoaded', function() {

    // --- GLOBAL STATE & CACHE ---
    let systemDeviceCache = null; // Caches the main device data to avoid repeated API calls.
    let map; // Holds the Leaflet map instance.
    let marker; // Holds the Leaflet map marker instance.
    let calibrationWizard = {}; // Holds the state for the multi-step calibration process.

    // --- DOM ELEMENT SELECTORS ---
    // Buttons
    const editDeviceBtn = document.getElementById('editDeviceBtn');
    const addLogBtn = document.getElementById('addLogBtn');
    
    // Modals
    const deviceModal = document.getElementById('deviceModal');
    const maintenanceLogModal = document.getElementById('maintenanceLogModal');
    const calibrationModal = document.getElementById('calibrationModal');
    const closeDeviceModalBtn = document.getElementById('closeDeviceModalBtn');
    const closeLogModalBtn = document.getElementById('closeLogModalBtn');
    const closeCalibrationModalBtn = document.getElementById('closeCalibrationModalBtn');
    
    // Forms
    const deviceForm = document.getElementById('deviceForm');
    const maintenanceLogForm = document.getElementById('maintenanceLogForm');

    // Device Form Inputs
    const deviceIdInput = document.getElementById('deviceId');
    const deviceNameInput = document.getElementById('deviceName');
    const deviceWaterSourceInput = document.getElementById('deviceWaterSource');
    const deviceProvinceSelect = document.getElementById('deviceProvince');
    const deviceMunicipalitySelect = document.getElementById('deviceMunicipality');
    const deviceLocationInput = document.getElementById('deviceLocation');

    // Log Form Inputs
    const technicianSelect = document.getElementById('technicianSelect');
    const logNotesSelect = document.getElementById('logNotesSelect');
    const logNotesOtherWrapper = document.getElementById('logNotesOtherWrapper');
    const logNotesTextarea = document.getElementById('logNotes');

    // Calibration Modal Title
    const calibrationModalTitle = document.getElementById('calibrationModalTitle');

    // --- TAB SWITCHING LOGIC ---
    const tabLinks = document.querySelectorAll('.tab-link');
    const tabContents = document.querySelectorAll('.tab-content');

    tabLinks.forEach(link => {
        link.addEventListener('click', () => {
            const tabId = link.dataset.tab;

            // Update active state on tab buttons
            tabLinks.forEach(l => l.classList.remove('active'));
            link.classList.add('active');

            // Show the correct tab content pane
            tabContents.forEach(content => {
                content.classList.remove('active');
                if (content.id === tabId) {
                    content.classList.add('active');
                }
            });
        });
    });

    // --- API & DATA FETCHING FUNCTIONS ---

    /**
     * Fetches the main system device data from the server and triggers the initial render.
     */
    async function fetchSystemDevice() {
        try {
            const response = await fetch('/api/system_device');
            if (!response.ok) throw new Error('Network response was not ok');
            systemDeviceCache = await response.json();
            renderDeviceStatus();
        } catch (error) {
            console.error("Failed to fetch system device info:", error);
            document.getElementById('system-details-card').innerHTML = '<p>Could not load system data.</p>';
        }
    }

    /**
     * Fetches all calibration dates for the current device.
     * @param {string} deviceId - The ID of the device.
     * @returns {Promise<Object>} A promise that resolves to an object mapping sensor types to their last calibration date.
     */
    async function fetchCalibrationsForDevice(deviceId) {
        try {
            const response = await fetch(`/api/devices/calibrations?deviceId=${deviceId}`);
            if (!response.ok) throw new Error('Could not fetch calibration data');
            return await response.json();
        } catch (error) {
            console.error(error);
            return {}; // Return an empty object on failure to prevent errors.
        }
    }

    /**
     * Fetches a list of users with 'technician' or 'admin' roles to populate the maintenance log dropdown.
     */
    async function loadTechnicians() {
        try {
            technicianSelect.innerHTML = '<option value="">Loading...</option>';
            const users = await fetch('/api/technicians').then(res => res.json());
            if (users.length > 0) {
                technicianSelect.innerHTML = '<option value="" hidden>Select a user</option>';
                users.forEach(user => {
                    const option = document.createElement('option');
                    option.value = user.id;
                    option.textContent = user.full_name;
                    technicianSelect.appendChild(option);
                });
            } else {
                technicianSelect.innerHTML = '<option value="">No eligible users found</option>';
            }
        } catch (error) {
            console.error("Failed to load technicians:", error);
            technicianSelect.innerHTML = '<option value="">Error loading users</option>';
        }
    }

    /**
     * Fetches a list of Philippine provinces from an external API.
     */
    async function loadProvinces() {
        try {
            const response = await fetch('https://psgc.gitlab.io/api/provinces/');
            const provinces = await response.json();
            deviceProvinceSelect.innerHTML = '<option value="">Select a province</option>';
            provinces.sort((a, b) => a.name.localeCompare(b.name));
            provinces.forEach(province => {
                const option = document.createElement('option');
                option.value = province.code;
                option.textContent = province.name;
                deviceProvinceSelect.appendChild(option);
            });
        } catch (error) {
            console.error("Failed to load provinces:", error);
            deviceProvinceSelect.innerHTML = '<option value="">Could not load provinces</option>';
        }
    }

    /**
     * Fetches a list of municipalities for a given province code from an external API.
     * @param {string} provinceCode - The PSGC code for the province.
     */
    async function loadMunicipalities(provinceCode) {
        if (!provinceCode) {
            deviceMunicipalitySelect.innerHTML = '<option value="">Select a province first</option>';
            deviceMunicipalitySelect.disabled = true;
            return;
        }
        try {
            deviceMunicipalitySelect.innerHTML = '<option value="">Loading...</option>';
            deviceMunicipalitySelect.disabled = false;
            const response = await fetch(`https://psgc.gitlab.io/api/provinces/${provinceCode}/municipalities/`);
            const municipalities = await response.json();
            deviceMunicipalitySelect.innerHTML = '<option value="">Select a municipality</option>';
            municipalities.sort((a, b) => a.name.localeCompare(b.name));
            municipalities.forEach(municipality => {
                const option = document.createElement('option');
                option.value = municipality.code;
                option.textContent = municipality.name;
                deviceMunicipalitySelect.appendChild(option);
            });
        } catch (error) {
            console.error("Failed to load municipalities:", error);
            deviceMunicipalitySelect.innerHTML = '<option value="">Could not load data</option>';
        }
    }

    /**
     * Fetches a live voltage reading for a specific sensor type from the device.
     * @param {string} sensorType - The type of sensor (e.g., 'pH', 'Temperature').
     * @returns {Promise<number|null>} The voltage reading, or null if an error occurs.
     */
    async function getLiveVoltage(sensorType) {
        try {
            const response = await fetch(`/api/live_sensor_data?sensorType=${sensorType}`);
            if (!response.ok) return null;
            const data = await response.json();
            return data.voltage;
        } catch (error) {
            console.error("Error fetching live voltage:", error);
            return null;
        }
    }


    // --- API SAVE/UPDATE FUNCTIONS ---

    /**
     * Saves the updated system device details to the server.
     * @param {Object} deviceData - The device data to save.
     */
    async function saveSystemDevice(deviceData) {
        try {
            const response = await fetch('/api/system_device/update', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(deviceData),
            });
            if (!response.ok) throw new Error('Failed to save device');
            await fetchSystemDevice(); // Re-fetch to update the UI with fresh data.
            deviceModal.style.display = 'none';
            showToastModal('Device details saved successfully!', svgSuccess);
        } catch (error) {
            console.error("Save device error:", error);
            showToastModal('Error: Could not save device details.', svgError, 5000);
        }
    }

    /**
     * Submits a new maintenance log entry to the server.
     * @param {Object} logData - The log data to save.
     */
    async function addLogEntry(logData) {
        try {
            const response = await fetch('/api/devices/log', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(logData),
            });
            if (!response.ok) throw new Error('Failed to add log');
            await fetchSystemDevice(); 

            showToastModal('Log added successfully!', svgSuccess);
            maintenanceLogModal.style.display = 'none';
        } catch(error) {
            console.error("Add log error:", error);
            showToastModal('Error: Could not add the log entry.', svgError, 5000);
        }
    }

    /**
     * Sends the collected calibration data to the server to calculate and save a new formula.
     * @returns {Promise<Object|null>} The result of the calculation, or null on error.
     */
    async function calculateAndSaveFormula() {
        try {
            const response = await fetch('/api/devices/calculate_calibration', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    deviceId: systemDeviceCache.id,
                    sensorType: calibrationWizard.sensorType,
                    points: calibrationWizard.collectedData
                })
            });
            if (!response.ok) throw new Error('Calculation failed');
            await fetchSystemDevice(); // Refresh data to get new calibration date.
            return await response.json();
        } catch (error) {
            console.error("Error calculating formula:", error);
            return null;
        }
    }

    /**
     * Sends a request to the server to restore a sensor's default calibration formula.
     * @param {string} sensorType - The sensor to restore.
     */
    async function restoreDefaults(sensorType) {
        if (!confirm(`Are you sure you want to restore the default calibration for the ${sensorType} sensor? This will delete the current custom calibration.`)) return;
        try {
            await fetch('/api/devices/restore_default_calibration', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ deviceId: systemDeviceCache.id, sensorType: sensorType })
            });
            await fetchSystemDevice(); // Refresh the UI to show the change.
            showToastModal('Default calibration restored successfully!', svgSuccess);
        } catch (error) {
            console.error("Error restoring defaults:", error);
            showToastModal('Could not restore default calibration. Please try again.', svgError, 5000);
        }
    }


    // --- UI RENDERING & MODAL FUNCTIONS ---

    /**
     * Populates the entire page with data from the `systemDeviceCache`.
     */
    async function renderDeviceStatus() {
        if (!systemDeviceCache) return;
        
        // Populate System Details Card
        document.getElementById('deviceIdDisplay').textContent = systemDeviceCache.id;
        document.getElementById('deviceNameDisplay').textContent = systemDeviceCache.name;
        document.getElementById('deviceFirmwareDisplay').textContent = systemDeviceCache.firmware;
        document.getElementById('deviceWaterSourceDisplay').textContent = systemDeviceCache.water_source || 'Not set';
        const statusSpan = document.getElementById('deviceStatusDisplay');
        statusSpan.textContent = systemDeviceCache.status;
        statusSpan.className = `status-indicator status-${systemDeviceCache.status.toLowerCase()}`;
        
        // Parse and display location information.
        const locationDisplay = document.getElementById('deviceLocationDisplay');
        try {
            const locationData = JSON.parse(systemDeviceCache.location);
            locationDisplay.textContent = `${locationData.coordinates}, ${locationData.municipality}, ${locationData.province}`;
        } catch (e) {
            locationDisplay.textContent = systemDeviceCache.location || 'Not set'; // Fallback for old format
        }

        // Populate Sensor List Card
        const sensorListContainer = document.getElementById('sensorList');
        sensorListContainer.innerHTML = '';
        const calibrationDates = await fetchCalibrationsForDevice(systemDeviceCache.id);

        if (systemDeviceCache.sensors && systemDeviceCache.sensors.length > 0) {
            systemDeviceCache.sensors.forEach(sensor => {
                const item = document.createElement('div');
                item.className = 'sensor-item';
                const calDate = calibrationDates[sensor.type];
                
                item.innerHTML = `
                    <div class="sensor-item-header">
                        <h4>${sensor.type}</h4>
                        <span class="live-value">${sensor.last_value ? sensor.last_value.toFixed(2) : '0.00'}</span>
                    </div>
                    <div class="sensor-item-footer">
                        <p>${calDate ? `Last Calibrated: ${new Date(calDate).toLocaleString()}` : 'Using default calibration'}</p>
                        <div class="sensor-item-actions">
                            ${calDate ? `<button class="action-button small restore-defaults-btn" data-sensor-type="${sensor.type}">Restore</button>` : ''}
                            <button class="action-button small calibrate-btn" data-sensor-type="${sensor.type}">Calibrate</button>
                        </div>
                    </div>
                `;
                sensorListContainer.appendChild(item);
            });
        } else {
            sensorListContainer.innerHTML = '<p>No sensor data available.</p>';
        }

        // Populate Maintenance Log Card
        const logContainer = document.getElementById('maintenanceLog');
        logContainer.innerHTML = '';
        if (systemDeviceCache.logs && systemDeviceCache.logs.length > 0) {
            systemDeviceCache.logs.forEach(log => {
                const item = document.createElement('div');
                item.className = 'log-item';
                item.innerHTML = `
                    <div class="log-item-header">
                        <h4>${log.tech}</h4>
                        <span>${new Date(log.date).toLocaleString()}</span>
                    </div>
                    <p>${log.notes}</p>
                `;
                logContainer.appendChild(item);
            });
        } else {
            logContainer.innerHTML = '<p>No maintenance logs recorded.</p>';
        }
    }

    /**
     * Opens the "Edit System Details" modal and populates it with the current device data.
     */
    async function openEditModal() {
        if (!systemDeviceCache) return;

        // Populate form fields
        deviceIdInput.value = systemDeviceCache.id;
        deviceNameInput.value = systemDeviceCache.name;
        deviceWaterSourceInput.value = systemDeviceCache.water_source;
        
        let savedLocation = {};
        try {
            savedLocation = JSON.parse(systemDeviceCache.location) || {};
        } catch (e) {
            savedLocation = { coordinates: systemDeviceCache.location }; // Fallback
        }
        deviceLocationInput.value = savedLocation.coordinates || '';
        
        // Asynchronously load and set location dropdowns.
        await loadProvinces();
        const provinceOption = Array.from(deviceProvinceSelect.options).find(opt => opt.text === savedLocation.province);
        if (provinceOption) {
            deviceProvinceSelect.value = provinceOption.value;
            await loadMunicipalities(provinceOption.value);
            const municipalityOption = Array.from(deviceMunicipalitySelect.options).find(opt => opt.text === savedLocation.municipality);
            if (municipalityOption) {
                deviceMunicipalitySelect.value = municipalityOption.value;
            }
        }
        
        // Initialize map with saved or default coordinates.
        let [lat, lng] = [14.2834, 122.6885]; // Default location
        if (savedLocation.coordinates && savedLocation.coordinates.includes(',')) {
            [lat, lng] = savedLocation.coordinates.split(',').map(parseFloat);
        }
        
        deviceModal.style.display = 'flex';
        setTimeout(() => showMapInModal(lat, lng), 50); // Delay to ensure modal is visible before map init.
    }


    // --- MAP & GEOLOCATION FUNCTIONS ---

    /**
     * Initializes or re-initializes the Leaflet map in the edit modal.
     * @param {number} lat - Initial latitude.
     * @param {number} lng - Initial longitude.
     */
    function showMapInModal(lat, lng) {
        if (map) map.remove(); // Remove previous map instance if it exists.
        map = L.map('map-container').setView([lat, lng], 14);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap'
        }).addTo(map);
        marker = L.marker([lat, lng], { draggable: true }).addTo(map);
        
        const updateInput = () => {
            const latLng = marker.getLatLng();
            deviceLocationInput.value = `${latLng.lat.toFixed(6)}, ${latLng.lng.toFixed(6)}`;
        };

        marker.on('dragend', updateInput);
        map.on('click', (e) => {
            marker.setLatLng(e.latlng);
            updateInput();
        });
        updateInput(); // Set initial value.
    }

    /**
     * Uses an external API to get coordinates for a selected municipality and updates the map.
     * @param {string} provinceName - The name of the province.
     * @param {string} municipalityName - The name of the municipality.
     */
    async function geocodeAndUpdateMap(provinceName, municipalityName) {
        if (!provinceName || !municipalityName) return;
        try {
            const query = encodeURIComponent(`${municipalityName}, ${provinceName}, Philippines`);
            const response = await fetch(`https://nominatim.openstreetmap.org/search?q=${query}&format=json&limit=1`);
            const data = await response.json();
            if (data.length > 0) {
                const lat = parseFloat(data[0].lat);
                const lon = parseFloat(data[0].lon);
                deviceLocationInput.value = `${lat.toFixed(6)}, ${lon.toFixed(6)}`;
                map.setView([lat, lon], 13);
                marker.setLatLng([lat, lon]);
            }
        } catch (error) {
            console.error("Geocoding failed:", error);
        }
    }


    // --- CALIBRATION WIZARD FUNCTIONS ---

    /**
     * Starts the multi-step calibration process for a given sensor.
     * @param {string} sensorType - The sensor to calibrate.
     */
    function startCalibrationWizard(sensorType) {
        calibrationWizard = {
            sensorType: sensorType,
            bufferPoints: [],
            collectedData: [],
            currentStep: 0,
            timer: null
        };
        calibrationModalTitle.textContent = `Calibrate ${sensorType} Sensor`;
        updateCalibrationModalUI();
        calibrationModal.style.display = 'flex';
    }

    /**
     * Renders the content of the calibration modal based on the current step in the wizard.
     */
    function updateCalibrationModalUI() {
        const body = calibrationModal.querySelector('.modal-body');
        const wizard = calibrationWizard;

        switch (wizard.currentStep) {
            case 0: // Introduction
                body.innerHTML = `
                    <h3>Multi-Point Calibration</h3>
                    <p>This wizard will guide you through calibrating the <strong>${wizard.sensorType}</strong> sensor. You will need at least two standard buffer solutions (e.g., pH 4.0, pH 7.0).</p>
                    <p><b>Do you have your buffer solutions ready?</b></p>
                    <div class="form-actions">
                        <button id="cal-start-btn" class="action-button">Yes, Start Calibration</button>
                    </div>
                `;
                document.getElementById('cal-start-btn').onclick = () => {
                    wizard.currentStep = 1;
                    updateCalibrationModalUI();
                };
                break;

            case 1: // Enter Buffer Values
                body.innerHTML = `
                    <h3>Step 1: Enter Buffer Values</h3>
                    <p>Enter the known values of your buffer solutions, separated by commas (e.g., 4.01, 7.0, 10.0).</p>
                    <div class="form-group">
                        <input type="text" id="buffer-values-input" placeholder="4.01, 7.0, 10.0">
                    </div>
                    <div class="form-actions">
                        <button id="cal-buffers-next" class="action-button">Next</button>
                    </div>
                `;
                document.getElementById('cal-buffers-next').onclick = () => {
                    const input = document.getElementById('buffer-values-input').value;
                    wizard.bufferPoints = input.split(',').map(v => parseFloat(v.trim())).filter(v => !isNaN(v));
                    if (wizard.bufferPoints.length < 2) {
                        showToastModal('Please enter at least two valid buffer values.', svgError, 5000);
                        return;
                    }
                    wizard.currentStep = 2;
                    updateCalibrationModalUI();
                };
                break;

            case 2: // Soaking and Analysis Loop
                const bufferValue = wizard.bufferPoints[wizard.collectedData.length];
                body.innerHTML = `
                    <h3>Step 2: Analysis (${wizard.collectedData.length + 1}/${wizard.bufferPoints.length})</h3>
                    <p>Place the sensor in the <strong>${bufferValue.toFixed(2)}</strong> buffer solution and wait for the reading to stabilize.</p>
                    <p>The system will analyze the sensor output for 30 seconds.</p>
                    <div class="progress-bar-container"><div id="cal-progress-bar"></div></div>
                    <p>Live Voltage: <strong id="live-voltage-display">Reading...</strong></p>
                    <div class="form-actions">
                        <button id="cal-soak-start" class="action-button">Start Analysis</button>
                    </div>
                `;
                document.getElementById('cal-soak-start').onclick = (e) => {
                    e.target.disabled = true;
                    e.target.textContent = "Analyzing...";
                    runCalibrationAnalysis(bufferValue);
                };
                break;
            
            case 3: // Final Confirmation
                body.innerHTML = `
                    <h3>Calibration Complete!</h3>
                    <p>The new calibration formula has been calculated and saved. The system will now use this formula for all future readings.</p>
                    <div class="form-actions">
                        <button id="cal-finish-btn" class="action-button">Finish</button>
                    </div>
                `;
                document.getElementById('cal-finish-btn').onclick = () => {
                    calibrationModal.style.display = 'none';
                };
                break;
        }
    }

    /**
     * Runs the 30-second analysis for a single calibration point.
     * @param {number} bufferValue - The known value of the buffer solution.
     */
    function runCalibrationAnalysis(bufferValue) {
        let readings = [];
        let duration = 30; // 30 seconds
        let elapsed = 0;
        const progressBar = document.getElementById('cal-progress-bar');
        const voltageDisplay = document.getElementById('live-voltage-display');

        calibrationWizard.timer = setInterval(async () => {
            elapsed++;
            progressBar.style.width = `${(elapsed / duration) * 100}%`;

            const voltage = await getLiveVoltage(calibrationWizard.sensorType);
            if (voltage !== null) {
                voltageDisplay.textContent = `${voltage.toFixed(3)} V`;
                readings.push(voltage);
            } else {
                voltageDisplay.textContent = "Error";
            }

            if (elapsed >= duration) {
                clearInterval(calibrationWizard.timer);
                // Average the last half of the readings for stability.
                const stableReadings = readings.slice(Math.floor(readings.length / 2));
                const avgVoltage = stableReadings.reduce((a, b) => a + b, 0) / stableReadings.length;
                
                calibrationWizard.collectedData.push({ buffer: bufferValue, voltage: avgVoltage });

                // ... inside runCalibrationAnalysis function
                // If more points need to be collected, go back to the analysis step.
                if (calibrationWizard.collectedData.length < calibrationWizard.bufferPoints.length) {
                    calibrationWizard.currentStep = 2; // Corrected
                    showToastModal('New sensor calibration saved successfully!', svgSuccess);
                    updateCalibrationModalUI();
                } else {
                    // Otherwise, calculate and save the final formula.
                    const result = await calculateAndSaveFormula();
                    if (result) {
                        calibrationWizard.currentStep = 3; // Corrected
                        showToastModal('New sensor calibration saved successfully!', svgSuccess);
                        updateCalibrationModalUI();
                    } else {
                        showToastModal('An error occurred while saving the calibration. Please try again.', svgError, 5000);
                    }
                }
            }
        }, 1000);
    }


    // --- EVENT HANDLERS ---

    /** Handles the submission of the "Edit System Details" form. */
    function handleDeviceFormSubmit(e) {
        e.preventDefault();
        const selectedProvince = deviceProvinceSelect.options[deviceProvinceSelect.selectedIndex];
        const selectedMunicipality = deviceMunicipalitySelect.options[deviceMunicipalitySelect.selectedIndex];
        
        const locationObject = {
            province: selectedProvince ? selectedProvince.text : "",
            municipality: selectedMunicipality ? selectedMunicipality.text : "",
            coordinates: deviceLocationInput.value
        };

        saveSystemDevice({
            deviceId: deviceIdInput.value,
            deviceName: deviceNameInput.value,
            deviceWaterSource: deviceWaterSourceInput.value,
            deviceLocation: JSON.stringify(locationObject),
        });
    }
    
    /** Handles the submission of the "Add Maintenance Log" form. */
    function handleMaintenanceLogSubmit(e) {
        e.preventDefault();
        if (!systemDeviceCache) return showToastModal('Device data not loaded yet.', svgError, 5000);

        const finalLogNotes = logNotesSelect.value === 'Other' ? logNotesTextarea.value : logNotesSelect.value;
        addLogEntry({
            deviceId: systemDeviceCache.id,
            userId: technicianSelect.value,
            logNotes: finalLogNotes,
        });
    }

    
    // --- EVENT LISTENER SETUP ---

    // Modal Open/Close Buttons
    editDeviceBtn.addEventListener('click', openEditModal);
    addLogBtn.addEventListener('click', () => {
        maintenanceLogForm.reset();
        loadTechnicians();
        logNotesOtherWrapper.style.display = 'none';
        logNotesTextarea.required = false;
        maintenanceLogModal.style.display = 'flex';
    });
    closeDeviceModalBtn.addEventListener('click', () => {
        deviceModal.style.display = 'none';
        if (map) { map.remove(); map = null; }
    });
    closeLogModalBtn.addEventListener('click', () => maintenanceLogModal.style.display = 'none');
    closeCalibrationModalBtn.addEventListener('click', () => {
        if (calibrationWizard && calibrationWizard.timer) {
            clearInterval(calibrationWizard.timer); // Stop any running timers.
        }
        calibrationModal.style.display = 'none';
    });

    // Form Submissions
    deviceForm.addEventListener('submit', handleDeviceFormSubmit);
    maintenanceLogForm.addEventListener('submit', handleMaintenanceLogSubmit);

    // Dynamic Form Behavior
    logNotesSelect.addEventListener('change', () => {
        const isOther = logNotesSelect.value === 'Other';
        logNotesOtherWrapper.style.display = isOther ? 'block' : 'none';
        logNotesTextarea.required = isOther;
    });

    // Location Dropdown Listeners
    deviceProvinceSelect.addEventListener('change', () => loadMunicipalities(deviceProvinceSelect.value));
    deviceMunicipalitySelect.addEventListener('change', () => {
        const provinceName = deviceProvinceSelect.options[deviceProvinceSelect.selectedIndex].text;
        const municipalityName = deviceMunicipalitySelect.options[deviceMunicipalitySelect.selectedIndex].text;
        geocodeAndUpdateMap(provinceName, municipalityName);
    });
    
    // Event delegation for buttons inside the dynamically generated sensor list.
    document.getElementById('sensorList').addEventListener('click', (e) => {
        const target = e.target;
        if (target) {
            if (target.classList.contains('calibrate-btn')) {
                startCalibrationWizard(target.dataset.sensorType);
            } else if (target.classList.contains('restore-defaults-btn')) {
                restoreDefaults(target.dataset.sensorType);
            }
        }
    });

    // --- INITIALIZATION ---
    setupSidebar();
    fetchSystemDevice();
});
