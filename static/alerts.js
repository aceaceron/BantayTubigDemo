// static/alerts.js

/**
 * ========================================================================
 * UNIVERSAL SIDEBAR SCRIPT
 * Manages the slide-out navigation menu, present on all pages.
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
 * has been loaded and is ready (thanks to 'DOMContentLoaded').
 * ========================================================================
 */
document.addEventListener('DOMContentLoaded', function() {
    
    // --- INITIALIZE GLOBAL COMPONENTS ---
    setupGlobalNavigation();
    const { showToast, svgSuccess, svgError } = setupToastNotifications();
    const { openModal, closeModal } = setupModalHandlers();

    // --- STATE MANAGEMENT ---
    // These variables store data fetched from the server. Caching them here avoids
    // making unnecessary API calls every time a modal is opened.
    let allUsers = []; 
    let allGroups = []; 
    let allPolicies = []; 
    let allThresholds = []; 
    let alertHistoryData = []; // Stores the complete, unfiltered history log.
    let historyCurrentPage = 1;
    const historyRowsPerPage = 10; // How many history items to show per page.

    // --- TABS LOGIC ---
    // This section handles the main navigation for the page (Rules, Settings, History, etc.).
    const tabLinks = document.querySelectorAll('.tab-link');
    const tabContents = document.querySelectorAll('.tab-content');
    tabLinks.forEach(link => {
        link.addEventListener('click', () => {
            // Hide all tabs and content panels.
            tabLinks.forEach(l => l.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            // Show the clicked tab and its corresponding content panel.
            link.classList.add('active');
            const tabId = link.dataset.tab;
            document.getElementById(tabId).classList.add('active');

            // Load data for the newly activated tab to ensure it's up-to-date.
            if (tabId === 'rules') {
                loadAlertRules();
            } else if (tabId === 'settings') {
                loadNotificationGroups();
                loadEscalationPolicies();
            } else if (tabId === 'thresholds') { 
                loadThresholds();
            } else if (tabId === 'history') {
                loadAlertHistory();
            }
        });
    });
    
    // --- CONFIRMATION MODAL LOGIC ---
    // This sets up a reusable confirmation pop-up for dangerous actions like deleting.
    const confirmationModalTitle = document.getElementById('confirmationModalTitle');
    const confirmationModalText = document.getElementById('confirmationModalText');
    let confirmationConfirmBtn = document.getElementById('confirmationConfirmBtn');
    const confirmationCancelBtn = document.getElementById('confirmationCancelBtn');

    /**
     * Shows a confirmation modal and executes a specific action (callback) if the user confirms.
     * How it works:
     * 1. It takes a title, text, and a function (`onConfirm`) as arguments.
     * 2. It populates the modal with the provided title and text.
     * 3. It clones the 'Confirm' button to remove any old event listeners, preventing bugs where
     * an action might be triggered multiple times. This is a crucial step for reusable modals.
     * 4. It attaches a new event listener that, when clicked, runs the `onConfirm` function.
     * @param {string} title - The title for the modal.
     * @param {string} text - The descriptive text in the modal.
     * @param {function} onConfirm - The function to call if the user clicks "Confirm".
     */
    function showConfirmationModal(title, text, onConfirm) {
        confirmationModalTitle.textContent = title;
        confirmationModalText.textContent = text;
        
        // This trick removes any lingering event listeners from previous calls.
        const newConfirmBtn = confirmationConfirmBtn.cloneNode(true);
        confirmationConfirmBtn.parentNode.replaceChild(newConfirmBtn, confirmationConfirmBtn);
        confirmationConfirmBtn = newConfirmBtn;
        
        confirmationConfirmBtn.addEventListener('click', () => {
            onConfirm(); // Execute the specific action for this confirmation.
            closeModal('confirmationModal');
        });

        confirmationCancelBtn.onclick = () => closeModal('confirmationModal');
        openModal('confirmationModal');
    }

    // --- API HELPER FUNCTION ---
    /**
     * A wrapper for the native `fetch` API to centralize logic and error handling.
     * How it works:
     * 1. It makes the API call.
     * 2. It automatically tries to parse the response as JSON.
     * 3. It checks if the response was successful (e.g., status 200 OK).
     * 4. If not successful, it throws an error using the message from the server's response.
     * 5. It includes a global `catch` block to show a user-friendly error toast message.
     * This simplifies all other functions because they don't need their own try/catch blocks.
     */
    async function apiFetch(url, options = {}) {
        try {
            const response = await fetch(url, options);
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.message || `HTTP error! status: ${response.status}`);
            }
            return data;
        } catch (error) {
            console.error('API Fetch Error:', error);
            showToast(`Error: ${error.message}`, svgError, 5000);
            throw error; // Re-throw the error so the calling function knows it failed.
        }
    }

    // ========================================================================
    // == ALERT RULES TAB LOGIC ===============================================
    // ========================================================================
    const alertRulesTableBody = document.querySelector('#alertRulesTable tbody');
    const ruleForm = document.getElementById('ruleForm');
    const addNewRuleBtn = document.getElementById('addNewRuleBtn');
    const restoreDefaultRulesBtn = document.getElementById('restoreDefaultRulesBtn');
    const ruleModalTitle = document.getElementById('ruleModalTitle');
    const ruleIdInput = document.getElementById('ruleId');
    const ruleNameInput = document.getElementById('ruleName');
    const ruleConditionsContainer = document.getElementById('ruleConditionsContainer');
    const addConditionBtn = document.getElementById('addConditionBtn');
    const ruleNotifyGroupSelect = document.getElementById('ruleNotifyGroup');
    const ruleEscalationPolicySelect = document.getElementById('ruleEscalationPolicy');
    const ruleEnabledCheckbox = document.getElementById('ruleEnabled');
    const ruleActivateBuzzerCheckbox = document.getElementById('ruleActivateBuzzer'); 
    const ruleBuzzerDurationInput = document.getElementById('ruleBuzzerDuration');
    const ruleBuzzerModeSelect = document.getElementById('ruleBuzzerMode');
    const snoozeModal = document.getElementById('snoozeModal');
    const snoozeForm = document.getElementById('snoozeForm');
    const snoozeRuleIdInput = document.getElementById('snoozeRuleId');
    const snoozeModalTitle = document.getElementById('snoozeModalTitle');
    
   // Constants for populating dropdowns in the rule builder.
    const RULE_PARAMETERS = ['Temperature', 'pH', 'TDS', 'Turbidity'];
    const RULE_OPERATORS = ['>', '<', '=', '>=', '<='];

    /** Fetches all alert rules from the server and triggers the rendering function. */
    async function loadAlertRules() {
        try {
            const rules = await apiFetch('/api/alerts/rules');
            renderRulesTable(rules);
        } catch (error) {
            alertRulesTableBody.innerHTML = `<tr><td colspan="5">Failed to load rules.</td></tr>`;
        }
    }

    /**
     * Clears and repopulates the alert rules table with fresh data.
     * @param {Array} rules - An array of rule objects from the server.
     */
    function renderRulesTable(rules) {
        alertRulesTableBody.innerHTML = ''; // Clear existing content.
        if (rules.length === 0) {
            alertRulesTableBody.innerHTML = `<tr><td colspan="5">No alert rules configured.</td></tr>`;
            return;
        }

        const now = new Date();
        rules.forEach(rule => {
            const tr = document.createElement('tr');
            const snoozedUntil = rule.snoozed_until ? new Date(rule.snoozed_until) : null;
            const isSnoozed = snoozedUntil && snoozedUntil > now; // Check if the snooze is still active.

            // Build the HTML for a single table row.
            tr.innerHTML = `
                <td>
                    ${rule.name} 
                    ${rule.is_default ? ' <span class="default-badge">Default</span>' : ''}
                    ${isSnoozed ? ` <span class="snooze-badge">Snoozed until ${snoozedUntil.toLocaleTimeString()}</span>` : ''}
                </td>
                <td>${formatConditions(rule.conditions)}</td>
                <td>${rule.group_name || 'N/A'}</td>
                <td><span class="status-badge ${rule.enabled ? 'status-active' : 'status-inactive'}">${rule.enabled ? 'Enabled' : 'Disabled'}</span></td>
                <td class="action-buttons-cell">
                    <button class="action-button small snooze-btn" data-id="${rule.id}" data-name="${rule.name}">Snooze</button>
                    <button class="action-button small edit-rule-btn" data-id="${rule.id}">Edit</button>
                    <button class="action-button small deactivate delete-rule-btn ${rule.is_default ? 'protected-rule-btn' : ''}" data-id="${rule.id}">Delete</button>
                </td>
            `;
            alertRulesTableBody.appendChild(tr);
        });
    }

    /** Populates the dropdowns in the rule editor modal with the latest groups and policies. */
    function populateRuleModalDropdowns() {
        const groupOptions = allGroups.map(g => `<option value="${g.id}">${g.name}</option>`).join('');
        ruleNotifyGroupSelect.innerHTML = groupOptions;
        const policyOptions = allPolicies.map(p => `<option value="${p.id}">${p.name}</option>`).join('');
        ruleEscalationPolicySelect.innerHTML = '<option value="">None</option>' + policyOptions;
    }

    /**
     * Dynamically creates the HTML for a single condition editor row and adds it to the form.
     * @param {object} condition - An optional object with existing condition data (for editing).
     */
    function addConditionRow(condition = {}) {
        const div = document.createElement('div');
        div.className = 'condition-row';
        const paramOptions = RULE_PARAMETERS.map(p => `<option value="${p}" ${condition.parameter === p ? 'selected' : ''}>${p}</option>`).join('');
        const opOptions = RULE_OPERATORS.map(o => `<option value="${o}" ${condition.operator === o ? 'selected' : ''}>${o}</option>`).join('');
        div.innerHTML = `
            <select class="rule-parameter">${paramOptions}</select>
            <select class="rule-operator">${opOptions}</select>
            <input type="number" class="rule-value" placeholder="Value" value="${condition.value || ''}" required>
            <button type="button" class="remove-condition-btn">&times;</button>
        `;
        ruleConditionsContainer.appendChild(div);
    }
    
    function formatConditions(conditions) {
        if (!conditions || conditions.length === 0) return 'No conditions set.';
        return conditions.map(c => `<b>${c.parameter}</b> ${c.operator} ${c.value}`).join('<br>');
    }

    /** Event listener for the main table body to handle clicks on Edit, Delete, or Snooze buttons. */
    alertRulesTableBody.addEventListener('click', async e => {
        const target = e.target;
        const ruleId = target.dataset.id;
        if (target.classList.contains('edit-rule-btn')) {
            const rule = await apiFetch(`/api/alerts/rules/${ruleId}`);
            if (!rule) return;
            ruleForm.reset();
            ruleModalTitle.textContent = 'Edit Alert Rule';
            populateRuleModalDropdowns();
            ruleConditionsContainer.innerHTML = '';
            ruleIdInput.value = rule.id;
            ruleNameInput.value = rule.name;
            ruleNotifyGroupSelect.value = rule.notification_group_id;
            ruleEscalationPolicySelect.value = rule.escalation_policy_id || '';
            ruleEnabledCheckbox.checked = rule.enabled;
            ruleActivateBuzzerCheckbox.checked = rule.activate_buzzer;
            ruleBuzzerDurationInput.value = rule.buzzer_duration_seconds;
            ruleBuzzerModeSelect.value = rule.buzzer_mode || 'once';
            rule.conditions.forEach(condition => addConditionRow(condition));
            openModal('ruleModal');
        } 
        else if (target.classList.contains('delete-rule-btn')) {
            if (target.classList.contains('protected-rule-btn')) {
                showToast('Default rules cannot be deleted.', svgError);
                return;
            }
            showConfirmationModal(
                'Delete this Rule?',
                'This action cannot be undone.',
                () => {
                    apiFetch(`/api/alerts/rules/${ruleId}`, { method: 'DELETE' })
                        .then(() => {
                            showToast('Rule deleted successfully.', svgSuccess);
                            loadAlertRules();
                        });
                }
            );
        }
        else if (target.classList.contains('snooze-btn')) {
            const ruleId = target.dataset.id;
            const ruleName = target.dataset.name;
            snoozeRuleIdInput.value = ruleId;
            snoozeModalTitle.textContent = `Snooze: ${ruleName}`;
            snoozeForm.reset();
            openModal('snoozeModal');
        }
    });

    /** Handles the submission of the "Add/Edit Rule" form. */
    ruleForm.addEventListener('submit', async e => {
        e.preventDefault();
        const conditions = [];
        const conditionRows = ruleConditionsContainer.querySelectorAll('.condition-row');
        // 1. Gathers all data from the form inputs, including the dynamic condition rows.
        // 2. Packages the data into a JSON object.
        // 3. Determines if it's a new rule (POST) or an update (PUT) based on whether an ID exists.
        // 4. Sends the data to the server via the `apiFetch` helper.
        // 5. Closes the modal and reloads the rules table on success.
        conditionRows.forEach(row => {
            conditions.push({
                parameter: row.querySelector('.rule-parameter').value,
                operator: row.querySelector('.rule-operator').value,
                value: row.querySelector('.rule-value').value
            });
        });

        const ruleData = {
            name: ruleNameInput.value,
            conditions: conditions,
            notification_group_id: ruleNotifyGroupSelect.value,
            escalation_policy_id: ruleEscalationPolicySelect.value || null,
            enabled: ruleEnabledCheckbox.checked,
            activate_buzzer: ruleActivateBuzzerCheckbox.checked,
            buzzer_duration_seconds: ruleBuzzerDurationInput.value,
            buzzer_mode: ruleBuzzerModeSelect.value
        };

        const ruleId = ruleIdInput.value;
        const url = ruleId ? `/api/alerts/rules/${ruleId}` : '/api/alerts/rules';
        const method = ruleId ? 'PUT' : 'POST';

        await apiFetch(url, { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(ruleData) });
        showToast(`Rule ${ruleId ? 'updated' : 'saved'} successfully.`, svgSuccess);
        closeModal('ruleModal');
        loadAlertRules();
    });

    /** Handles the submission of the "Snooze Rule" form. */
    snoozeForm.addEventListener('submit', async e => {
        e.preventDefault();
        const ruleId = snoozeRuleIdInput.value;
        const duration = document.getElementById('snoozeDuration').value;
        // Sends the snooze request to the server.
        await apiFetch(`/api/alerts/rules/${ruleId}/snooze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ duration_minutes: parseInt(duration) })
        });
        showToast('Rule has been snoozed.', svgSuccess);
        closeModal('snoozeModal');
        loadAlertRules(); // Reload to show the "Snoozed" badge.
    });

    addNewRuleBtn.addEventListener('click', () => {
        ruleForm.reset();
        ruleIdInput.value = '';
        ruleModalTitle.textContent = 'Add New Alert Rule';
        ruleEnabledCheckbox.checked = true;
        ruleActivateBuzzerCheckbox.checked = false;
        ruleConditionsContainer.innerHTML = '';
        addConditionRow();
        populateRuleModalDropdowns();
        openModal('ruleModal');
    });

    restoreDefaultRulesBtn.addEventListener('click', () => {
        showConfirmationModal(
            'Restore Default Rules?',
            'Any changes you made to default rules will be lost. This cannot be undone.',
            () => {
                apiFetch('/api/alerts/rules/restore', { method: 'POST' })
                    .then(() => {
                        showToast('Default rules have been restored.', svgSuccess);
                        loadAlertRules();
                    });
            }
        );
    });
    
    addConditionBtn.addEventListener('click', () => addConditionRow());

    ruleConditionsContainer.addEventListener('click', e => {
        if (e.target.classList.contains('remove-condition-btn')) {
            e.target.closest('.condition-row').remove();
        }
    });
    
    
    // ========================================================================
    // == NOTIFICATION SETTINGS TAB LOGIC =====================================
    // ========================================================================
    const notificationGroupsTableBody = document.querySelector('#notificationGroupsTable tbody');
    const escalationPoliciesTableBody = document.querySelector('#escalationPoliciesTable tbody');
    const addNewGroupBtn = document.getElementById('addNewGroupBtn');
    const groupModalTitle = document.getElementById('groupModalTitle');
    const groupForm = document.getElementById('groupForm');
    const groupIdInput = document.getElementById('groupId');
    const groupNameInput = document.getElementById('groupName');
    const groupMembersChecklist = document.getElementById('groupMembersChecklist');
    const addNewPolicyBtn = document.getElementById('addNewPolicyBtn');
    const policyForm = document.getElementById('policyForm');
    const policyModalTitle = document.getElementById('policyModalTitle');
    const policyIdInput = document.getElementById('policyId');
    const policyNameInput = document.getElementById('policyName');
    const policyStepsContainer = document.getElementById('policyStepsContainer');
    const addPolicyStepBtn = document.getElementById('addPolicyStepBtn');

    /** Fetches notification groups and triggers the render function. */
    async function loadNotificationGroups() {
        try {
            allGroups = await apiFetch('/api/alerts/groups');
            renderGroupsTable(allGroups);
        } catch (error) {
            notificationGroupsTableBody.innerHTML = `<tr><td colspan="3">Failed to load groups.</td></tr>`;
        }
    }
    
    /** Fetches escalation policies and triggers the render function. */
    async function loadEscalationPolicies() {
        try {
            allPolicies = await apiFetch('/api/alerts/policies');
            renderPoliciesTable(allPolicies);
        } catch(error) {
            escalationPoliciesTableBody.innerHTML = `<tr><td colspan="3">Failed to load policies.</td></tr>`;
        }
    }

    /** Renders the table of notification groups. */
    function renderGroupsTable(groups) {
        notificationGroupsTableBody.innerHTML = '';
        if (groups.length === 0) {
            notificationGroupsTableBody.innerHTML = `<tr><td colspan="3">No notification groups defined.</td></tr>`;
            return;
        }

        groups.forEach(group => {
            const tr = document.createElement('tr');
            const isProtected = group.name === 'Administrators';
            tr.innerHTML = `
                <td>${group.name}</td>
                <td>${group.member_count} user/s</td>
                <td class="action-buttons-cell">
                    <button class="action-button small edit-group-btn" data-id="${group.id}">Edit</button>
                    <button 
                        class="action-button small deactivate delete-group-btn ${isProtected ? 'protected-btn' : ''}" 
                        data-id="${group.id}"
                    >
                        Delete
                    </button>
                </td>
            `;
            notificationGroupsTableBody.appendChild(tr);
        });
    }


    /** Renders the table of escalation policies. */
    function renderPoliciesTable(policies) {
        escalationPoliciesTableBody.innerHTML = '';
        if (policies.length === 0) {
            escalationPoliciesTableBody.innerHTML = `<tr><td colspan="3">No escalation policies defined.</td></tr>`;
            return;
        }
        policies.forEach(policy => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${policy.name}</td>
                <td>${formatEscalationPath(policy.path)}</td>
                <td class="action-buttons-cell">
                    <button class="action-button small edit-policy-btn" data-id="${policy.id}">Edit</button>
                    <button class="action-button small deactivate delete-policy-btn" data-id="${policy.id}">Delete</button>
                </td>
            `;
            escalationPoliciesTableBody.appendChild(tr);
        });
    }

    /**
     * Converts a policy's path data into a human-readable string.
     * e.g., "Wait 15 minutes, then notify On-Call Techs → Wait 10 minutes, then notify Managers"
     */
    function formatEscalationPath(path) {
        if (!path || !Array.isArray(path) || path.length === 0) {
            return 'No path defined.';
        }
        if (!allGroups || allGroups.length === 0) {
            return 'Loading group names...';
        }

        const steps = path.map(step => {
            const group = allGroups.find(g => g.id == step.group_id);
            const groupName = group ? group.name : `Unknown Group (ID: ${step.group_id})`;
            
            // Swap order: wait first, then notify
            return `Wait <b>${step.wait_minutes} minute/s</b>, then notify <b>${groupName}</b>`;
        });

        return steps.join(' → ');
    }

    /** Dynamically creates the user checklist for the group editor modal. */
    function renderGroupMembersChecklist(users, selectedMemberIds = []) {
        groupMembersChecklist.innerHTML = users.map(user => `
            <label class="checklist-item">
                <input type="checkbox" value="${user.id}" ${selectedMemberIds.includes(user.id) ? 'checked' : ''}>
                ${user.full_name}
            </label>
        `).join('');
    }

    async function openGroupModalForEdit(groupId) {
        groupForm.reset();
        groupModalTitle.textContent = 'Edit Group';
        
        try {
            const [group, users] = await Promise.all([
                apiFetch(`/api/alerts/groups/${groupId}`),
                apiFetch('/api/alerts/users_for_groups')
            ]);
            
            groupIdInput.value = group.id;
            groupNameInput.value = group.name;
            renderGroupMembersChecklist(users, group.members);
            openModal('groupModal');
        } catch (error) {
            showToast('Failed to load group details.', svgError);
        }
    }
    
    addNewGroupBtn.addEventListener('click', () => {
        groupForm.reset();
        groupIdInput.value = '';
        groupModalTitle.textContent = 'Add New Group';
        renderGroupMembersChecklist(allUsers);
        openModal('groupModal');
    });

    addNewPolicyBtn.addEventListener('click', () => {
        document.getElementById('policyForm').reset();
        openModal('policyModal');
    });

    groupForm.addEventListener('submit', async e => {
        e.preventDefault();
        const selectedMembers = [...groupMembersChecklist.querySelectorAll('input:checked')].map(input => input.value);
        const groupData = {
            name: groupNameInput.value,
            members: selectedMembers
        };
        const groupId = groupIdInput.value;
        const url = groupId ? `/api/alerts/groups/${groupId}` : '/api/alerts/groups';
        const method = groupId ? 'PUT' : 'POST';

        try {
            await apiFetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(groupData)
            });
            showToast(`Group ${groupId ? 'updated' : 'added'} successfully.`, svgSuccess);
            closeModal('groupModal');
            loadNotificationGroups();
        } catch(error) { /* Handled by apiFetch */ }
    });

    // Event listener for the notification groups table body
    notificationGroupsTableBody.addEventListener('click', async e => {
        const target = e.target;
        const groupId = target.dataset.id;

        // ✅ Delete button protection
        if (target.classList.contains('delete-group-btn') && target.classList.contains('protected-btn')) {
            showToast("The 'Administrators' group cannot be deleted.", svgError);
            return;
        }

        // ✅ Edit button clicked
        if (target.classList.contains('edit-group-btn')) {
            groupForm.reset();
            groupModalTitle.textContent = 'Edit Group';

            try {
                const [groupDetails, users] = await Promise.all([
                    apiFetch(`/api/alerts/groups/${groupId}`),
                    apiFetch('/api/alerts/users_for_groups')
                ]);
                
                groupIdInput.value = groupDetails.id;
                groupNameInput.value = groupDetails.name;

                // 🔒 Protect Administrators group name
                const isProtected = groupDetails.name === 'Administrators';
                groupNameInput.readOnly = isProtected;   // use readOnly instead of disabled
                groupNameInput.classList.toggle('protected-input', isProtected);

                renderGroupMembersChecklist(users, groupDetails.members);
                openModal('groupModal');

            } catch (error) {
                showToast('Failed to load group details.', svgError);
            }
        } 
        
        // ✅ Delete button (normal groups)
        else if (target.classList.contains('delete-group-btn')) {
            showConfirmationModal(
                'Delete this Group?',
                'This action cannot be undone. Rules using this group will no longer send notifications.',
                () => {
                    apiFetch(`/api/alerts/groups/${groupId}`, { method: 'DELETE' })
                        .then(() => {
                            showToast('Group deleted.', svgSuccess);
                            loadNotificationGroups();
                            loadEscalationPolicies();
                        });
                }
            );
        }
    });

    // ✅ Toast on click of protected input
    groupNameInput.addEventListener("click", e => {
        if (e.target.readOnly && e.target.classList.contains("protected-input")) {
            showToast("The 'Administrators' group name cannot be changed.", svgError);
        }
    });

    groupForm.addEventListener('submit', async e => {
        e.preventDefault();
        const selectedMembers = [...groupMembersChecklist.querySelectorAll('input:checked')].map(input => input.value);
        const groupData = { name: groupNameInput.value, members: selectedMembers };
        const groupId = groupIdInput.value;
        const url = groupId ? `/api/alerts/groups/${groupId}` : '/api/alerts/groups';
        const method = groupId ? 'PUT' : 'POST';

        await apiFetch(url, { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(groupData) });
        showToast(`Group ${groupId ? 'updated' : 'added'} successfully.`, svgSuccess);
        closeModal('groupModal');
        loadNotificationGroups();
        loadEscalationPolicies();
    });


    addNewPolicyBtn.addEventListener('click', () => {
        policyForm.reset();
        policyIdInput.value = '';
        policyModalTitle.textContent = 'Add New Escalation Policy';
        policyStepsContainer.innerHTML = '';
        addPolicyStep();
        openModal('policyModal');
    });

    escalationPoliciesTableBody.addEventListener('click', e => {
        const target = e.target;
        const policyId = target.dataset.id;
        if (target.classList.contains('edit-policy-btn')) {
            const policy = allPolicies.find(p => p.id == policyId);
            policyForm.reset();
            policyIdInput.value = policy.id;
            policyNameInput.value = policy.name;
            policyModalTitle.textContent = 'Edit Escalation Policy';
            policyStepsContainer.innerHTML = '';
            policy.path.forEach(step => addPolicyStep(step));
            openModal('policyModal');
        } else if (target.classList.contains('delete-policy-btn')) {
            showConfirmationModal(
                'Delete this Policy?',
                'This action cannot be undone. Rules using this policy will no longer escalate.',
                () => {
                    apiFetch(`/api/alerts/policies/${policyId}`, { method: 'DELETE' })
                        .then(() => {
                            showToast('Policy deleted.', svgSuccess);
                            loadEscalationPolicies();
                        });
                }
            );
        }
    });

    policyForm.addEventListener('submit', async e => {
        e.preventDefault();
        const path = [];
        const stepRows = policyStepsContainer.querySelectorAll('.condition-row');
        for (const row of stepRows) {
            path.push({
                group_id: row.querySelector('.policy-group-select').value,
                wait_minutes: row.querySelector('.policy-wait-input').value
            });
        }
        
        const policyData = { name: policyNameInput.value, path };
        const policyId = policyIdInput.value;
        const url = policyId ? `/api/alerts/policies/${policyId}` : '/api/alerts/policies';
        const method = policyId ? 'PUT' : 'POST';

        await apiFetch(url, { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(policyData) });
        showToast(`Policy ${policyId ? 'updated' : 'saved'} successfully.`, svgSuccess);
        closeModal('policyModal');
        loadEscalationPolicies();
    });

    addPolicyStepBtn.addEventListener('click', () => addPolicyStep());

    policyStepsContainer.addEventListener('click', e => {
        if (e.target.classList.contains('remove-condition-btn')) {
            e.target.closest('.condition-row').remove();
        }
    });

    function addPolicyStep(step = {}) {
        const div = document.createElement('div');
        div.className = 'condition-row';

        const groupOptions = allGroups
            .map(g => `<option value="${g.id}" ${step.group_id == g.id ? 'selected' : ''}>${g.name}</option>`)
            .join('');

        div.innerHTML = `
            <span>Wait</span>
            <input type="number" class="policy-wait-input" min="1" value="${step.wait_minutes || 15}">
            <span>minutes, then notify</span>
            <select class="policy-group-select">${groupOptions}</select>
            <button type="button" class="remove-condition-btn">&times;</button>
        `;

        policyStepsContainer.appendChild(div);
    }


    // ========================================================================
    // == THRESHOLDS TAB LOGIC ================================================
    // ========================================================================
    const thresholdsTableBody = document.querySelector('#thresholdsTable tbody');
    const restoreDefaultThresholdsBtn = document.getElementById('restoreDefaultThresholdsBtn');
    const thresholdForm = document.getElementById('thresholdForm');
    const thresholdIdInput = document.getElementById('thresholdId');
    const thresholdLabel = document.getElementById('thresholdLabel');
    const thresholdMinValueInput = document.getElementById('thresholdMinValue');
    const thresholdMaxValueInput = document.getElementById('thresholdMaxValue');

    /** Fetches the water quality thresholds and triggers the render function. */
    async function loadThresholds() {
        try {
            allThresholds = await apiFetch('/api/thresholds');
            renderThresholdsTable(allThresholds);
        } catch (error) {
            thresholdsTableBody.innerHTML = `<tr><td colspan="5">Failed to load thresholds.</td></tr>`;
        }
    }

    /** Renders the table of thresholds. */
    function renderThresholdsTable(thresholds) {
        thresholdsTableBody.innerHTML = '';
        thresholds.forEach(t => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${t.parameter_name}</td>
                <td>${t.quality_level} (${t.range_identifier})</td>
                <td>${t.min_value ?? 'N/A'}</td>
                <td>${t.max_value ?? 'N/A'}</td>
                <td class="action-buttons-cell">
                    <button class="action-button small edit-threshold-btn" data-id="${t.id}">Edit</button>
                </td>
            `;
            thresholdsTableBody.appendChild(tr);
        });
    }

    restoreDefaultThresholdsBtn.addEventListener('click', () => {
        showConfirmationModal(
            'Restore Default Thresholds?',
            'This will reset all thresholds to their original values. This action cannot be undone.',
            () => {
                apiFetch('/api/thresholds/restore', { method: 'POST' })
                    .then(() => {
                        showToast('Default thresholds have been restored.', svgSuccess);
                        loadThresholds();
                    });
            }
        );
    });

    thresholdsTableBody.addEventListener('click', e => {
        if (e.target.classList.contains('edit-threshold-btn')) {
            const thresholdId = e.target.dataset.id;
            const threshold = allThresholds.find(t => t.id == thresholdId);
            
            thresholdIdInput.value = threshold.id;
            thresholdLabel.textContent = `${threshold.parameter_name} - ${threshold.quality_level} (${threshold.range_identifier})`;
            thresholdMinValueInput.value = threshold.min_value;
            thresholdMaxValueInput.value = threshold.max_value;
            
            openModal('thresholdModal');
        }
    });

    thresholdForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const thresholdId = thresholdIdInput.value;
        const thresholdData = {
            min_value: thresholdMinValueInput.value || null,
            max_value: thresholdMaxValueInput.value || null
        };

        try {
            await apiFetch(`/api/thresholds/${thresholdId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(thresholdData)
            });
            showToast('Threshold updated successfully.', svgSuccess);
            closeModal('thresholdModal');
            loadThresholds();
        } catch (error) {
            // Error is already handled by apiFetch
        }
    });
    

    // ========================================================================
    // == ALERT HISTORY TAB LOGIC =============================================
    // ========================================================================
    const alertHistoryTableBody = document.querySelector('#alertHistoryTable tbody');
    const historyDateFilter = document.getElementById('historyDateFilter');
    const historyRuleFilter = document.getElementById('historyRuleFilter');
    const historyStatusFilter = document.getElementById('historyStatusFilter');
    const historyPrevPageBtn = document.getElementById('historyPrevPageBtn');
    const historyNextPageBtn = document.getElementById('historyNextPageBtn');
    const historyPageInfo = document.getElementById('historyPageInfo');

    /** Initializes the date range picker using the Flatpickr library. */
    const historyDatePicker = flatpickr(historyDateFilter, {
        mode: "range",
        dateFormat: "Y-m-d",
        onChange: () => {
            historyCurrentPage = 1;
            renderFilteredHistory();
        }
    });

    /** Fetches the entire alert history log from the server once. */
    async function loadAlertHistory() {
        try {
            alertHistoryData = await apiFetch('/api/alerts/history');
            historyCurrentPage = 1;
            renderFilteredHistory();
        } catch (error) {
            alertHistoryTableBody.innerHTML = `<tr><td colspan="6">Failed to load history.</td></tr>`;
        }
    }

    /**
     * Applies all active filters (date, rule, status) to the cached history data
     * before calling the function to render the table. This is efficient as it
     * doesn't require a new API call for every filter change.
     */
    function renderFilteredHistory() {
        let filteredData = [...alertHistoryData];

        if (historyDatePicker.selectedDates.length === 2) {
            const startDate = historyDatePicker.selectedDates[0].setHours(0, 0, 0, 0);
            const endDate = historyDatePicker.selectedDates[1].setHours(23, 59, 59, 999);
            filteredData = filteredData.filter(log => {
                const logDate = new Date(log.timestamp).getTime();
                return logDate >= startDate && logDate <= endDate;
            });
        }
        
        const ruleFilter = historyRuleFilter.value.toLowerCase();
        if (ruleFilter) {
            filteredData = filteredData.filter(log => log.rule_name.toLowerCase().includes(ruleFilter));
        }

        const statusFilter = historyStatusFilter.value;
        if (statusFilter) {
            filteredData = filteredData.filter(log => log.status === statusFilter);
        }

        renderHistoryTable(filteredData);
    }

    /**
     * Renders a single page of the history table.
     * @param {Array} history - The filtered list of history logs.
     */
    function renderHistoryTable(history) {
        alertHistoryTableBody.innerHTML = '';
        const start = (historyCurrentPage - 1) * historyRowsPerPage;
        const end = start + historyRowsPerPage;
        const paginatedHistory = history.slice(start, end);

        if (paginatedHistory.length === 0) { 
            alertHistoryTableBody.innerHTML = `<tr><td colspan="6">No alert history found for the selected filters.</td></tr>`;
        } else {
            paginatedHistory.forEach(log => {
                const tr = document.createElement('tr');
                const statusClass = `status-${log.status.toLowerCase()}`;
                tr.innerHTML = `
                    <td>${new Date(log.timestamp).toLocaleString()}</td>
                    <td>${log.rule_name}</td>
                    <td>${log.details}</td>
                    <td><span class="status-badge ${statusClass}">${log.status}</span></td>
                    <td>${log.acknowledged_by || 'N/A'}</td>
                    <td class="action-buttons-cell">
                        ${log.status === 'Triggered' ? `<button class="action-button small ack-btn" data-id="${log.id}">Acknowledge</button>` : ''}
                    </td>
                `;
                alertHistoryTableBody.appendChild(tr);
            });
        }
        updateHistoryPagination(history.length);
    }

    /** Updates the pagination controls (page info, button disabled states). */
    function updateHistoryPagination(totalLogs) {
        const totalPages = Math.ceil(totalLogs / historyRowsPerPage) || 1;
        historyPageInfo.textContent = `Page ${historyCurrentPage} of ${totalPages}`;
        historyPrevPageBtn.disabled = historyCurrentPage === 1;
        historyNextPageBtn.disabled = historyCurrentPage >= totalPages;
    }

    historyRuleFilter.addEventListener('input', () => { historyCurrentPage = 1; renderFilteredHistory(); });
    historyStatusFilter.addEventListener('change', () => { historyCurrentPage = 1; renderFilteredHistory(); });

    alertHistoryTableBody.addEventListener('click', e => {
        if (e.target.classList.contains('ack-btn')) {
            apiFetch(`/api/alerts/history/${e.target.dataset.id}/acknowledge`, { method: 'POST' }).then(() => {
                showToast('Alert acknowledged.', svgSuccess);
                loadAlertHistory();
            });
        }
    });

    historyPrevPageBtn.addEventListener('click', () => {
        if (historyCurrentPage > 1) {
            historyCurrentPage--;
            renderFilteredHistory();
        }
    });
    
    historyNextPageBtn.addEventListener('click', () => {
        historyCurrentPage++;
        renderFilteredHistory();
    });

    // ========================================================================
    // == INITIALIZATION ======================================================
    // ========================================================================
    /**
     * Fetches all necessary initial data (users, groups, policies) in parallel
     * to populate dropdowns and caches. Then, it loads the content for the default tab.
     */
    
    async function loadInitialData() {
        try {
            [allUsers, allGroups, allPolicies] = await Promise.all([
                apiFetch('/api/alerts/users_for_groups'),
                apiFetch('/api/alerts/groups'),
                apiFetch('/api/alerts/policies')
            ]);
        } catch (error) {
            console.error("Failed to load initial data for settings tab.");
        }
        loadAlertRules();
        renderGroupsTable(allGroups); 
        loadEscalationPolicies();
        loadAlertHistory();
    }

    // --- INITIALIZATION ---
    loadInitialData();
});

/** A factory function that sets up generic open/close logic for all modals. */
function setupModalHandlers() {
    const modals = document.querySelectorAll('.modal-overlay');
    const closeModalBtns = document.querySelectorAll('.modal-close-btn');

    function openModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'flex';
        }
    }

    function closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'none';
        }
    }

    closeModalBtns.forEach(btn => btn.addEventListener('click', () => closeModal(btn.dataset.modalId)));
    modals.forEach(modal => modal.addEventListener('click', e => {
        if (e.target === modal) {
            closeModal(modal.id);
        }
    }));

    return { openModal, closeModal };
}

/** A factory function that sets up the toast notification system. */
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