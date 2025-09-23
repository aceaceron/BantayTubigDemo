const saveMessage = document.getElementById("saveMessage");
const temperatureEl = document.getElementById("temperature");
const phEl = document.getElementById("ph");
const phVoltageEl = document.getElementById("ph_voltage");
const tdsEl = document.getElementById("tds");
const tdsVoltageEl = document.getElementById("tds_voltage");
const turbidityEl = document.getElementById("turbidity");
const turbidityVoltageEl = document.getElementById("turbidity_voltage");
const waterQualityEl = document.getElementById("water_quality");

// Prefill form from API
window.addEventListener("DOMContentLoaded", async () => {
  saveMessage.textContent = "Loading current settings...";
  try {
    const res = await fetch("/api/dev/settings/turbidity");
    if (!res.ok) throw new Error("Failed to fetch settings");
    const data = await res.json();
    document.getElementById("vHigh").value = data.V_REF_HIGH;
    document.getElementById("vLow").value = data.V_REF_LOW;
    saveMessage.textContent = "";
  } catch (err) {
    console.error("Could not fetch turbidity references:", err);
    saveMessage.innerHTML = `<p style="color:red;">Error loading settings. Please try again.</p>`;
  }
});

// === Secret Unlock for Turbidity Voltage References ===
let clickCount = 0;
const liveSensorCard = document.getElementById("liveSensorCard");
const turbidityCard = document.getElementById("turbidityCard");

function unlockTurbidity() {
    turbidityCard.style.display = "block"; // show the hidden section
    alert("Developer Mode: Turbidity Voltage References unlocked!");
    clickCount = 0; // reset after unlock
}

// === 10 quick taps unlock ===
liveSensorCard.addEventListener("click", () => {
    clickCount++;
    if (clickCount >= 10) {
        unlockTurbidity();
    }
});

// === Long press (10 seconds) unlock ===
let pressTimer;
liveSensorCard.addEventListener("mousedown", () => {
    pressTimer = setTimeout(unlockTurbidity, 10000); // hold for 10s
});
liveSensorCard.addEventListener("mouseup", () => {
    clearTimeout(pressTimer);
});
liveSensorCard.addEventListener("mouseleave", () => {
    clearTimeout(pressTimer);
});

// For mobile touch events
liveSensorCard.addEventListener("touchstart", () => {
    pressTimer = setTimeout(unlockTurbidity, 10000); // hold for 10s
});
liveSensorCard.addEventListener("touchend", () => {
    clearTimeout(pressTimer);
});

// Save form data to API
document.getElementById("turbidityForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const vHigh = parseFloat(document.getElementById("vHigh").value);
  const vLow = parseFloat(document.getElementById("vLow").value);

  saveMessage.textContent = "Saving...";
  try {
    const res = await fetch("/api/dev/settings/turbidity", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ V_REF_HIGH: vHigh, V_REF_LOW: vLow })
    });

    const data = await res.json();
    saveMessage.innerHTML = `<p style="color:${res.ok ? "green" : "red"};">${data.message}</p>`;
  } catch (err) {
    console.error("Save error:", err);
    saveMessage.innerHTML = `<p style="color:red;">Error saving settings.</p>`;
  }
});

// Poll latest sensor readings every 2 seconds
async function updateSensorReadings() {
  try {
    const res = await fetch("http://192.168.1.35:5000/analytics/latest");
    if (!res.ok) throw new Error("Failed to fetch latest sensor data");
    const data = await res.json();

    temperatureEl.textContent = data.temperature?.toFixed(2) ?? "--";
    phEl.textContent = data.ph?.toFixed(2) ?? "--";
    phVoltageEl.textContent = data.ph_voltage?.toFixed(3) ?? "--";
    tdsEl.textContent = data.tds?.toFixed(2) ?? "--";
    tdsVoltageEl.textContent = data.tds_voltage?.toFixed(3) ?? "--";
    turbidityEl.textContent = data.turbidity?.toFixed(2) ?? "--";
    turbidityVoltageEl.textContent = data.turbidity_voltage?.toFixed(3) ?? "--";
    waterQualityEl.textContent = data.water_quality ?? "--";

  } catch (err) {
    console.error("Error fetching sensor data:", err);
  } finally {
    setTimeout(updateSensorReadings, 2000);
  }
}

updateSensorReadings();

const consoleLog = document.getElementById("consoleLog");

