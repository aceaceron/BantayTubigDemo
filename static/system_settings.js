// static/system_settings.js

/**
 * ------------------------------------------------------------------------
 * UNIVERSAL SIDEBAR & HEADER SCRIPT
 * This function sets up the event listeners for the mobile-friendly
 * sidebar navigation menu.
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

// --- Reusable Confirmation Modal ---
    const confirmationModal = document.getElementById('confirmationModal');
    const confirmationModalTitle = document.getElementById('confirmationModalTitle');
    const confirmationModalText = document.getElementById('confirmationModalText');
    const closeConfirmationModalBtn = document.getElementById('closeConfirmationModalBtn');
    let confirmationConfirmBtn = document.getElementById('confirmationConfirmBtn'); // Use let
    const confirmationCancelBtn = document.getElementById('confirmationCancelBtn');

    /**
     * Shows a confirmation modal and executes a callback if the user confirms.
     * @param {string} title - The title for the modal.
     * @param {string} text - The descriptive text for the modal.
     * @param {function} onConfirm - The function to execute if the user clicks "Confirm".
     */
    function showConfirmationModal(title, text, onConfirm) {
        if (!confirmationModal) {
            console.error("Confirmation modal HTML is missing. Falling back to default confirm.");
            if (confirm(`${title}\n${text}`)) {
                onConfirm();
            }
            return;
        }
        
        confirmationModalTitle.textContent = title;
        confirmationModalText.textContent = text;
        
        const newConfirmBtn = confirmationConfirmBtn.cloneNode(true);
        confirmationConfirmBtn.parentNode.replaceChild(newConfirmBtn, confirmationConfirmBtn);
        confirmationConfirmBtn = newConfirmBtn;
        
        confirmationConfirmBtn.addEventListener('click', () => {
            onConfirm();
            confirmationModal.style.display = 'none';
        });

        confirmationCancelBtn.onclick = () => confirmationModal.style.display = 'none';
        closeConfirmationModalBtn.onclick = () => confirmationModal.style.display = 'none';
        confirmationModal.style.display = 'flex';
    }

/**
 * ------------------------------------------------------------------------
 * API FETCH HELPER
 * A reusable function to make requests to the backend API and handle
 * responses and errors consistently.
 * ------------------------------------------------------------------------
 */
async function apiFetch(url, options = {}) {
    try {
        const response = await fetch(url, options);
        const data = await response.json();
        if (!response.ok) throw new Error(data.message || `HTTP error! status: ${response.status}`);
        return data;
    } catch (error) {
        console.error('API Fetch Error:', error);
        showToastModal(`Error: ${error.message}`, svgError, 5000); 
        throw error;
    }
}

/**
 * ------------------------------------------------------------------------
 * SYSTEM SETTINGS PAGE SCRIPT
 * This function contains all the logic specific to the system_settings.html page.
 * ------------------------------------------------------------------------
 */
