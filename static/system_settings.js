// static/system_settings.js

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
/**
 * ------------------------------------------------------------------------
 * API FETCH HELPER
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
                contentPanel.style.maxHeight = "100vh";
            }
        });
    });

    // --- STATE MANAGEMENT ---
    let currentSettings = { dataRetention: '365' };
    let previewData = { full: [], filtered: [] };
    let previewCurrentPage = 1;
    const previewRowsPerPage = 5;
    let previewSort = { column: 'timestamp', direction: 'desc' };

    // --- ELEMENT SELECTORS ---
    const systemNameInput = document.getElementById('systemName');
    const saveBtn = document.getElementById('saveSettingsBtn');
    const powerOffBtn = document.getElementById('powerOffBtn'); 
    const scanWifiBtn = document.getElementById('scanWifiBtn');
    const wifiListBody = document.getElementById('wifiListBody');
    const networkStatusContent = document.getElementById('networkStatusContent');
    const wifiModal = document.getElementById('wifiPasswordModal');
    const closeWifiModalBtn = document.getElementById('closeWifiModalBtn');
    const wifiConnectForm = document.getElementById('wifiConnectForm');
    const ssidNameLabel = document.getElementById('ssidNameLabel');
    const wifiSsidInput = document.getElementById('wifiSsidInput');
    const wifiPasswordInput = document.getElementById('wifiPasswordInput');
    const sessionTimeoutInput = document.getElementById('sessionTimeout');
    const dataRetentionInput = document.getElementById('dataRetention');
    const dataCleanupModal = document.getElementById('dataCleanupModal');
    const closeCleanupModalBtn = document.getElementById('closeCleanupModalBtn');
    const tablePreviewSelect = document.getElementById('tablePreviewSelect');
    const previewSearchInput = document.getElementById('previewSearchInput');
    const cleanupPreviewTableBody = document.querySelector('#cleanupPreviewTable tbody');
    const previewSortableHeaders = document.querySelectorAll('#cleanupPreviewTable th.sortable');
    const previewPrevPageBtn = document.getElementById('previewPrevPageBtn');
    const previewNextPageBtn = document.getElementById('previewNextPageBtn');
    const previewPageInfo = document.getElementById('previewPageInfo');
    const cancelDeleteBtn = document.getElementById('cancelDeleteBtn');
    const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
    const toastModal = document.getElementById('toastModal');
    const toastIcon = document.getElementById('toastIcon');
    const toastMessage = document.getElementById('toastMessage');
    const showMlConfidenceToggle = document.getElementById('showMlConfidenceToggle'); 

    // --- SVG Icon Definitions ---
    const svgLoader = `<svg class="svg-loader" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg>`;
    const svgSync = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M23 4v6h-6"/><path d="M1 20v-6h6"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>`;
    const svgSuccess = `<svg viewBox="0 0 24 24" fill="none" stroke="#28a745" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>`;
    const svgConnecting = `<svg class="wifi-connecting-icon" viewBox="0 0 24 24" fill="none" stroke="#3498db" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.55a8 8 0 0 1 14.08 0"/><path d="M1.42 9a16 16 0 0 1 21.16 0"/><path d="M8.53 16.11a4 4 0 0 1 6.95 0"/><line x1="12" y1="20" x2="12.01" y2="20"/></svg>`;
    const svgError = `<svg viewBox="0 0 24 24" fill="none" stroke="#dc3545" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>`;
    const svgPower = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18.36 6.64a9 9 0 1 1-12.73 0"></path><line x1="12" y1="2" x2="12" y2="12"></line></svg>`; 

    // --- DATA FETCHING & SAVING LOGIC ---
    async function loadDeviceSettings() {
        try {
            const data = await apiFetch('/api/system/settings');
            if (systemNameInput) systemNameInput.value = data.systemName;
            if (sessionTimeoutInput) sessionTimeoutInput.value = data.sessionTimeout;
            if (dataRetentionInput) {
                dataRetentionInput.value = data.dataRetention;
                currentSettings.dataRetention = data.dataRetention; 
            }
            if (showMlConfidenceToggle) showMlConfidenceToggle.checked = (data.showMlConfidence === 'true');
        } catch (error) {
            console.error("Could not load system settings:", error);
        }
    }

    if (saveBtn) {
        saveBtn.addEventListener('click', async () => {
            saveBtn.classList.add('saving');

            const oldRetention = currentSettings.dataRetention;
            const newRetention = dataRetentionInput.value;

            try {
                // Step 1: Save the new setting to the database
                const settingsData = {
                    systemName: systemNameInput.value,
                    sessionTimeout: sessionTimeoutInput.value,
                    dataRetention: newRetention,
                    showMlConfidence: showMlConfidenceToggle.checked
                };
                localStorage.setItem('showMlConfidence', showMlConfidenceToggle.checked);
                await apiFetch('/api/system/settings', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(settingsData)
                });

                // Step 2: Check if the new policy is stricter
                if (parseInt(newRetention) < parseInt(oldRetention)) {
                    // Step 3: Before showing the modal, check if there is actually data to delete
                    const previewCheckData = await apiFetch('/api/system/retention-preview', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            retention_days: newRetention,
                            table_name: 'measurements' // Use a primary table for the check
                        })
                    });

                    // Step 4: Only open the modal if the check returns data
                    if (previewCheckData && previewCheckData.length > 0) {
                        openCleanupModal(newRetention);
                    } else {
                        // If no data would be deleted, skip the modal
                        showToastModal('Settings saved!', svgSuccess);
                        currentSettings.dataRetention = newRetention;
                    }
                } else {
                    // If the policy is not stricter, just confirm the save
                    showToastModal('Settings saved successfully!', svgSuccess);
                    currentSettings.dataRetention = newRetention;
                }
            } catch (error) {
                // Error is handled by apiFetch
            } finally {
                setTimeout(() => {
                    saveBtn.classList.remove('saving');
                }, 1500);
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


    // --- DATA CLEANUP MODAL FUNCTIONS ---
    async function openCleanupModal(retentionDays) {
        dataCleanupModal.style.display = 'flex';
        await fetchAndRenderPreview();
    }
    
    async function fetchAndRenderPreview() {
        const retentionDays = dataRetentionInput.value;
        const selectedTable = tablePreviewSelect.value;
        
        try {
            const data = await apiFetch('/api/system/retention-preview', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    retention_days: retentionDays,
                    table_name: selectedTable
                })
            });
            previewData.full = data;
            applyPreviewFilters();
        } catch (error) {
            cleanupPreviewTableBody.innerHTML = `<tr><td colspan="3">Error loading preview.</td></tr>`;
        }
    }


    function applyPreviewFilters() {
        const searchTerm = previewSearchInput.value.trim().toLowerCase();

        if (!searchTerm) {
            previewData.filtered = [...previewData.full];
            renderPreviewTable();
            return;
        }

        previewData.filtered = previewData.full.filter(row => {
            const rowTimestamp = new Date(row.timestamp);

            // 1. Search by ID (if input is purely a number)
            if (/^\d+$/.test(searchTerm)) {
                return String(row.id).includes(searchTerm);
            }

            // 2. Search by Date (if input can be parsed as a valid date, e.g., "2025-08-19")
            const searchDate = new Date(searchTerm);
            if (!isNaN(searchDate.getTime())) {
                return rowTimestamp.getFullYear() === searchDate.getFullYear() &&
                       rowTimestamp.getMonth() === searchDate.getMonth() &&
                       rowTimestamp.getDate() === searchDate.getDate();
            }
            
            // 3. Search by Time (if input is like "7:28pm", searches for all records on the current day)
            // This allows users to quickly see today's logs without typing the full date.
            if (/^\d{1,2}:\d{2}\s*(am|pm)?$/i.test(searchTerm)) {
                const today = new Date();
                return rowTimestamp.getFullYear() === today.getFullYear() &&
                       rowTimestamp.getMonth() === today.getMonth() &&
                       rowTimestamp.getDate() === today.getDate();
            }

            // 4. Fallback to generic text search in details and full timestamp string
            const details = row.Details ? String(row.Details).toLowerCase() : '';
            const timestampString = row.timestamp ? String(row.timestamp).toLowerCase() : '';
            return details.includes(searchTerm) || timestampString.includes(searchTerm);
        });

        previewCurrentPage = 1;
        applyPreviewSort(); 
        renderPreviewTable();
    }

    function applyPreviewSort() {
        previewData.filtered.sort((a, b) => {
            const col = previewSort.column;
            const dir = previewSort.direction === 'asc' ? 1 : -1;
            
            let valA = a[col];
            let valB = b[col];

            if (col === 'timestamp') {
                valA = valA ? new Date(valA).getTime() : 0;
                valB = valB ? new Date(valB).getTime() : 0;
            } else {
                valA = valA ? String(valA).toLowerCase() : '';
                valB = valB ? String(valB).toLowerCase() : '';
            }

            if (valA < valB) return -1 * dir;
            if (valA > valB) return 1 * dir;
            return 0;
        });
        updatePreviewSortIcons();
    }

    function renderPreviewTable() {
        cleanupPreviewTableBody.innerHTML = '';
        const start = (previewCurrentPage - 1) * previewRowsPerPage;
        const end = start + previewRowsPerPage;
        const paginatedData = previewData.filtered.slice(start, end);

        if (paginatedData.length === 0) {
            cleanupPreviewTableBody.innerHTML = `<tr><td colspan="3">No data matching the criteria will be deleted.</td></tr>`;
        } else {
            paginatedData.forEach(row => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${row.id}</td>
                    <td>${new Date(row.timestamp).toLocaleString()}</td>
                    <td>${row.Details || 'N/A'}</td>
                `;
                cleanupPreviewTableBody.appendChild(tr);
            });
        }
        updatePreviewPagination();
    }

    function updatePreviewSortIcons() {
        previewSortableHeaders.forEach(th => {
            const icon = th.querySelector('.sort-icon');
            if (th.dataset.column === previewSort.column) {
                icon.textContent = previewSort.direction === 'asc' ? ' ▲' : ' ▼';
            } else {
                icon.textContent = '';
            }
        });
    }

    function updatePreviewPagination() {
        const totalRows = previewData.filtered.length;
        const totalPages = Math.ceil(totalRows / previewRowsPerPage) || 1;
        previewPageInfo.textContent = `Page ${previewCurrentPage} of ${totalPages}`;
        previewPrevPageBtn.disabled = previewCurrentPage === 1;
        previewNextPageBtn.disabled = previewCurrentPage >= totalPages;
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

    if (tablePreviewSelect) tablePreviewSelect.addEventListener('change', fetchAndRenderPreview);
    if (previewSearchInput) previewSearchInput.addEventListener('input', applyPreviewFilters);
    if (previewPrevPageBtn) {
        previewPrevPageBtn.addEventListener('click', () => {
            if (previewCurrentPage > 1) {
                previewCurrentPage--;
                renderPreviewTable();
            }
        });
    }
    previewSortableHeaders.forEach(header => {
        header.addEventListener('click', () => {
            const column = header.dataset.column;
            if (previewSort.column === column) {
                previewSort.direction = previewSort.direction === 'asc' ? 'desc' : 'asc';
            } else {
                previewSort.column = column;
                previewSort.direction = 'desc'; // Default to descending for a new column
            }
            applyPreviewSort();
            renderPreviewTable();
        });
    });
    if (previewNextPageBtn) {
        previewNextPageBtn.addEventListener('click', () => {
            const totalPages = Math.ceil(previewData.filtered.length / previewRowsPerPage);
            if (previewCurrentPage < totalPages) {
                previewCurrentPage++;
                renderPreviewTable();
            }
        });
    }
    if (confirmDeleteBtn) {
        confirmDeleteBtn.addEventListener('click', async () => {
            confirmDeleteBtn.disabled = true;
            confirmDeleteBtn.textContent = 'Deleting...';
            try {
                const result = await apiFetch('/api/system/run-cleanup', { method: 'POST' });
                showToastModal(result.message, svgSuccess, 5000);
                dataCleanupModal.style.display = 'none';
                // Finalize the state update now that deletion is confirmed
                currentSettings.dataRetention = dataRetentionInput.value;
            } catch (error) {
                // Handled by apiFetch
            } finally {
                confirmDeleteBtn.disabled = false;
                confirmDeleteBtn.textContent = 'Yes, Delete Old Data';
            }
        });
    }

    if (cancelDeleteBtn) {
        cancelDeleteBtn.addEventListener('click', async () => {
            // Get the original value that was stored before the save attempt
            const originalRetentionValue = currentSettings.dataRetention;

            // 1. Visually revert the dropdown
            dataRetentionInput.value = originalRetentionValue;
            
            // 2. Save the original value back to the database
            try {
                await apiFetch('/api/system/settings', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ dataRetention: originalRetentionValue })
                });
                showToastModal('Data retention change canceled.', svgSuccess);
            } catch (error) {
                showToastModal('Failed to revert the setting. Please try saving again.', svgError);
            }

            // 3. Close the modal
            dataCleanupModal.style.display = 'none';
        });
    }

    if (powerOffBtn) {
        powerOffBtn.addEventListener('click', () => {
            if (!confirm("Are you sure you want to shut down the system? It will become unresponsive in a few seconds.")) {
                return;
            }

            // Disable buttons to prevent multiple clicks
            powerOffBtn.disabled = true;
            if (saveBtn) saveBtn.disabled = true;

            // Show a toast that the process has started
            showToastModal('System will power off shortly.', svgPower, 10000);

            // Call the SINGLE endpoint that handles the entire sequence
            fetch('/api/system/power-off', { method: 'POST' })
                .catch(error => {
                    // A network error is EXPECTED because the server is stopping.
                    // This indicates the process is working correctly.
                    console.log("Shutdown initiated. Server connection lost as expected.");
                });
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