async function fetchLogs() {
    try {
        const response = await fetch("/api/dev/logs");
        const data = await response.json();
        const consoleDiv = document.getElementById("consoleLog");
        consoleDiv.innerHTML = ""; // Clear previous

        data.logs.forEach(line => {
            const logLine = document.createElement("div");

            if (line.includes("!!! LOOP ERROR") || line.toLowerCase().includes("exception")) {
                logLine.style.color = "red";
            } else if (line.match(/Temp=|pH=|TDS=|Turb=/)) {
                logLine.style.color = "green";
            } else if (line.match(/GET|POST/)) {
                logLine.style.color = "blue";
            } else {
                logLine.style.color = "#fff"; // default white
            }

            logLine.textContent = line;
            consoleDiv.appendChild(logLine);
        });

        consoleDiv.scrollTop = consoleDiv.scrollHeight; // Auto-scroll
    } catch (err) {
        console.error("Failed to fetch logs:", err);
    }
}

let fontSize = 14; // initial font size

document.getElementById("zoomIn").addEventListener("click", () => {
    fontSize += 2;
    document.getElementById("consoleLog").style.fontSize = fontSize + "px";
});

document.getElementById("zoomOut").addEventListener("click", () => {
    fontSize = Math.max(8, fontSize - 2); // min 8px
    document.getElementById("consoleLog").style.fontSize = fontSize + "px";
});

const tableSelect = document.getElementById("tableSelect");
let currentTable = "";
let currentPage = 1;
let perPage = 10;
let sortColumn = null;
let sortDirection = "asc";
let searchTimeout;

// Populate table select
async function loadTables() {
    const res = await fetch("/api/dev/tables");
    const data = await res.json();
    tableSelect.innerHTML = data.tables.map(t => `<option value="${t}">${t}</option>`).join("");
    if(data.tables.length>0) { currentTable = data.tables[0]; fetchTable(); }
}
loadTables();


// Auto-load table on dropdown change
tableSelect.addEventListener("change", () => {
    currentPage = 1;  // reset to page 1 on table change
    fetchTable();
});

// Watch search input for live updates
document.getElementById("tableSearch").addEventListener("input", () => {
    // Debounce to avoid too many requests
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        currentPage = 1; // Reset page to 1 on search
        fetchTable();
    }, 300); // 300ms delay after typing stops
});

async function fetchTable() {
    currentTable = document.getElementById("tableSelect").value;
    const searchQuery = document.getElementById("tableSearch").value.trim();
    let url = `/api/dev/table/${currentTable}?page=${currentPage}&per_page=${perPage}`;

    if (sortColumn) url += `&sort_col=${sortColumn}&sort_dir=${sortDirection}`;
    if (searchQuery) url += `&search=${encodeURIComponent(searchQuery)}`;

    try {
        const res = await fetch(url);
        const data = await res.json();

        const thead = document.querySelector("#devTable thead");
        const tbody = document.querySelector("#devTable tbody");

        // Default sort state
        if (!sortColumn && data.columns.length > 0) {
            sortColumn = data.columns[0];   // first column
            sortDirection = "asc";          // ascending by default
        }

        // Build headers with sortable arrows
        thead.innerHTML = "<tr>" + data.columns.map(c => {
            let arrow = "";
            if (sortColumn === c) {
                arrow = sortDirection === "asc" ? " &#x25B2;" : " &#x25BC;"; // ▲ or ▼
            }
            return `<th data-col="${c}">${c}${arrow}</th>`;
        }).join("") + "<th>Actions</th></tr>";

        
        // Build insert form dynamically
        buildInsertForm(data.columns);

        // Build rows
        tbody.innerHTML = data.rows.map(row => {
            const cells = row.map(v => `<td contenteditable>${v}</td>`).join("");
            return `<tr data-id="${row[0]}">${cells}<td></td></tr>`; // last td for buttons
        }).join("");

        // Add sorting listeners
        thead.querySelectorAll("th[data-col]").forEach(th => {
            th.style.cursor = "pointer";
            th.addEventListener("click", () => {
                if(sortColumn === th.dataset.col){
                    sortDirection = sortDirection === "asc" ? "desc" : "asc";
                } else {
                    sortColumn = th.dataset.col;
                    sortDirection = "asc";
                }
                fetchTable();
            });
        });

        // Add buttons to each row
        tbody.querySelectorAll("tr").forEach(tr => {
            const actionTd = tr.lastElementChild;

            const saveBtn = document.createElement("button");
            saveBtn.textContent = "Save";
            saveBtn.classList.add("save-btn");
            saveBtn.onclick = () => saveRow(saveBtn, tr.dataset.id);

            const deleteBtn = document.createElement("button");
            deleteBtn.textContent = "Delete";
            deleteBtn.classList.add("delete-btn");
            deleteBtn.onclick = () => deleteRow(tr.dataset.id);

            actionTd.appendChild(saveBtn);
            actionTd.appendChild(deleteBtn);
        });

    } catch (err) {
        console.error("Failed to fetch table:", err);
    }
}