function setupSettingsPage() {
    
    // --- ACCORDION UI LOGIC ---
    const accordionButtons = document.querySelectorAll('.settings-toggle-btn');
    accordionButtons.forEach(button => {
        button.addEventListener('click', () => {
            button.classList.toggle('active');
            const contentPanel = button.nextElementSibling;
            if (contentPanel.style.maxHeight) {
                contentPanel.style.maxHeight = null;
            } else {
                contentPanel.style.maxHeight = "100%";
            }
        });
    });

    // --- STATE MANAGEMENT ---
    let previewData = { full: [], filtered: [] };
    let previewCurrentPage = 1;
    const previewRowsPerPage = 5;
    let previewSort = { column: 'timestamp', direction: 'desc' };

    // <<< --- ELEMENT SELECTORS --- >>>

    // General & Floating Actions
    const saveBtn = document.getElementById('saveSettingsBtn');
    const powerOffBtn = document.getElementById('powerOffBtn');
    const systemNameInput = document.getElementById('systemName');

    // Security & Account
    const changePasswordForm = document.getElementById('changePasswordForm');
    const currentPasswordInput = document.getElementById('currentPassword');
    const newPasswordInput = document.getElementById('newPassword');
    const confirmPasswordInput = document.getElementById('confirmPassword');

    // UI & Display
    const showMlConfidenceToggle = document.getElementById('showMlConfidenceToggle');

    // Network & Connectivity
    const scanWifiBtn = document.getElementById('scanWifiBtn');
    const wifiListBody = document.getElementById('wifiListBody');
    const networkStatusContent = document.getElementById('networkStatusContent');
    const wifiModal = document.getElementById('wifiPasswordModal');
    const closeWifiModalBtn = document.getElementById('closeWifiModalBtn');
    const wifiConnectForm = document.getElementById('wifiConnectForm');
    const ssidNameLabel = document.getElementById('ssidNameLabel');
    const wifiSsidInput = document.getElementById('wifiSsidInput');
    const wifiPasswordInput = document.getElementById('wifiPasswordInput');

    // Universal Toast Notifications
    const toastModal = document.getElementById('toastModal');
    const toastIcon = document.getElementById('toastIcon');
    const toastMessage = document.getElementById('toastMessage');

    // --- SVG Icon Definitions ---
    // These constants store SVG markup as strings. This is an efficient method
    // that avoids loading separate image files and allows for easy styling and
    // dynamic rendering in the user interface.
    // Icon for ongoing operations, like an API call.
    const svgLoader = `<svg class="svg-loader" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg>`;
    // Icon for buttons that trigger a refresh or scan, like the "Scan WiFi" button.
    const svgSync = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M23 4v6h-6"/><path d="M1 20v-6h6"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>`;
    // Icon for success notifications, shown in a green toast modal.
    const svgSuccess = `<svg viewBox="0 0 24 24" fill="none" stroke="#28a745" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>`;
    // Icon for when the device is attempting to connect to a network.
    const svgConnecting = `<svg class="wifi-connecting-icon" viewBox="0 0 24 24" fill="none" stroke="#3498db" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.55a8 8 0 0 1 14.08 0"/><path d="M1.42 9a16 16 0 0 1 21.16 0"/><path d="M8.53 16.11a4 4 0 0 1 6.95 0"/><line x1="12" y1="20" x2="12.01" y2="20"/></svg>`;
    // Icon for error notifications, shown in a red toast modal.
    const svgError = `<svg viewBox="0 0 24 24" fill="none" stroke="#dc3545" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>`;
    // Icon for the system shutdown button.
    const svgPower = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18.36 6.64a9 9 0 1 1-12.73 0"></path><line x1="12" y1="2" x2="12" y2="12"></line></svg>`;
        
    // --- DATA FETCHING & SAVING LOGIC ---
    async function loadDeviceSettings() {
        try {
            const data = await apiFetch('/api/system/settings');
            if (systemNameInput) systemNameInput.value = data.systemName;
            if (showMlConfidenceToggle) showMlConfidenceToggle.checked = (data.showMlConfidence === 'true');
        } catch (error) {
            console.error("Could not load system settings:", error);
        }
    }

    if (saveBtn) {
        saveBtn.addEventListener('click', async () => {
            saveBtn.classList.add('saving');

            try {
                // Step 1: Save the new setting to the database
                const settingsData = {
                    systemName: systemNameInput.value,
                    showMlConfidence: showMlConfidenceToggle.checked
                };
                localStorage.setItem('showMlConfidence', showMlConfidenceToggle.checked);
                await apiFetch('/api/system/settings', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(settingsData)
                });

            } catch (error) {
                // Error is handled by apiFetch
            } finally {
                setTimeout(() => {
                    saveBtn.classList.remove('saving');
                }, 1500);
                showToastModal('Settings saved!', svgSuccess);
            }
        });
    }

    function loadUiSettings() {
        const savedSettings = localStorage.getItem('bantayTubigUiSettings');
        if (savedSettings) {
            const settings = JSON.parse(savedSettings);
            const sessionTimeoutEl = document.getElementById('sessionTimeout');
            if(sessionTimeoutEl) sessionTimeoutEl.value = settings.sessionTimeout || '15';
            const dataRetentionEl = document.getElementById('dataRetention');
            if(dataRetentionEl) dataRetentionEl.value = settings.dataRetention || '365';
        }
    }
    
    // --- NETWORK & CONNECTIVITY LOGIC ---
    function renderSignalIndicator(signal) {
        let colorClass = 'signal-weak';
        if (signal > 75) colorClass = 'signal-excellent';
        else if (signal > 50) colorClass = 'signal-good';
        else if (signal > 25) colorClass = 'signal-ok';
        const bar1Opacity = signal > 0 ? 1 : 0.2;
        const bar2Opacity = signal > 25 ? 1 : 0.2;
        const bar3Opacity = signal > 50 ? 1 : 0.2;
        const bar4Opacity = signal > 75 ? 1 : 0.2;
        const svgIcon = `<svg class="signal-svg ${colorClass}" viewBox="0 0 24 24" fill="currentColor"><path d="M12 4C7.31 4 3.07 5.9 0 8.98L12 21l12-12.02C20.93 5.9 16.69 4 12 4z" opacity="${bar1Opacity}"/><path d="M12 9c-2.31 0-4.43.7-6.24 1.98L12 18l6.24-7.02C16.43 9.7 14.31 9 12 9z" opacity="${bar2Opacity}"/><path d="M12 14c-1.15 0-2.2.35-3.12.99L12 15l3.12-1.01C14.2 14.35 13.15 14 12 14z" opacity="${bar3Opacity}"/><circle cx="12" cy="18" r="2" opacity="${bar4Opacity}"/></svg>`;
        return `${svgIcon} ${signal}%`;
    }

    async function getNetworkStatus() {
        if (!networkStatusContent) return;
        try {
            const data = await apiFetch('/api/system/network/status');
            const statusBadge = networkStatusContent.querySelector('.status-badge');
            const currentSsid = document.getElementById('currentSsid');
            const currentIp = document.getElementById('currentIp');
            
            if (data.status === 'connected') {
                statusBadge.textContent = 'Connected';
                statusBadge.className = 'status-badge status-connected';
                currentSsid.textContent = data.connected_ssid;
                currentIp.textContent = data.ip_address;
            } else {
                statusBadge.textContent = 'Disconnected';
                statusBadge.className = 'status-badge status-disconnected';
                currentSsid.textContent = 'N/A';
                currentIp.textContent = 'N/A';
            }
        } catch (error) { /* Fail silently */ }
    }

    if (scanWifiBtn) {
        const iconPlaceholder = scanWifiBtn.querySelector('.button-icon-placeholder');
        iconPlaceholder.innerHTML = svgSync; // Set initial icon
        scanWifiBtn.addEventListener('click', async () => {
            scanWifiBtn.disabled = true;
            iconPlaceholder.innerHTML = svgLoader; // Set loading icon
            wifiListBody.innerHTML = `<tr><td colspan="4">Scanning... Please wait.</td></tr>`;
            try {
                const networks = await apiFetch('/api/system/network/scan', { method: 'POST' });
                wifiListBody.innerHTML = '';
                if (networks.length === 0) {
                    wifiListBody.innerHTML = `<tr><td colspan="4">No networks found.</td></tr>`;
                } else {
                    networks.forEach(net => {
                        const tr = document.createElement('tr');
                        
                        // **MODIFIED CODE BLOCK**
                        tr.innerHTML = `
                            <td>${net.in_use ? '<strong>' + net.ssid + '</strong>' : net.ssid}</td>
                            <td>${renderSignalIndicator(net.signal)}</td>
                            <td>${net.security}</td>
                            <td>
                                ${net.in_use 
                                    ? '<span class="connected-label">Connected</span>' 
                                    : `<button class="action-button small connect-btn" data-ssid="${net.ssid}" data-security="${net.security}">Connect</button>`
                                }
                            </td>
                        `;
                        wifiListBody.appendChild(tr);
                    });
                }
            } catch (error) {
                wifiListBody.innerHTML = `<tr><td colspan="4">Error scanning for networks.</td></tr>`;
            } finally {
                scanWifiBtn.disabled = false;
                iconPlaceholder.innerHTML = svgSync; // Restore initial icon
            }
        });
    }

    if (wifiListBody) {
        wifiListBody.addEventListener('click', (e) => {
            if (e.target.classList.contains('connect-btn')) {
                const ssid = e.target.dataset.ssid;
                const security = e.target.dataset.security;
                if (security === 'Open') {
                    handleWifiConnect(ssid, '');
                } else {
                    ssidNameLabel.textContent = ssid;
                    wifiSsidInput.value = ssid;
                    wifiPasswordInput.value = '';
                    wifiModal.style.display = 'flex';
                    wifiPasswordInput.focus();
                }
            }
        });
    }
    
    if (wifiConnectForm) {
        wifiConnectForm.addEventListener('submit', (e) => {
            e.preventDefault();
            handleWifiConnect(wifiSsidInput.value, wifiPasswordInput.value);
        });
    }

    // --- NETWORK & CONNECTIVITY LOGIC ---
    async function handleWifiConnect(ssid, password) {
        if (wifiModal) wifiModal.style.display = 'none';
        showToastModal(`Attempting to connect to ${ssid}...`, svgConnecting, 10000); // Show for 10 seconds
        try {
            const result = await apiFetch('/api/system/network/connect', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ssid, password })
            });
            showToastModal(result.message, svgSuccess, 5000);
            setTimeout(() => {
                getNetworkStatus();
                if (scanWifiBtn) scanWifiBtn.click();
            }, 10000);
        } catch (error) { /* Handled by apiFetch */ }
    }
    
    if (closeWifiModalBtn) {
        closeWifiModalBtn.addEventListener('click', () => wifiModal.style.display = 'none');
    }

    // --- TOAST MODAL FUNCTION ---
    function showToastModal(message, icon, duration = 3000) {
        if (!toastModal) return; // Exit if modal isn't on the page
        
        toastMessage.textContent = message;
        toastIcon.innerHTML = icon;

        toastModal.classList.add('show');

        setTimeout(() => {
            toastModal.classList.remove('show');
        }, duration);
    }

    // --- SETUP EVENT LISTENERS (add these inside the function) ---

    if (changePasswordForm) {
        changePasswordForm.addEventListener('submit', async (e) => {
            e.preventDefault(); // Prevent the default browser form submission

            const currentPassword = currentPasswordInput.value;
            const newPassword = newPasswordInput.value;
            const confirmPassword = confirmPasswordInput.value;

            // --- Client-side validation ---
            if (newPassword.length < 6) {
                showToastModal('New password must be at least 6 characters long.', svgError);
                return;
            }
            if (newPassword !== confirmPassword) {
                showToastModal('New passwords do not match.', svgError);
                return;
            }

            try {
                const result = await apiFetch('/api/users/change_password', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        current_password: currentPassword,
                        new_password: newPassword
                    })
                });
                showToastModal(result.message, svgSuccess);
                changePasswordForm.reset(); // Clear the form fields on success
            } catch (error) {
                // The apiFetch helper already shows a toast for errors
                console.error('Password change failed:', error);
            }
        });
    }

    // --- POWER OFF LOGIC ---
    // Handles the device shutdown process.
    if (powerOffBtn) {
        powerOffBtn.addEventListener('click', () => {
            showConfirmationModal(
                'Shut Down System?',
                'The device will power off and the application will become unresponsive. This action requires a physical restart.',
                () => { // This function runs only if the user clicks "Confirm"
                    powerOffBtn.disabled = true;
                    if (saveBtn) saveBtn.disabled = true;

                    showToastModal('System will power off shortly.', svgPower, 10000);

                    fetch('/api/system/power-off', { method: 'POST' })
                        .catch(error => {
                            console.log("Shutdown initiated. Server connection lost as expected.");
                        });
                }
            );
        });
    }

    // --- INITIAL DATA LOADS ---
    loadDeviceSettings();
    loadUiSettings();
    getNetworkStatus();
    if (scanWifiBtn) scanWifiBtn.click();
}

// --- SCRIPT EXECUTION START ---
document.addEventListener('DOMContentLoaded', function() {
    setupGlobalNavigation();
    setupSettingsPage();
});
