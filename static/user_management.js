// user_management.js

// --- SIDEBAR AND GLOBAL NAVIGATION SCRIPT ---
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


document.addEventListener('DOMContentLoaded', function() {
    setupGlobalNavigation();

    // --- TABS ---
    const tabLinks = document.querySelectorAll('.tab-link');
    const tabContents = document.querySelectorAll('.tab-content');

    tabLinks.forEach(link => {
        link.addEventListener('click', () => {
            const tabId = link.dataset.tab;

            tabLinks.forEach(l => l.classList.remove('active'));
            link.classList.add('active');

            tabContents.forEach(content => {
                content.classList.remove('active');
                if (content.id === tabId) {
                    content.classList.add('active');
                    if (tabId === 'audit') {
                        loadAuditLogs();
                    }
                }
            });
        });
    });

    // --- USERS TAB ELEMENTS ---
    const usersTableBody = document.querySelector('#usersTable tbody');
    const addNewUserBtn = document.getElementById('addNewUserBtn');
    const userModal = document.getElementById('userModal');
    const userModalTitle = document.getElementById('userModalTitle');
    const closeUserModalBtn = document.getElementById('closeUserModalBtn');
    const userForm = document.getElementById('userForm');
    const userIdInput = document.getElementById('userId');
    const userFullNameInput = document.getElementById('userFullName');
    const userEmailInput = document.getElementById('userEmail');
    const userPhoneNumberInput = document.getElementById('userPhoneNumber');
    const userRoleSelect = document.getElementById('userRole');
    const userSearchInput = document.getElementById('userSearchInput');
    const sortableHeaders = document.querySelectorAll('#usersTable th.sortable');
    const userPrevPageBtn = document.getElementById('userPrevPageBtn');
    const userNextPageBtn = document.getElementById('userNextPageBtn');
    const userPageInfo = document.getElementById('userPageInfo');
    const userRoleWrapper = document.getElementById('userRoleWrapper');

    // --- USER DATA STATE MANAGEMENT ---
    let allUsers = []; 
    let allRoles = []; 
    let currentSort = { column: 'full_name', direction: 'asc' };
    let userCurrentPage = 1;
    const userRowsPerPage = 10; 

    // --- AUDIT LOG TAB ELEMENTS ---
    const auditLogTableBody = document.querySelector('#auditLogTable tbody');
    const auditDateFilter = document.getElementById('auditDateFilter');
    const auditUserFilter = document.getElementById('auditUserFilter');
    const auditActionFilter = document.getElementById('auditActionFilter');
    const exportAuditCsvBtn = document.getElementById('exportAuditCsvBtn');
    const exportAuditPdfBtn = document.getElementById('exportAuditPdfBtn');
    const auditSortableHeaders = document.querySelectorAll('#auditLogTable th.sortable'); // New selector
    const auditPrevPageBtn = document.getElementById('auditPrevPageBtn');
    const auditNextPageBtn = document.getElementById('auditNextPageBtn');
    const auditPageInfo = document.getElementById('auditPageInfo');

    // --- AUDIT LOG STATE MANAGEMENT ---
    let auditLogData = []; // Cache for fetched log data
    let currentAuditSort = { column: 'timestamp', direction: 'desc' }; // New state for audit log sorting
    let auditCurrentPage = 1;
    const auditRowsPerPage = 10;

    // --- Add a constant list of all available pages/permissions ---
    const AVAILABLE_PERMISSIONS = {
        'dashboard': 'Dashboard',
        'analytics': 'Analytics & Reports',
        'devices': 'Device & Sensor',
        'alerts': 'Alerts & Notification',
        'machine_learning': 'Machine Learning',
        'users': 'User Management',
        'settings': 'System Settings'
    };

    // --- OTHER MODAL ELEMENTS ---
    const credentialsModal = document.getElementById('newUserCredentialsModal');
    const credentialsModalTitle = document.getElementById('credentialsModalTitle');
    const closeCredentialsModalBtn = document.getElementById('closeCredentialsModalBtn');
    const newUserNameSpan = document.getElementById('newUserName');
    const newUserEmailSpan = document.getElementById('newUserEmail');
    const newPhoneNumberSpan = document.getElementById('newPhoneNumber');
    const newUserPasswordSpan = document.getElementById('newUserPassword');
    const rolesTableBody = document.querySelector('#rolesTable tbody');
    const addNewRoleBtn = document.getElementById('addNewRoleBtn');
    const roleModal = document.getElementById('roleModal');
    const roleModalTitle = document.getElementById('roleModalTitle');
    const closeRoleModalBtn = document.getElementById('closeRoleModalBtn');
    const roleForm = document.getElementById('roleForm');
    const roleIdInput = document.getElementById('roleId');
    const roleNameInput = document.getElementById('roleName');
    const roleDescriptionTextarea = document.getElementById('roleDescription');
    const rolePermissionsChecklist = document.getElementById('rolePermissionsChecklist');
    

    // --- MODAL FOR PROTECTED ROLES ---
    const protectedRoleModal = document.getElementById('protectedRoleModal');
    const closeProtectedRoleModalBtn = document.getElementById('closeProtectedRoleModalBtn');

    // --- DEFINE CORE SYSTEM ROLES ---
    const PROTECTED_ROLES = ['Administrator', 'Technician', 'Viewer', 'Data Scientist'];

    // --- API FUNCTIONS ---
    /**
     * ------------------------------------------------------------------------
     * API FETCH HELPER
     * This function fetches data from the API and intelligently handles redirects
     * by checking the Content-Type of the server's response.
     * ------------------------------------------------------------------------
     */
    async function apiFetch(url, options = {}) {
        try {
            const response = await fetch(url, options);

            // Check the 'Content-Type' header of the response.
            const contentType = response.headers.get("content-type");

            // If the server sent back HTML/text instead of JSON, it's a redirect to the login page.
            if (!contentType || !contentType.includes("application/json")) {
                console.error("Authentication error: Server sent back non-JSON response. Redirecting to login.");
                // Force the browser to navigate to the login page.
                window.location.assign('/login');
                // Stop any further script execution by returning a promise that never resolves.
                return new Promise(() => {});
            }

            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.message || `HTTP error! status: ${response.status}`);
            }
            return data;

        } catch (error) {
            // This will catch any other network or unexpected errors.
            console.error('API Fetch Error:', error);
            // Display a user-friendly error message. A toast notification would be ideal.
            alert(`An error occurred: ${error.message}`);
            throw error;
        }
    }


    // --- USER MANAGEMENT FUNCTIONS ---
    /**
     * Fetches the list of all users from the API.
     */
    async function loadUsers() {
        if (!usersTableBody) return; // Exit if the table isn't on the page.
        
        try {
            usersTableBody.innerHTML = '<tr><td colspan="6">Loading users...</td></tr>';
            // Use the robust apiFetch to get the user list.
            const users = await apiFetch('/api/users');
            allUsers = users;
            renderFilteredAndSortedUsers();
        } catch (error) {
            // The apiFetch function already handles the redirect, so this will catch other errors.
            usersTableBody.innerHTML = '<tr><td colspan="6">Failed to load users. Please try again.</td></tr>';
            console.error("Error in loadUsers:", error);
        }
    }

    // Central function to handle filtering, sorting, and rendering
    function renderFilteredAndSortedUsers() {
        let processedUsers = [...allUsers];
    
        const searchTerm = userSearchInput.value.toLowerCase();
        if (searchTerm) {
            processedUsers = processedUsers.filter(user => 
                user.full_name.toLowerCase().includes(searchTerm) ||
                user.email.toLowerCase().includes(searchTerm) ||
                user.id.toString().includes(searchTerm)
            );
        }
    
        processedUsers.sort((a, b) => {
            const col = currentSort.column;
            const dir = currentSort.direction === 'asc' ? 1 : -1;
            let valA = a[col], valB = b[col];
    
            if (col === 'last_login') {
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
    
        updateSortIcons();
        renderUsersTable(processedUsers);
    }

    // Function to update the sort icons in the table header
    function updateSortIcons() {
        sortableHeaders.forEach(th => {
            const icon = th.querySelector('.sort-icon');
            if (th.dataset.column === currentSort.column) {
                icon.textContent = currentSort.direction === 'asc' ? ' ▲' : ' ▼';
            } else {
                icon.textContent = '';
            }
        });
    }

    async function loadRolesForUserForm() {
        const roles = await apiFetch('/api/roles');
        // Only get name and id for the dropdown
        const roleOptions = roles.map(role => ({ id: role.id, name: role.name }));
        userRoleSelect.innerHTML = roleOptions.map(role => `<option value="${role.id}">${role.name}</option>`).join('');
    }
    
    function renderUsersTable(users) {
        usersTableBody.innerHTML = '';
        const start = (userCurrentPage - 1) * userRowsPerPage;
        const end = start + userRowsPerPage;
        const paginatedUsers = users.slice(start, end);

        if (paginatedUsers.length === 0) {
            usersTableBody.innerHTML = `<tr><td colspan="7">No users found.</td></tr>`;
        } else {
            paginatedUsers.forEach(user => {
                const tr = document.createElement('tr');
                const statusClass = user.status.toLowerCase() === 'active' ? 'status-active' : 'status-inactive';
                const statusToggleText = user.status.toLowerCase() === 'active' ? 'Deactivate' : 'Reactivate';
                const statusToggleClass = user.status.toLowerCase() === 'active' ? 'deactivate' : 'reactivate';

                tr.innerHTML = `
                    <td>${user.full_name}</td>
                    <td>${user.email}</td>
                    <td>${user.phone_number || 'N/A'}</td>
                    <td>${user.role_name}</td>
                    <td><span class="status-badge ${statusClass}">${user.status}</span></td>
                    <td>${user.last_login ? new Date(user.last_login).toLocaleString() : 'Never'}</td>
                    <td class="action-buttons-cell">
                        <button class="action-button small edit-btn" data-id="${user.id}">Edit</button>
                        <button class="action-button small ${statusToggleClass}" data-id="${user.id}" data-status="${user.status}">${statusToggleText}</button>
                        <button class="action-button small reset-pw" data-id="${user.id}">Reset Password</button>
                    </td>
                `;
                usersTableBody.appendChild(tr);
            });
        }
        updateUserPaginationControls(users.length);
    }

    function updateUserPaginationControls(totalUsers) {
        const totalPages = Math.ceil(totalUsers / userRowsPerPage) || 1;
        userPageInfo.textContent = `Page ${userCurrentPage} of ${totalPages}`;
        userPrevPageBtn.disabled = userCurrentPage === 1;
        userNextPageBtn.disabled = userCurrentPage >= totalPages;
    }

    function openUserModal(user = null) {
        userForm.reset();
        userRoleSelect.disabled = false;

        if (userRoleWrapper) {
            userRoleWrapper.classList.remove('disabled-wrapper');
            userRoleWrapper.removeAttribute('data-tooltip');
        }

        if (user) {
            userModalTitle.textContent = 'Edit User';
            userIdInput.value = user.id;
            userFullNameInput.value = user.full_name;
            userEmailInput.value = user.email;
            userEmailInput.readOnly = true;
            userPhoneNumberInput.value = user.phone_number || '';
            userRoleSelect.value = user.role_id;

            // Count how many users have the 'Administrator' role.
            const adminCount = allUsers.filter(u => u.role_name === 'Administrator').length;

            // If the current user is an admin AND they are the only one, disable the role dropdown.
            if (user.role_name === 'Administrator' && adminCount === 1) {
                // --- Apply the disabled state and tooltip ---
                userRoleSelect.disabled = true;
                userRoleWrapper.classList.add('disabled-wrapper');
                userRoleWrapper.setAttribute('data-tooltip', 'Hindi maaaring baguhin ang role dahil kailangan ng system ng kahit isang Administrator.\n\nThis role cannot be changed as the system requires at least one Administrator.');
            }

        } else {
            userModalTitle.textContent = 'Add New User';
            userIdInput.value = '';
            userEmailInput.readOnly = false;

            // This logic correctly handles creating the first-ever user
            if (allUsers.length === 0) {
                const adminRole = allRoles.find(role => role.name === 'Administrator');
                if (adminRole) {
                    userRoleSelect.value = adminRole.id;
                }
                userRoleSelect.disabled = true;
            }
        }
        userModal.style.display = 'flex';
    }

    function showCredentialsModal(userData, isReset = false) {

        credentialsModal.style.display = 'flex';
        document.getElementById('newUserCredentialsModal').display = 'flex';

        if (isReset) {
            credentialsModalTitle.textContent = 'Password Reset Successfully';
        } else {
            credentialsModalTitle.textContent = 'User Created Successfully';
        }
        
        newUserNameSpan.textContent = userData.name;
        newUserEmailSpan.textContent = userData.email;
        newPhoneNumberSpan.textContent = userData.phone_number;
        newUserPasswordSpan.textContent = userData.password;
        
    }

    // --- MODIFIED USER FORM SUBMISSION HANDLER ---
    async function handleUserFormSubmit(e) {
        e.preventDefault();

        let phoneNumber = userPhoneNumberInput.value;
        // Treat an incomplete number as empty before saving
        if (phoneNumber === '+639' || phoneNumber.length < 13) {
            phoneNumber = '';
        }

        const userData = {
            id: userIdInput.value,
            full_name: userFullNameInput.value,
            email: userEmailInput.value,
            phone_number: userPhoneNumberInput.value,
            role_id: userRoleSelect.value
        };
        
        if (!userData.id) { // Adding a new user
            const url = '/api/users/add';
            try {
                const result = await apiFetch(url, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(userData)
                });
                userModal.style.display = 'none';
                loadUsers();
                if (result.newUser) {
                    showToastModal('User added successfully!', svgSuccess);
                    showCredentialsModal(result.newUser, false);
                }
            } catch (error) { /* Handled by apiFetch */ 
            showToastModal(error.message, svgError, 5000);
            }
        } else { // Updating an existing user
            const url = '/api/users/update';
            try {
                await apiFetch(url, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(userData)
                });
                showToastModal('User updated successfully!', svgSuccess);
                userModal.style.display = 'none';
                loadUsers();
            }  catch (error) { /* Handled by apiFetch */ 
            showToastModal(error.message, svgError, 5000);
            }
        }
    }

    async function setUserStatus(userId, currentStatus) {
        const newStatus = currentStatus.toLowerCase() === 'active' ? 'Inactive' : 'Active';
        
        showConfirmationModal(
            `Set user to '${newStatus}'?`,
            `Are you sure you want to change this user's status to ${newStatus}?`,
            async () => {
                await apiFetch('/api/users/set_status', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ id: userId, status: newStatus })
                });
                loadUsers();
            }
        );
    }
    // --- PASSWORD RESET FUNCTION ---
    async function resetUserPassword(userId) {
        showConfirmationModal(
            'Reset User Password?',
            'Are you sure you want to reset the password for this user? A new temporary password will be generated.',
            async () => {
                try {
                    const result = await apiFetch('/api/users/reset_password', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ id: userId })
                    });

                    if (result.resetUser) {
                        showCredentialsModal(result.resetUser, true);
                    }
                } catch (error) { /* Handled by apiFetch */ }
            }
        );
    }

    // --- ROLE MANAGEMENT FUNCTIONS (VIEW-ONLY) ---
    async function loadRoles() {
        if (!rolesTableBody) return;

        try {
            rolesTableBody.innerHTML = '<tr><td colspan="3">Loading roles...</td></tr>';
            const roles = await apiFetch('/api/roles');
            allRoles = roles;
            renderRolesTable(allRoles);
        } catch (error) {
            rolesTableBody.innerHTML = '<tr><td colspan="3">Failed to load roles. Please try again.</td></tr>';
            console.error("Error in loadRoles:", error);
        }
    }

    // Renders the role table 
    function renderRolesTable(roles) {
        rolesTableBody.innerHTML = '';

        if (roles.length === 0) {
            rolesTableBody.innerHTML = `<tr><td colspan="3">No roles found.</td></tr>`;
        } else {
            roles.forEach(role => {
                const tr = document.createElement('tr');
                const enabledPermissions = Object.keys(role.permissions).filter(key => role.permissions[key]);

                tr.innerHTML = `
                    <td>${role.name}</td>
                    <td>${role.description || 'No description provided.'}</td>
                    <td>
                        <div class="permissions-badge">
                            ${enabledPermissions.map(key => `
                                <span class="permission-badge" data-permission="${key}">
                                    ${AVAILABLE_PERMISSIONS[key] || key}
                                </span>`).join('')}
                        </div>
                    </td>
                `;
                rolesTableBody.appendChild(tr);
            });
        }
    }

    // --- AUDIT LOG FUNCTIONS ---
    async function loadAuditLogs() {
        const params = new URLSearchParams({
            date_range: auditDateFilter.value,
            user: auditUserFilter.value,
            action: auditActionFilter.value
        });
        auditLogData = await apiFetch(`/api/audit_log?${params.toString()}`);
        renderFilteredAndSortedAuditLogs();
    }

    // Central function to handle sorting and rendering of audit logs
    function renderFilteredAndSortedAuditLogs() {
        let processedLogs = [...auditLogData];

        // Sort the data based on the currentAuditSort state
        processedLogs.sort((a, b) => {
            const col = currentAuditSort.column;
            const dir = currentAuditSort.direction === 'asc' ? 1 : -1;

            let valA = a[col];
            let valB = b[col];

            // Timestamps need to be compared as numbers
            if (col === 'timestamp') {
                valA = new Date(valA).getTime();
                valB = new Date(valB).getTime();
            } else {
                valA = valA ? String(valA).toLowerCase() : '';
                valB = valB ? String(valB).toLowerCase() : '';
            }

            if (valA < valB) return -1 * dir;
            if (valA > valB) return 1 * dir;
            return 0;
        });

        updateAuditSortIcons();
        renderAuditLogTable(processedLogs);
    }

    // Function to update the sort icons in the audit table header
    function updateAuditSortIcons() {
        auditSortableHeaders.forEach(th => {
            const icon = th.querySelector('.sort-icon');
            if (th.dataset.column === currentAuditSort.column) {
                icon.textContent = currentAuditSort.direction === 'asc' ? ' ▲' : ' ▼';
            } else {
                icon.textContent = '';
            }
        });
    }

    // This function handles rendering, not fetching or sorting
   function renderAuditLogTable(logs) {
        auditLogTableBody.innerHTML = '';
        const start = (auditCurrentPage - 1) * auditRowsPerPage;
        const end = start + auditRowsPerPage;
        const paginatedLogs = logs.slice(start, end);

        if (paginatedLogs.length === 0) {
            auditLogTableBody.innerHTML = `<tr><td colspan="5">No audit logs found for the selected filters.</td></tr>`;
            return;
        }
        paginatedLogs.forEach(log => {
            const tr = document.createElement('tr');
            const statusClass = log.status ? log.status.toLowerCase() : 'unknown';

            tr.innerHTML = `
                <td>${new Date(log.timestamp).toLocaleString()}</td>
                <td>${log.user_name || 'System'}</td>
                <td class="event-cell">${formatEventDescription(log)}</td>
                <td><span class="status-badge status-${statusClass}">${log.status}</span></td>
                <td>${log.ip_address || 'N/A'}</td>
            `;
            auditLogTableBody.appendChild(tr);
        });
        updateAuditPaginationControls(logs.length);
    }

    function updateAuditPaginationControls(totalLogs) {
        const totalPages = Math.ceil(totalLogs / auditRowsPerPage) || 1;
        auditPageInfo.textContent = `Page ${auditCurrentPage} of ${totalPages}`;
        auditPrevPageBtn.disabled = auditCurrentPage === 1;
        auditNextPageBtn.disabled = auditCurrentPage >= totalPages;
    }

    function formatEventDescription(log) {
        // Create a badge for the system component (e.g., 'User Management')
        let componentBadge = log.component ? `<span class="component-badge">${log.component}</span>` : '';
        
        // The main action text (e.g., 'User Created')
        let actionText = log.action || 'Unknown Action';
        
        let detailsText = '';

        // If there are extra details (JSON), parse and format them
        if (log.details) {
            try {
                const detailsObj = JSON.parse(log.details);
                const detailsList = Object.entries(detailsObj)
                    // Format each detail as a list item, e.g., "New Status: Active"
                    .map(([key, value]) => `<li><strong>${key.replace(/_/g, ' ')}:</strong> ${value}</li>`)
                    .join('');
                    
                if (detailsList) {
                    detailsText = `<ul class="log-details">${detailsList}</ul>`;
                }
            } catch (e) {
                // Fallback for non-JSON details
                detailsText = `<div class="log-details-raw">${log.details}</div>`;
            }
        }
        
        return `${componentBadge} <span class="action-text">${actionText}</span>${detailsText}`;
    }
    
    function exportAuditLogToCSV() {
        if (auditLogData.length === 0) {
            showToastModal('No data to export.', svgError, 5000);
            return;
        }
        const csv = Papa.unparse(auditLogData, { header: true });
        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement("a");
        link.href = URL.createObjectURL(blob);
        link.download = `BantayTubig_AuditLog_${new Date().toISOString().split('T')[0]}.csv`;
        link.click();
    }
    
    // --- Function to export the audit log as a PDF ---
    function exportAuditLogToPDF() {
        if (auditLogData.length === 0) {
            showToastModal('No data to export.', svgError, 5000);
            return;
        }

        const { jsPDF } = window.jspdf;
        const doc = new jsPDF();

        doc.text("BantayTubig - System Audit Log Report", 14, 16);
        doc.setFontSize(10);
        doc.text(`Report Generated: ${new Date().toLocaleString()}`, 14, 22);

        // Define the columns for the PDF table
        const tableColumn = ["Timestamp", "User", "Component", "Action", "Status"];
        
        // Map the currently filtered data to the row format for the PDF
        const tableRows = auditLogData.map(log => {
            return [
                new Date(log.timestamp).toLocaleString(),
                log.user_name || 'System',
                log.component || 'N/A',
                log.action || '',
                log.status || ''
            ];
        });

        // Use the autoTable plugin to generate the table
        doc.autoTable({
            head: [tableColumn],
            body: tableRows,
            startY: 28,
            theme: 'grid',
            styles: { fontSize: 8 },
            headStyles: { fillColor: [41, 128, 185] } // A blue header
        });

        doc.save(`BantayTubig_AuditLog_${new Date().toISOString().split('T')[0]}.pdf`);
    }
    
    // --- INITIALIZATION & EVENT LISTENERS ---
    
    // Initial data loads
    loadUsers();
    loadRolesForUserForm();
    loadRoles();
    //loadAuditLogs();

    // User Tab Listeners
    addNewUserBtn.addEventListener('click', () => openUserModal());
    closeUserModalBtn.addEventListener('click', () => userModal.style.display = 'none');
    closeCredentialsModalBtn.addEventListener('click', () => credentialsModal.style.display = 'none');
    userForm.addEventListener('submit', handleUserFormSubmit);
    userSearchInput.addEventListener('input', () => {
        userCurrentPage = 1;
        renderFilteredAndSortedUsers();
    });

    sortableHeaders.forEach(header => {
        header.addEventListener('click', () => {
            const column = header.dataset.column;
            if (currentSort.column === column) {
                currentSort.direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
            } else {
                currentSort.column = column;
                currentSort.direction = 'asc';
            }
            userCurrentPage = 1;
            renderFilteredAndSortedUsers();
        });
    });

    userPrevPageBtn.addEventListener('click', () => {
        if (userCurrentPage > 1) {
            userCurrentPage--;
            renderFilteredAndSortedUsers();
        }
    });

    userNextPageBtn.addEventListener('click', () => {
        // Re-filter to get total length for boundary check
        const searchTerm = userSearchInput.value.toLowerCase();
        const totalUsers = allUsers.filter(user => 
            !searchTerm || 
            user.full_name.toLowerCase().includes(searchTerm) ||
            user.email.toLowerCase().includes(searchTerm) ||
            user.id.toString().includes(searchTerm)
        ).length;
        
        if (userCurrentPage < Math.ceil(totalUsers / userRowsPerPage)) {
            userCurrentPage++;
            renderFilteredAndSortedUsers();
        }
    });

    usersTableBody.addEventListener('click', (e) => {
        const target = e.target.closest('button');
        if (!target) return;
        const userId = target.dataset.id;
        
        // Handle Deactivate/Reactivate clicks
        if (target.classList.contains('deactivate') || target.classList.contains('reactivate')) {
            // NEW RULE: Check if this is the last administrator before deactivating
            if (target.classList.contains('deactivate')) {
                const clickedUser = allUsers.find(u => u.id == userId);
                const adminCount = allUsers.filter(u => u.role_name === 'Administrator').length;
                
                if (clickedUser && clickedUser.role_name === 'Administrator' && adminCount === 1) {
                    showToastModal('The last administrator account cannot be deactivated.', svgError, 5000);
                    return; // Stop the function here
                }
            }
            
            // If the rule doesn't apply, proceed as normal
            setUserStatus(userId, target.dataset.status);
            return;
        }
        
        // Handle other button clicks
        if (!userId) return;

        if (target.classList.contains('edit-btn')) {
            apiFetch(`/api/users/${userId}`).then(user => openUserModal(user));
        } else if (target.classList.contains('reset-pw')) {
            resetUserPassword(userId);
        }
    });

    // Audit Log Listeners
    flatpickr(auditDateFilter, { mode: "range", dateFormat: "Y-m-d", onChange: () => { auditCurrentPage = 1; loadAuditLogs(); } });
    auditUserFilter.addEventListener('input', () => { auditCurrentPage = 1; loadAuditLogs(); });
    auditActionFilter.addEventListener('input', () => { auditCurrentPage = 1; loadAuditLogs(); });
    exportAuditCsvBtn.addEventListener('click', exportAuditLogToCSV);
    exportAuditPdfBtn.addEventListener('click', exportAuditLogToPDF);

    auditSortableHeaders.forEach(header => {
        header.addEventListener('click', () => {
            const column = header.dataset.column;
            if (currentAuditSort.column === column) {
                currentAuditSort.direction = currentAuditSort.direction === 'asc' ? 'desc' : 'asc';
            } else {
                currentAuditSort.column = column;
                currentAuditSort.direction = 'asc';
            }
            auditCurrentPage = 1;
            renderFilteredAndSortedAuditLogs();
        });
    });

    auditPrevPageBtn.addEventListener('click', () => {
        if (auditCurrentPage > 1) {
            auditCurrentPage--;
            renderFilteredAndSortedAuditLogs();
        }
    });

    auditNextPageBtn.addEventListener('click', () => {
        if (auditCurrentPage < Math.ceil(auditLogData.length / auditRowsPerPage)) {
            auditCurrentPage++;
            renderFilteredAndSortedAuditLogs();
        }
    });

    // --- Event listeners for the protected role modal ---
    closeProtectedRoleModalBtn.addEventListener('click', () => {
        protectedRoleModal.style.display = 'none';
    });

    // Also close the modal if the user clicks on the overlay background
    protectedRoleModal.addEventListener('click', (event) => {
        if (event.target === protectedRoleModal) {
            protectedRoleModal.style.display = 'none';
        }
    });
    
    // Phone Number Input Formatting
    userPhoneNumberInput.addEventListener('focus', () => {
        if (userPhoneNumberInput.value === '') userPhoneNumberInput.value = '+639';
    });
    // Enforces the format during input
    userPhoneNumberInput.addEventListener('input', () => {
        let value = userPhoneNumberInput.value;

        // 1. Ensure the prefix is always present
        if (!value.startsWith('+639')) {
            value = '+639';
        }

        // 2. Allow only numbers after the prefix
        const numericPart = value.substring(4).replace(/[^0-9]/g, '');
        
        // 3. Combine prefix and the cleaned numeric part
        userPhoneNumberInput.value = '+639' + numericPart;
    });

    // Prevents the user from deleting the prefix
    userPhoneNumberInput.addEventListener('keydown', (e) => {
        const selectionStart = e.target.selectionStart;
        if (selectionStart < 4 && (e.key === 'Backspace' || e.key === 'Delete')) {
            e.preventDefault();
        }
    });
});