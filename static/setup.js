// static/setup.js

document.addEventListener('DOMContentLoaded', function() {

    // --- ELEMENT SELECTors ---
    const scanWifiBtn = document.getElementById('scanWifiBtn');
    const wifiListBody = document.getElementById('wifiListBody');
    const wifiModal = document.getElementById('wifiPasswordModal');
    const closeWifiModalBtn = document.getElementById('closeWifiModalBtn');
    const wifiConnectForm = document.getElementById('wifiConnectForm');
    const ssidNameLabel = document.getElementById('ssidNameLabel');
    const wifiSsidInput = document.getElementById('wifiSsidInput');
    const wifiPasswordInput = document.getElementById('wifiPasswordInput');
    const statusContainer = document.getElementById('statusMessageContainer');
    const statusTitle = document.getElementById('statusTitle');
    const statusText = document.getElementById('statusText');

    // --- SVG Icon Definitions ---
    const svgLoader = `<svg class="svg-loader" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg>`;
    const svgSync = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M23 4v6h-6"/><path d="M1 20v-6h6"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>`;

    async function apiFetch(url, options = {}) {
        const response = await fetch(url, options);
        if (!response.ok) {
            const data = await response.json().catch(() => ({ message: 'An unknown error occurred' }));
            throw new Error(data.message || `HTTP error! status: ${response.status}`);
        }
        return response.json();
    }

    function renderSignalIndicator(signal) {
        let colorClass = 'signal-weak';
        if (signal > 75) colorClass = 'signal-excellent';
        else if (signal > 50) colorClass = 'signal-good';
        else if (signal > 25) colorClass = 'signal-ok';
        return `<svg class="signal-svg ${colorClass}" viewBox="0 0 24 24" fill="currentColor"><path d="M12 4C7.31 4 3.07 5.9 0 8.98L12 21l12-12.02C20.93 5.9 16.69 4 12 4z" opacity="${signal > 0 ? 1 : 0.2}"/><path d="M12 9c-2.31 0-4.43.7-6.24 1.98L12 18l6.24-7.02C16.43 9.7 14.31 9 12 9z" opacity="${signal > 25 ? 1 : 0.2}"/><path d="M12 14c-1.15 0-2.2.35-3.12.99L12 15l3.12-1.01C14.2 14.35 13.15 14 12 14z" opacity="${signal > 50 ? 1 : 0.2}"/><circle cx="12" cy="18" r="2" opacity="${signal > 75 ? 1 : 0.2}"/></svg> ${signal}%`;
    }

    // --- EVENT LISTENERS ---
    if (scanWifiBtn) {
        const iconPlaceholder = scanWifiBtn.querySelector('.button-icon-placeholder');
        iconPlaceholder.innerHTML = svgSync;
        scanWifiBtn.addEventListener('click', async () => {
            statusContainer.style.display = 'none';
            
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

    if (wifiListBody) {
        wifiListBody.addEventListener('click', (e) => {
            if (e.target.classList.contains('connect-btn')) {
                statusContainer.style.display = 'none';

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

    function handleWifiConnect(ssid, password) {
        if (wifiModal) wifiModal.style.display = 'none';

        statusTitle.textContent = `Sinusubukang Kumonekta sa "${ssid}"...`;
        statusText.textContent = 'Madidiskonekta ngayon ang hotspot ng device para subukang kumonekta sa iyong network. Maaaring abutin ito ng 30 segundo.';
        statusContainer.style.display = 'flex';

        fetch('/api/system/network/connect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ssid, password }),
        }).catch(error => {
            console.log("Browser disconnected as expected while device attempts to connect.", error);
        });

        setTimeout(() => {
            statusTitle.textContent = 'Tapos na ang Pagtangkang Kumonekta';
            statusText.innerHTML = `
                Tingnan ang LCD screen ng device para sa susunod na hakbang.
                <br><em><small><strong>Please look at the device's LCD screen for the next step.</strong></small></em>
                <br><br>
                <strong>Kung Nagtagumpay:</strong> Ipapakita ng LCD ang bagong IP address ng device (hal. 192.168.1.10). I-reconnect ang computer na ito sa iyong main Wi-Fi at gamitin ang IP address na iyon sa iyong browser.
                <br><em><small><strong>If Successful:</strong> The LCD will display the device's new IP address (e.g., 192.168.1.10). Reconnect this computer to your main Wi-Fi and use that IP address in your browser.</small></em>
                <br><br>
                <strong>Kung Nabigo:</strong> Ipapakita muli ng LCD ang mga detalye ng "BantayTubig-Setup" hotspot. Paki-reconnect sa hotspot na iyon at i-refresh ang page na ito para subukang muli.
                <br><em><small><strong>If it Fails:</strong> The LCD will again display the "BantayTubig-Setup" hotspot details. Please reconnect to that hotspot and refresh this page to try again.</small></em>
            `;
        }, 8000);
    }
    
    if (closeWifiModalBtn) {
        closeWifiModalBtn.addEventListener('click', () => wifiModal.style.display = 'none');
    }

    if (scanWifiBtn) scanWifiBtn.click();
});