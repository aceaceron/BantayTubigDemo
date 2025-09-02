// static/global_alerter.js

document.addEventListener('DOMContentLoaded', () => {
    // --- Elements for the Live Alert Banner ---
    const liveAlertBanner = document.getElementById('liveAlertBanner');
    const liveAlertTitle = document.getElementById('liveAlertTitle');
    const liveAlertDetails = document.getElementById('liveAlertDetails');
    const snoozeLiveAlertBtn = document.getElementById('snoozeLiveAlertBtn');
    const ackLiveAlertBtn = document.getElementById('ackLiveAlertBtn');
    const closeLiveAlertBtn = document.getElementById('closeLiveAlertBtn');

    // Establish a connection to the WebSocket server
    const socket = io();

    socket.on('connect', () => {
        console.log('Successfully connected to WebSocket server.');
        // NEW: Tell the server to add this client to the broadcast room
        socket.emit('join_room', { room: 'broadcast_room' });
    });

    // This is the main listener for new alerts from the server
    socket.on('new_alert', (alertData) => {
        console.log('Received new alert:', alertData);
        showLiveAlertBanner(alertData);
    });
    
    // Listen for events that indicate an alert has been cleared
    socket.on('alert_cleared', () => {
        console.log('Received alert cleared signal.');
        hideLiveAlertBanner();
    });

    function showLiveAlertBanner(alert) {
        liveAlertTitle.textContent = alert.rule_name;
        liveAlertDetails.textContent = alert.details;
        ackLiveAlertBtn.dataset.historyId = alert.id;
        snoozeLiveAlertBtn.dataset.ruleId = alert.rule_id;
        liveAlertBanner.classList.add('show');
    }
    
    function hideLiveAlertBanner() {
        liveAlertBanner.classList.remove('show');
    }
    
    // --- Event Listeners for Banner Buttons ---
    closeLiveAlertBtn.addEventListener('click', hideLiveAlertBanner);

    ackLiveAlertBtn.addEventListener('click', async () => {
        const historyId = ackLiveAlertBtn.dataset.historyId;
        if (!historyId) return;
        try {
            await fetch(`/api/alerts/history/${historyId}/acknowledge`, { method: 'POST' });
            hideLiveAlertBanner();
        } catch (error) {
            console.error("Failed to acknowledge alert.");
        }
    });

    snoozeLiveAlertBtn.addEventListener('click', async () => {
        const ruleId = snoozeLiveAlertBtn.dataset.ruleId;
        if (!ruleId) return;
        hideLiveAlertBanner();
        try {
            await fetch(`/api/alerts/rules/${ruleId}/snooze`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ duration_minutes: 1 })
            });
        } catch (error) {
            console.error("Failed to snooze alert:", error);
        }
    });

    // --- Network Status Checker ---
    const networkStatusBanner = document.getElementById('networkStatusBanner');
    const networkStatusText = document.getElementById('networkStatusText');

    async function checkNetworkStatus() {
        try {
            const response = await fetch('/api/system/network/status');
            if (!response.ok) {
                showNetworkWarning('Cannot reach server.');
                return;
            }
            const data = await response.json();

            if (data.status === 'connected') {
                hideNetworkWarning();
            } else {
                showNetworkWarning('Device is offline. Displayed data may not be live.');
            }

        } catch (error) {
            // This catches fetch errors, which usually mean no network
            showNetworkWarning('No network connection. Retrying...');
        }
    }

    function showNetworkWarning(message) {
        if (networkStatusBanner) {
            networkStatusText.textContent = message;
            networkStatusBanner.classList.add('show');
        }
    }

    function hideNetworkWarning() {
        if (networkStatusBanner) {
            networkStatusBanner.classList.remove('show');
        }
    }

    // Start polling for network status every 5 seconds
    setInterval(checkNetworkStatus, 5000);
    // And check once immediately on page load
    checkNetworkStatus();
});


// --- GLOBAL HELPERS (Accessible by all other scripts) ---

const toastModal = document.getElementById('toastModal');
const toastIcon = document.getElementById('toastIcon');
const toastMessage = document.getElementById('toastMessage');
const svgSuccess = `<svg viewBox="0 0 24 24" fill="none" stroke="#28a745" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>`;
const svgError = `<svg viewBox="0 0 24 24" fill="none" stroke="#dc3545" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>`;

/**
 * Displays a global toast notification.
 */
function showToastModal(message, icon, duration = 4000) {
    if (!toastModal) return;
    toastMessage.textContent = message;
    toastIcon.innerHTML = icon;
    toastModal.classList.add('show');
    setTimeout(() => toastModal.classList.remove('show'), duration);
}


/**
 * A robust, global helper function to fetch data from the API and handle
 * authentication redirects by checking the Content-Type.
 */
async function apiFetch(url, options = {}) {
    try {
        const response = await fetch(url, options);
        const contentType = response.headers.get("content-type");

        if (!contentType || !contentType.includes("application/json")) {
            console.error("Auth error: Server sent non-JSON response. Redirecting to login.");
            window.location.assign('/login');
            return new Promise(() => {});
        }

        const data = await response.json();
        if (!response.ok) throw new Error(data.message || `HTTP error! status: ${response.status}`);
        return data;
    } catch (error) {
        if (error instanceof SyntaxError) {
            console.error("Received non-JSON response from API. Redirecting to login.");
            window.location.assign('/login');
            return new Promise(() => {});
        }
        console.error('API Fetch Error:', error);
        showToastModal(`Error: ${error.message}`, svgError);
        throw error;
    }
}


