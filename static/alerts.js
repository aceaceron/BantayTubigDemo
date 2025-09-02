// static/alerts.js
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

document.addEventListener('DOMContentLoaded', function() {
    
    // --- INITIALIZE GLOBAL NAVIGATION ---
    setupGlobalNavigation();
    
    // --- GLOBAL NAVIGATION AND TOAST SETUP ---
    const { showToast, svgSuccess, svgError } = setupToastNotifications();

    // --- STATE MANAGEMENT ---
    let allUsers = []; // Cache for user list to populate forms
    let allGroups = []; // Cache for group list
    let allPolicies = []; // Cache for policy list
    let allThresholds = []; 
    let alertHistoryData = []; // Cache for all alert history logs
    let historyCurrentPage = 1;
    const historyRowsPerPage = 10;

    // --- TABS LOGIC ---
    const tabLinks = document.querySelectorAll('.tab-link');
    const tabContents = document.querySelectorAll('.tab-content');
    tabLinks.forEach(link => {
        link.addEventListener('click', () => {
            // --- This part handles the visual switching ---
            tabLinks.forEach(l => l.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            link.classList.add('active');
            const tabId = link.dataset.tab;
            document.getElementById(tabId).classList.add('active');

            if (tabId === 'rules') {
                loadAlertRules();
            } else if (tabId === 'settings') {
                // The settings tab contains two tables
                loadNotificationGroups();
                loadEscalationPolicies();
            }  else if (tabId === 'thresholds') { 
                loadThresholds();
            } else if (tabId === 'history') {
                loadAlertHistory();
            }
        });
    });

    // --- MODAL HANDLING ---
    const { openModal, closeModal } = setupModalHandlers();

    // --- API HELPER FUNCTION ---
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
            throw error;
        }
    }

    // --- ALERT RULES TAB ---
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
    
    // --- Rule Creation Constants ---
    const RULE_PARAMETERS = ['Temperature', 'pH', 'TDS', 'Turbidity'];
    const RULE_OPERATORS = ['>', '<', '=', '>=', '<='];

    async function loadAlertRules() {
        try {
            const rules = await apiFetch('/api/alerts/rules');
            renderRulesTable(rules);
        } catch (error) {
            alertRulesTableBody.innerHTML = `<tr><td colspan="5">Failed to load rules.</td></tr>`;
        }
    }

    function renderRulesTable(rules) {
        alertRulesTableBody.innerHTML = '';
        if (rules.length === 0) {
            alertRulesTableBody.innerHTML = `<tr><td colspan="5">No alert rules configured.</td></tr>`;
            return;
        }

        const now = new Date();
        rules.forEach(rule => {
            const tr = document.createElement('tr');
            
            // Check if the rule is currently snoozed
            const snoozedUntil = rule.snoozed_until ? new Date(rule.snoozed_until) : null;
            const isSnoozed = snoozedUntil && snoozedUntil > now;

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

    function populateRuleModalDropdowns() {
        const groupOptions = allGroups.map(g => `<option value="${g.id}">${g.name}</option>`).join('');
        ruleNotifyGroupSelect.innerHTML = groupOptions;
        const policyOptions = allPolicies.map(p => `<option value="${p.id}">${p.name}</option>`).join('');
        ruleEscalationPolicySelect.innerHTML = '<option value="">None</option>' + policyOptions;
    }

    // Function to dynamically add a condition row to the UI
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


    // --- Rule Modal Event Listeners ---

    // Listener for the "Add New Rule" button
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
        if (confirm('Are you sure you want to restore the default alert rules? Any changes you made to them will be lost.')) {
            apiFetch('/api/alerts/rules/restore_defaults', { method: 'POST' })
                .then(() => {
                    showToast('Default rules have been restored.', svgSuccess);
                    loadAlertRules();
                });
        }
    });
    
    addConditionBtn.addEventListener('click', () => addConditionRow());

    ruleConditionsContainer.addEventListener('click', e => {
        if (e.target.classList.contains('remove-condition-btn')) {
            e.target.closest('.condition-row').remove();
        }
    });
    
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
                return; // Stop the function here
            }
            
            // If not protected, proceed with the confirmation and deletion.
            if (confirm('Are you sure you want to delete this rule?')) {
                apiFetch(`/api/alerts/rules/${ruleId}`, { method: 'DELETE' })
                    .then(() => {
                        showToast('Rule deleted successfully.', svgSuccess);
                        loadAlertRules();
                    });
            }
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

    ruleForm.addEventListener('submit', async e => {
        e.preventDefault();
        const conditions = [];
        const conditionRows = ruleConditionsContainer.querySelectorAll('.condition-row');
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

    snoozeForm.addEventListener('submit', async e => {
        e.preventDefault();
        const ruleId = snoozeRuleIdInput.value;
        const duration = document.getElementById('snoozeDuration').value;

        await apiFetch(`/api/alerts/rules/${ruleId}/snooze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ duration_minutes: parseInt(duration) })
        });

        showToast('Rule has been snoozed.', svgSuccess);
        closeModal('snoozeModal');
        loadAlertRules(); // Refresh the table to show the "Snoozed" badge
    });


    // --- NOTIFICATION SETTINGS TAB ---
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


    async function loadNotificationGroups() {
        try {
            allGroups = await apiFetch('/api/alerts/groups');
            renderGroupsTable(allGroups);
        } catch (error) {
            notificationGroupsTableBody.innerHTML = `<tr><td colspan="3">Failed to load groups.</td></tr>`;
        }
    }
    
    async function loadEscalationPolicies() {
        try {
            allPolicies = await apiFetch('/api/alerts/policies');
            renderPoliciesTable(allPolicies);
        } catch(error) {
            escalationPoliciesTableBody.innerHTML = `<tr><td colspan="3">Failed to load policies.</td></tr>`;
        }
    }

    function renderGroupsTable(groups) {
        notificationGroupsTableBody.innerHTML = '';
        if (groups.length === 0) { 
            notificationGroupsTableBody.innerHTML = `<tr><td colspan="3">No notification groups defined.</td></tr>`;
            return; 
        }
        groups.forEach(group => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${group.name}</td>
                <td>${group.member_count} users</td>
                <td class="action-buttons-cell">
                    <button class="action-button small edit-group-btn" data-id="${group.id}">Edit</button>
                    <button class="action-button small deactivate delete-group-btn" data-id="${group.id}">Delete</button>
                </td>
            `;
            notificationGroupsTableBody.appendChild(tr);
        });
    }

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

    function formatEscalationPath(path) {
        if (!path || !Array.isArray(path) || path.length === 0) {
            return 'No path defined.';
        }
        // The 'allGroups' variable is already loaded by your script
        if (!allGroups || allGroups.length === 0) {
            return 'Loading group names...';
        }

        const steps = path.map(step => {
            // Find the group's name from its ID
            const group = allGroups.find(g => g.id == step.group_id);
            const groupName = group ? group.name : `Unknown Group (ID: ${step.group_id})`;
            
            return `Notify <b>${groupName}</b> & wait ${step.wait_minutes} min`;
        });

        return steps.join(' → '); // Join steps with an arrow
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
    
    // --- Group Modal Logic ---
    addNewGroupBtn.addEventListener('click', () => {
        groupForm.reset();
        groupIdInput.value = '';
        groupModalTitle.textContent = 'Add New Group';
        renderGroupMembersChecklist(allUsers);
        openModal('groupModal');
    });

    // Add click listener for the "Add New Policy" button
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


    notificationGroupsTableBody.addEventListener('click', async e => {
        const target = e.target;
        const groupId = target.dataset.id;
        if (target.classList.contains('edit-group-btn')) {
            groupForm.reset();
            groupModalTitle.textContent = 'Edit Group';
            const groupDetails = await apiFetch(`/api/alerts/groups/${groupId}`);
            groupIdInput.value = groupDetails.id;
            groupNameInput.value = groupDetails.name;
            renderGroupMembersChecklist(allUsers, groupDetails.members);
            openModal('groupModal');
        } else if (target.classList.contains('delete-group-btn')) {
             if (confirm('Are you sure you want to delete this group?')) {
                apiFetch(`/api/alerts/groups/${groupId}`, { method: 'DELETE' })
                    .then(() => {
                        showToast('Group deleted.', svgSuccess);
                        loadNotificationGroups();
                        loadEscalationPolicies(); // Reload in case a policy used this group
                    });
            }
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
        loadEscalationPolicies(); // A group name might have changed
    });


    function renderGroupMembersChecklist(users, selectedMemberIds = []) {
        groupMembersChecklist.innerHTML = users.map(user => `
            <label class="checklist-item">
                <input type="checkbox" value="${user.id}" ${selectedMemberIds.includes(user.id) ? 'checked' : ''}>
                ${user.full_name}
            </label>
        `).join('');
    }

    // --- Policy Modal Logic ---
    addNewPolicyBtn.addEventListener('click', () => {
        policyForm.reset();
        policyIdInput.value = '';
        policyModalTitle.textContent = 'Add New Escalation Policy';
        policyStepsContainer.innerHTML = ''; // Clear previous steps
        addPolicyStep(); // Add one empty step to start with
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
            if (confirm('Are you sure you want to delete this policy?')) {
                apiFetch(`/api/alerts/policies/${policyId}`, { method: 'DELETE' })
                    .then(() => {
                        showToast('Policy deleted.', svgSuccess);
                        loadEscalationPolicies();
                    });
            }
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
        const groupOptions = allGroups.map(g => `<option value="${g.id}" ${step.group_id == g.id ? 'selected' : ''}>${g.name}</option>`).join('');

        div.innerHTML = `
            <span>Step:</span>
            <select class="policy-group-select">${groupOptions}</select>
            <span>Wait for</span>
            <input type="number" class="policy-wait-input" min="1" value="${step.wait_minutes || 15}">
            <span>minutes, then escalate.</span>
            <button type="button" class="remove-condition-btn">&times;</button>
        `;
        policyStepsContainer.appendChild(div);
    }

    // --- THRESHOLDS TAB ---
    const thresholdsTableBody = document.querySelector('#thresholdsTable tbody');
    const restoreDefaultThresholdsBtn = document.getElementById('restoreDefaultThresholdsBtn');
    const thresholdForm = document.getElementById('thresholdForm');
    const thresholdIdInput = document.getElementById('thresholdId');
    const thresholdLabel = document.getElementById('thresholdLabel');
    const thresholdMinValueInput = document.getElementById('thresholdMinValue');
    const thresholdMaxValueInput = document.getElementById('thresholdMaxValue');

    async function loadThresholds() {
        try {
            allThresholds = await apiFetch('/api/thresholds');
            renderThresholdsTable(allThresholds);
        } catch (error) {
            thresholdsTableBody.innerHTML = `<tr><td colspan="5">Failed to load thresholds.</td></tr>`;
        }
    }

    function renderThresholdsTable(thresholds) {
        thresholdsTableBody.innerHTML = '';
        thresholds.forEach(t => {
            const tr = document.createElement('tr');
            // Use ?? to show 'N/A' for null values, which is more user-friendly
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

    // Event listener for the restore defaults button
    restoreDefaultThresholdsBtn.addEventListener('click', () => {
        if (confirm('Are you sure you want to restore all thresholds to their default values? This cannot be undone.')) {
            apiFetch('/api/thresholds/restore', { method: 'POST' })
                .then(() => {
                    showToast('Default thresholds have been restored.', svgSuccess);
                    loadThresholds(); // Refresh the table
                });
        }
    });

    // Event listener for the table (to catch clicks on "Edit" buttons)
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

    // Event listener for the modal form submission
    thresholdForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const thresholdId = thresholdIdInput.value;
        const thresholdData = {
            min_value: thresholdMinValueInput.value,
            max_value: thresholdMaxValueInput.value
        };

        try {
            await apiFetch(`/api/thresholds/${thresholdId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(thresholdData)
            });
            showToast('Threshold updated successfully.', svgSuccess);
            closeModal('thresholdModal');
            loadThresholds(); // Refresh the table with new values
        } catch (error) {
            // Error is already handled by apiFetch
        }
    });
    
    // --- ALERT HISTORY TAB ---
    // *** Element selectors for filters and pagination ***
    const alertHistoryTableBody = document.querySelector('#alertHistoryTable tbody');
    const historyDateFilter = document.getElementById('historyDateFilter');
    const historyRuleFilter = document.getElementById('historyRuleFilter');
    const historyStatusFilter = document.getElementById('historyStatusFilter');
    const historyPrevPageBtn = document.getElementById('historyPrevPageBtn');
    const historyNextPageBtn = document.getElementById('historyNextPageBtn');
    const historyPageInfo = document.getElementById('historyPageInfo');

    // *** Initialize flatpickr on the date filter input ***
    const historyDatePicker = flatpickr(historyDateFilter, {
        mode: "range",
        dateFormat: "Y-m-d",
        onChange: () => {
            historyCurrentPage = 1;
            renderFilteredHistory();
        }
    });

    async function loadAlertHistory() {
        try {
            // Data is now stored in the global state variable
            alertHistoryData = await apiFetch('/api/alerts/history');
            historyCurrentPage = 1; // Reset to first page
            renderFilteredHistory(); // Call the new central rendering function
        } catch (error) {
            alertHistoryTableBody.innerHTML = `<tr><td colspan="6">Failed to load history.</td></tr>`;
        }
    }

    function renderFilteredHistory() {
        let filteredData = [...alertHistoryData];

        // Apply date range filter from flatpickr
        if (historyDatePicker.selectedDates.length === 2) {
            const startDate = historyDatePicker.selectedDates[0].setHours(0, 0, 0, 0);
            const endDate = historyDatePicker.selectedDates[1].setHours(23, 59, 59, 999);
            filteredData = filteredData.filter(log => {
                const logDate = new Date(log.timestamp).getTime();
                return logDate >= startDate && logDate <= endDate;
            });
        }
        
        // Apply rule name filter
        const ruleFilter = historyRuleFilter.value.toLowerCase();
        if (ruleFilter) {
            filteredData = filteredData.filter(log => log.rule_name.toLowerCase().includes(ruleFilter));
        }

        // Apply status filter
        const statusFilter = historyStatusFilter.value;
        if (statusFilter) {
            filteredData = filteredData.filter(log => log.status === statusFilter);
        }

        // Pass the final filtered data to the table renderer
        renderHistoryTable(filteredData);
    }

    // *** MODIFIED: This function now handles pagination ***
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

    // *** Function to update pagination controls ***
    function updateHistoryPagination(totalLogs) {
        const totalPages = Math.ceil(totalLogs / historyRowsPerPage) || 1;
        historyPageInfo.textContent = `Page ${historyCurrentPage} of ${totalPages}`;
        historyPrevPageBtn.disabled = historyCurrentPage === 1;
        historyNextPageBtn.disabled = historyCurrentPage >= totalPages;
    }

   // *** Event listeners for filters and pagination buttons ***
    historyRuleFilter.addEventListener('input', () => { historyCurrentPage = 1; renderFilteredHistory(); });
    historyStatusFilter.addEventListener('change', () => { historyCurrentPage = 1; renderFilteredHistory(); });

    alertHistoryTableBody.addEventListener('click', e => {
        if (e.target.classList.contains('ack-btn')) {
            apiFetch(`/api/alerts/history/${e.target.dataset.id}/acknowledge`, { method: 'POST' }).then(() => {
                showToast('Alert acknowledged.', svgSuccess);
                loadAlertHistory(); // Reload all data after acknowledging
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
        // The check for disabling the button is now in updateHistoryPagination
        historyCurrentPage++;
        renderFilteredHistory();
    });
    
    // --- UTILITY & HELPER FUNCTIONS ---
    function formatConditions(conditions) {
        if (!conditions || conditions.length === 0) return 'No conditions set.';
        return conditions.map(c => `<b>${c.parameter}</b> ${c.operator} ${c.value}`).join('<br>');
    }
    
    async function loadInitialData() {
    try {
        [allUsers, allGroups] = await Promise.all([
            apiFetch('/api/alerts/users_for_groups'),
            apiFetch('/api/alerts/groups')
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