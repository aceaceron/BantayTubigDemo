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