function buildInsertForm(columns) {
    const insertForm = document.getElementById("insertForm");
    insertForm.innerHTML = ""; // clear old

    columns.forEach(col => {
        if (col.toLowerCase() === "id" || col.toLowerCase().endsWith("id")) {
            return; // skip auto IDs
        }
        const input = document.createElement("input");
        input.type = "text";
        input.name = col;
        input.placeholder = col;
        insertForm.appendChild(input);
    });
}

// --- Drop entire table ---
async function dropTable() {
    if (!currentTable) {
        alert("Please select a table first.");
        return;
    }
    if (!confirm(`Are you sure you want to DROP the table "${currentTable}"? This cannot be undone!`)) return;

    try {
        const res = await fetch(`/api/dev/table/${currentTable}/drop`, {
            method: "POST"
        });
        const data = await res.json();

        if (res.ok) {
            alert(`Table "${currentTable}" dropped successfully.`);
            loadTables(); // reload list of tables
        } else {
            alert(`Error: ${data.error}`);
        }
    } catch (err) {
        console.error("Drop table error:", err);
        alert("Failed to drop table.");
    }
}

// --- Delete all rows from table ---
async function deleteAll() {
    if (!currentTable) {
        alert("Please select a table first.");
        return;
    }
    if (!confirm(`Are you sure you want to DELETE ALL rows from "${currentTable}"?`)) return;

    try {
        const res = await fetch(`/api/dev/table/${currentTable}/delete_all`, {
            method: "POST"
        });
        const data = await res.json();

        if (res.ok) {
            alert(`All rows deleted from "${currentTable}".`);
            fetchTable(); // refresh the table view
        } else {
            alert(`Error: ${data.error}`);
        }
    } catch (err) {
        console.error("Delete all rows error:", err);
        alert("Failed to delete all rows.");
    }
}

