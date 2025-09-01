// static/setup.js

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

document.addEventListener('DOMContentLoaded', function() {

    // --- ELEMENT SELECTORS ---
    const scanWifiBtn = document.getElementById('scanWifiBtn');
    const wifiListBody = document.getElementById('wifiListBody');
    const wifiModal = document.getElementById('wifiPasswordModal');
    const closeWifiModalBtn = document.getElementById('closeWifiModalBtn');
    const wifiConnectForm = document.getElementById('wifiConnectForm');
    const ssidNameLabel = document.getElementById('ssidNameLabel');
    const wifiSsidInput = document.getElementById('wifiSsidInput');
    const wifiPasswordInput = document.getElementById('wifiPasswordInput');
    
    // Status message elements
    const statusContainer = document.getElementById('statusMessageContainer');
    const statusTitle = document.getElementById('statusTitle');
    const statusText = document.getElementById('statusText');

    // --- SVG Icon Definitions ---
    const svgLoader = `<svg class="svg-loader" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg>`;
    const svgSync = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M23 4v6h-6"/><path d="M1 20v-6h6"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>`;

    /**
     * A helper function to fetch data from the API and handle errors.
     * @param {string} url The API endpoint to fetch.
     * @param {object} options The options for the fetch request.
     * @returns {Promise<any>} The JSON response from the API.
     */
    async function apiFetch(url, options = {}) {
        try {
            const response = await fetch(url, options);
            const data = await response.json();
            if (!response.ok) throw new Error(data.message || `HTTP error! status: ${response.status}`);
            return data;
        } catch (error) {
            console.error('API Fetch Error:', error);
            showToastModal(`An error occured: ${error.message}`, svgError, 5000); 
            throw error;
        }
    }

    /**
     * Renders a visual signal strength indicator based on a percentage.
     * @param {number} signal The signal strength (0-100).
     * @returns {string} The HTML for the SVG signal indicator.
     */
    function renderSignalIndicator(signal) {
        let colorClass = 'signal-weak';
        if (signal > 75) colorClass = 'signal-excellent';
        else if (signal > 50) colorClass = 'signal-good';
        else if (signal > 25) colorClass = 'signal-ok';
        return `<svg class="signal-svg ${colorClass}" viewBox="0 0 24 24" fill="currentColor"><path d="M12 4C7.31 4 3.07 5.9 0 8.98L12 21l12-12.02C20.93 5.9 16.69 4 12 4z" opacity="${signal > 0 ? 1 : 0.2}"/><path d="M12 9c-2.31 0-4.43.7-6.24 1.98L12 18l6.24-7.02C16.43 9.7 14.31 9 12 9z" opacity="${signal > 25 ? 1 : 0.2}"/><path d="M12 14c-1.15 0-2.2.35-3.12.99L12 15l3.12-1.01C14.2 14.35 13.15 14 12 14z" opacity="${signal > 50 ? 1 : 0.2}"/><circle cx="12" cy="18" r="2" opacity="${signal > 75 ? 1 : 0.2}"/></svg> ${signal}%`;
    }

    // --- EVENT LISTENERS ---

    // Scan for WiFi networks when the button is clicked
    if (scanWifiBtn) {
        const iconPlaceholder = scanWifiBtn.querySelector('.button-icon-placeholder');
        iconPlaceholder.innerHTML = svgSync;
        scanWifiBtn.addEventListener('click', async () => {
            scanWifiBtn.disabled = true;
            iconPlaceholder.innerHTML = svgLoader;
            wifiListBody.innerHTML = `<tr><td colspan="4">Scanning... Please wait.</td></tr>`;
            try {
                const networks = await apiFetch('/api/system/network/scan', { method: 'POST' });
                wifiListBody.innerHTML = '';
                if (networks.length === 0) {
                    wifiListBody.innerHTML = `<tr><td colspan="4">No networks found.</td></tr>`;
                } else {
                    networks.forEach(net => {
                        const tr = document.createElement('tr');
                        tr.innerHTML = `
                            <td>${net.ssid}</td>
                            <td>${renderSignalIndicator(net.signal)}</td>
                            <td>${net.security}</td>
                            <td><button class="action-button small connect-btn" data-ssid="${net.ssid}" data-security="${net.security}">Connect</button></td>
                        `;
                        wifiListBody.appendChild(tr);
                    });
                }
            } catch (error) {
                wifiListBody.innerHTML = `<tr><td colspan="4">Error scanning for networks.</td></tr>`;
            } finally {
                scanWifiBtn.disabled = false;
                iconPlaceholder.innerHTML = svgSync;
            }
        });
    }

    // Open the password modal when a "Connect" button in the list is clicked
    if (wifiListBody) {
        wifiListBody.addEventListener('click', (e) => {
            if (e.target.classList.contains('connect-btn')) {
                const ssid = e.target.dataset.ssid;
                const security = e.target.dataset.security;
                if (security === 'Open') {
                    handleWifiConnect(ssid, ''); // Connect directly if network is open
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
    
    // Handle the form submission from the password modal
    if (wifiConnectForm) {
        wifiConnectForm.addEventListener('submit', (e) => {
            e.preventDefault();
            handleWifiConnect(wifiSsidInput.value, wifiPasswordInput.value);
        });
    }

    /**
     * This is the core connection logic. It handles the expected disconnection
     * from the hotspot gracefully.
     * @param {string} ssid The SSID to connect to.
     * @param {string} password The password for the network.
     */
    function handleWifiConnect(ssid, password) {
        if (wifiModal) wifiModal.style.display = 'none';

        // 1. Show an optimistic status message in the new modal.
        statusTitle.textContent = `Connecting to "${ssid}"...`;
        statusText.textContent = 'The hotspot will now disconnect. Please wait for final instructions.';
        statusContainer.style.display = 'flex';

        // 2. Send the connection request. We expect this to fail because the hotspot
        // will turn off, so we only care about the .catch() block.
        fetch('/api/system/network/connect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ssid, password }),
        }).catch(error => {
            console.log("Fetch failed as expected, because the hotspot disconnected.", error);
        });

        // 3. After a delay, update the UI with final instructions.
        setTimeout(() => {
            statusTitle.textContent = 'Connection Successful!';
            statusText.innerHTML = `
                The BantayTubig device is now connected to <strong>${ssid}</strong>.
                <br><br>
                Please manually reconnect your phone or laptop to your main WiFi network to continue. The device will restart its services.
            `;
        }, 5000); // 5-second delay to allow the Pi to switch networks
    }
    
    // Close the modal when the 'x' is clicked
    if (closeWifiModalBtn) {
        closeWifiModalBtn.addEventListener('click', () => wifiModal.style.display = 'none');
    }


    if (scanWifiBtn) scanWifiBtn.click();
});