// --- Save row ---
async function saveRow(button, rowId) {
    const row = button.closest("tr");
    const data = {};
    row.querySelectorAll("td[contenteditable]").forEach(td => {
        const colIndex = Array.from(td.parentNode.children).indexOf(td);
        const colName = document.querySelector(`#devTable thead th:nth-child(${colIndex+1})`).dataset.col;
        data[colName] = td.textContent;
    });

    try {
        const res = await fetch(`/api/dev/table/${currentTable}/row/${rowId}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data)
        });
        const result = await res.json();

        if(res.ok) {
            button.textContent = "Saved!";
            setTimeout(() => button.textContent = "Save", 1000);
        } else {
            button.textContent = "Error!";
            console.error(result.error);
            setTimeout(() => button.textContent = "Save", 2000);
        }
    } catch (err) {
        console.error("Save error:", err);
        button.textContent = "Error!";
        setTimeout(() => button.textContent = "Save", 2000);
    }

    fetchTable();
}

// --- Delete row ---
async function deleteRow(rowId) {
    if (!confirm("Are you sure you want to delete this row?")) return;

    try {
        await fetch(`/api/dev/table/${currentTable}/row/${rowId}`, { method: "DELETE" });
        fetchTable();
    } catch (err) {
        console.error("Delete error:", err);
        alert("Failed to delete row.");
    }
}

// --- Insert row ---
async function insertRow() {
    const rowData = {};
    let valid = false;

    document.querySelectorAll("#insertForm input").forEach(input => {
        const value = input.value.trim();
        rowData[input.name] = value;
        if(value) valid = true;
    });

    if(!valid) {
        alert("Please enter at least one value.");
        return;
    }

    try {
        const res = await fetch(`/api/dev/table/${currentTable}/row`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(rowData)
        });
        if(!res.ok) {
            const data = await res.json();
            console.error("Insert error:", data.error);
            alert("Failed to insert row.");
        }
    } catch(err) {
        console.error("Insert error:", err);
        alert("Failed to insert row.");
    }

    // Clear form
    document.querySelectorAll("#insertForm input").forEach(input => input.value = "");
    fetchTable();
}

// Toggle dropdown
document.getElementById("exportBtn").addEventListener("click", () => {
    const menu = document.getElementById("exportMenu");
    menu.style.display = (menu.style.display === "block") ? "none" : "block";
});

// Close dropdown when clicking outside
window.addEventListener("click", (event) => {
    if (!event.target.matches("#exportBtn")) {
        document.getElementById("exportMenu").style.display = "none";
    }
});

// Helper: get today's date in YYYY-MM-DD
function getTodayDate() {
    const d = new Date();
    return d.toISOString().split("T")[0]; // YYYY-MM-DD
}

// === EXPORT FUNCTIONS ===

async function exportDatabase() {
    try {
        const res = await fetch("/api/dev/export/database");
        if (!res.ok) throw new Error("Export failed");

        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `BantayTubig_${getTodayDate()}.db`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
    } catch (err) {
        console.error("Export error:", err);
        alert("Failed to export database file.");
    }
}

async function exportSQL() {
    try {
        const res = await fetch(`/api/dev/export/table/${currentTable}`); 
        if (!res.ok) throw new Error("Export failed");

        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `${currentTable}_BantayTubig_${getTodayDate()}.sql`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
    } catch (err) {
        console.error("Export error:", err);
        alert("Failed to export SQL dump.");
    }
}
async function exportTableCSV() {
    if (!currentTable) {
        alert("Please select a table first.");
        return;
    }
    try {
        const res = await fetch(`/api/dev/export/table/${currentTable}/csv`);
        if (!res.ok) throw new Error("Export failed");

        const text = await res.text();

        // Split into lines
        const lines = text.split("\n").filter(line => line.trim() !== "");
        const data = lines.map(line => line.split(","));

        // Find "Actions" column index
        const header = data[0];
        const actionsIndex = header.findIndex(h => h.trim().toLowerCase() === "actions");

        let filteredData = data;
        if (actionsIndex !== -1) {
            filteredData = data.map(row => row.filter((_, i) => i !== actionsIndex));
        }

        // Convert back to CSV string
        const csvContent = filteredData.map(row => row.join(",")).join("\n");

        // Create blob and download
        const blob = new Blob([csvContent], { type: "text/csv" });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `${currentTable}_BantayTubig_${getTodayDate()}.csv`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
    } catch (err) {
        console.error("Export CSV error:", err);
        alert("Failed to export table as CSV.");
    }
}

// === EXPORT TO PDF  ===
function exportTablePDF() {
    const { jsPDF } = window.jspdf;
    const tableName = document.getElementById("tableSelect").value;
    if (!tableName) {
        alert("Please select a table first.");
        return;
    }

    const table = document.getElementById("devTable");

    // Grab headers, skip "Actions"
    const headers = Array.from(table.querySelectorAll("thead th"))
        .map((th, i) => ({ text: th.textContent.trim(), index: i }))
        .filter(h => h.text.toLowerCase() !== "actions");

    // Grab rows, skipping the "Actions" cell
    const rows = Array.from(table.querySelectorAll("tbody tr"))
        .map(tr => Array.from(tr.querySelectorAll("td"))
            .map((td, i) => td.textContent.trim())
            .filter((_, i) => headers.some(h => h.index === i)) // keep only allowed cols
        );

    const doc = new jsPDF("l", "mm", "a4"); // landscape A4
    doc.setFontSize(14);
    doc.text(`BantayTubig - Table Export`, 14, 16);

    doc.setFontSize(10);
    doc.text(`Table: ${tableName}`, 14, 22);
    doc.text(`Export Date: ${new Date().toLocaleString()}`, 14, 28);

    // AutoTable with filtered headers + rows
    doc.autoTable({
        head: [headers.map(h => h.text)],
        body: rows,
        startY: 35,
        styles: { fontSize: 8 },
        headStyles: { fillColor: [41, 128, 185] }
    });

    const dateStr = new Date().toISOString().split("T")[0];
    doc.save(`${tableName}_BantayTubig_${dateStr}.pdf`);
}


// --- Pagination ---
function prevPage() {
    if(currentPage > 1) { currentPage--; fetchTable(); }
}
function nextPage() {
    currentPage++; fetchTable();
}


// Fetch logs every 1 second
setInterval(fetchLogs, 1000);
fetchLogs();
