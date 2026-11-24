/**
 * script.js - Smart Parking Management Agent
 * ==========================================
 * Interactive dashboard controller, AI agent coordinator, and Chart.js integration.
 */

// Global Application State
const state = {
  spaces: [],
  statistics: {},
  driverLocation: { x: 0.0, y: 10.0 },
  preferredType: "Regular",
  maxDistance: 50.0,
  recommendedSlotId: null,
  isAutoSimRunning: false,
  autoSimInterval: null,
  mapClickModeActive: false,
  inspectedSlotId: null,
  charts: {
    occupancyDoughnut: null,
    typeBar: null
  }
};

// Preset Coordinates Map
const PRESETS = {
  "Gate A": { x: 0.0, y: 10.0 },
  "Gate B": { x: 15.0, y: 0.0 },
  "Gate C": { x: 30.0, y: 10.0 },
  "Center Plaza": { x: 15.0, y: 12.0 }
};

// ============================================================================
// INITIALIZATION
// ============================================================================
document.addEventListener("DOMContentLoaded", () => {
  initEventListeners();
  initCharts();
  fetchParkingSpaces();
  fetchAgentHistory();
});

/**
 * Attach UI event listeners
 */
function initEventListeners() {
  // Preset Location Buttons
  document.querySelectorAll(".btn-preset").forEach(btn => {
    btn.addEventListener("click", (e) => {
      document.querySelectorAll(".btn-preset").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      const x = parseFloat(btn.dataset.x);
      const y = parseFloat(btn.dataset.y);
      setDriverLocation(x, y);
    });
  });

  // Manual Coordinates Input
  const xInput = document.getElementById("driverXInput");
  const yInput = document.getElementById("driverYInput");
  [xInput, yInput].forEach(inp => {
    inp.addEventListener("change", () => {
      const x = parseFloat(xInput.value) || 0.0;
      const y = parseFloat(yInput.value) || 0.0;
      setDriverLocation(x, y, false);
    });
  });

  // Click on Map to Place Driver Toggle
  const btnMapClick = document.getElementById("btnMapClickMode");
  const lotContainer = document.getElementById("parkingLotContainer");
  btnMapClick.addEventListener("click", () => {
    state.mapClickModeActive = !state.mapClickModeActive;
    if (state.mapClickModeActive) {
      btnMapClick.classList.add("active");
      btnMapClick.innerHTML = '<i class="fa-solid fa-check"></i> Click Lot Now';
      lotContainer.style.cursor = "crosshair";
      showTicker("Click Mode: Tap anywhere inside the parking lot to place driver coordinates.");
    } else {
      btnMapClick.classList.remove("active");
      btnMapClick.innerHTML = '<i class="fa-solid fa-crosshairs"></i> Click on Map';
      lotContainer.style.cursor = "default";
    }
  });

  lotContainer.addEventListener("click", (e) => {
    if (!state.mapClickModeActive) return;
    const rect = lotContainer.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const clickY = e.clientY - rect.top;
    
    // Scale click position to lot coordinates (X: 0 to 38m, Y: 0 to 22m)
    const normX = Math.max(0, Math.min(38, (clickX / rect.width) * 38));
    const normY = Math.max(0, Math.min(22, (clickY / rect.height) * 22));
    
    setDriverLocation(Math.round(normX * 10) / 10, Math.round(normY * 10) / 10);
    state.mapClickModeActive = false;
    btnMapClick.classList.remove("active");
    btnMapClick.innerHTML = '<i class="fa-solid fa-crosshairs"></i> Click on Map';
    lotContainer.style.cursor = "default";
  });

  // Gate Marker Clicks
  document.getElementById("gateMarkerA").addEventListener("click", () => setDriverLocation(0.0, 10.0));
  document.getElementById("gateMarkerB").addEventListener("click", () => setDriverLocation(15.0, 0.0));
  document.getElementById("gateMarkerC").addEventListener("click", () => setDriverLocation(30.0, 10.0));

  // Vehicle Preference Select
  const typeSelect = document.getElementById("vehicleTypeSelect");
  typeSelect.addEventListener("change", () => {
    state.preferredType = typeSelect.value;
    updatePerceptSummary();
  });

  // Max Distance Slider
  const distSlider = document.getElementById("maxDistSlider");
  const distValue = document.getElementById("maxDistValue");
  distSlider.addEventListener("input", () => {
    state.maxDistance = parseFloat(distSlider.value);
    distValue.textContent = `${state.maxDistance} meters`;
    updatePerceptSummary();
  });

  // Run AI Agent Button
  document.getElementById("btnFindParking").addEventListener("click", runIntelligentAgent);

  // Search & Filter
  document.getElementById("slotSearchInput").addEventListener("input", filterAndRenderSlots);
  document.getElementById("typeFilterSelect").addEventListener("change", filterAndRenderSlots);
  document.getElementById("statusFilterSelect").addEventListener("change", filterAndRenderSlots);

  // Reasoning Accordion Toggle
  const rToggleBtn = document.getElementById("reasoningToggleBtn");
  const rList = document.getElementById("reasoningList");
  const rChevron = document.getElementById("reasoningChevron");
  rToggleBtn.addEventListener("click", () => {
    rList.classList.toggle("hidden");
    rChevron.classList.toggle("fa-chevron-down");
    rChevron.classList.toggle("fa-chevron-up");
  });

  // Action: Park In Recommended Slot
  document.getElementById("btnParkInSlot").addEventListener("click", parkInRecommendedSlot);

  // Simulation Controls
  document.getElementById("btnAutoSim").addEventListener("click", toggleAutoSimulation);
  document.getElementById("btnSimStep").addEventListener("click", simulateTrafficStep);
  document.getElementById("btnRandomize").addEventListener("click", randomizeLot);
  document.getElementById("btnResetLot").addEventListener("click", resetLot);

  // Modal Closers
  document.getElementById("btnCloseSlotModal").addEventListener("click", closeSlotModal);
  document.getElementById("slotModalBackdrop").addEventListener("click", (e) => {
    if (e.target.id === "slotModalBackdrop") closeSlotModal();
  });

  document.getElementById("btnOpenDocs").addEventListener("click", openDocsModal);
  document.getElementById("btnCloseDocsModal").addEventListener("click", closeDocsModal);
  document.getElementById("docsModalBackdrop").addEventListener("click", (e) => {
    if (e.target.id === "docsModalBackdrop") closeDocsModal();
  });

  // Docs Modal Tabs
  document.querySelectorAll(".doc-tab").forEach(tab => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".doc-tab").forEach(t => t.classList.remove("active"));
      document.querySelectorAll(".doc-tab-content").forEach(c => c.classList.remove("active"));
      tab.classList.add("active");
      const target = document.getElementById(tab.dataset.tab);
      if (target) target.classList.add("active");
    });
  });

  // Slot Inspector Action Buttons
  document.getElementById("btnToggleSlotStatus").addEventListener("click", () => toggleSlotStatus(state.inspectedSlotId));
  document.getElementById("btnSetSlotAvailable").addEventListener("click", () => setSlotStatusExplicit(state.inspectedSlotId, "Available"));
  document.getElementById("btnSetSlotOccupied").addEventListener("click", () => setSlotStatusExplicit(state.inspectedSlotId, "Occupied"));
  document.getElementById("btnSetSlotReserved").addEventListener("click", () => setSlotStatusExplicit(state.inspectedSlotId, "Reserved"));

  // Clear history view button
  document.getElementById("btnClearHistoryBtn").addEventListener("click", () => {
    const tbody = document.getElementById("historyTableBody");
    tbody.innerHTML = '<tr class="empty-history-row"><td colspan="7" class="text-center text-muted">History view cleared.</td></tr>';
  });
}

// ============================================================================
// DRIVER LOCATION & PERCEPT UPDATES
// ============================================================================
function setDriverLocation(x, y, updatePresetButtons = true) {
  state.driverLocation.x = x;
  state.driverLocation.y = y;

  document.getElementById("driverXInput").value = x.toFixed(1);
  document.getElementById("driverYInput").value = y.toFixed(1);

  if (updatePresetButtons) {
    document.querySelectorAll(".btn-preset").forEach(btn => {
      const bx = parseFloat(btn.dataset.x);
      const by = parseFloat(btn.dataset.y);
      if (Math.abs(bx - x) < 0.1 && Math.abs(by - y) < 0.1) {
        btn.classList.add("active");
      } else {
        btn.classList.remove("active");
      }
    });
  }

  updateDriverPinPosition();
  updatePerceptSummary();
  // Live recalculate distances on visible slots
  recomputeSlotDistancesLocally();
}

function updateDriverPinPosition() {
  const pin = document.getElementById("driverPinMarker");
  const label = document.getElementById("driverPinLabel");
  label.textContent = `Driver (${state.driverLocation.x.toFixed(1)}m, ${state.driverLocation.y.toFixed(1)}m)`;

  // Scale map coordinates: width 38m, height 22m
  const pctX = Math.max(3, Math.min(92, (state.driverLocation.x / 38) * 100));
  const pctY = Math.max(5, Math.min(88, (state.driverLocation.y / 22) * 100));

  pin.style.left = `${pctX}%`;
  pin.style.top = `${pctY}%`;
}

function updatePerceptSummary() {
  const el = document.getElementById("perceptSummary");
  if (el) {
    el.innerHTML = `Driver at (${state.driverLocation.x.toFixed(1)}m, ${state.driverLocation.y.toFixed(1)}m) | Type: <strong>${state.preferredType}</strong> | Max Dist: <strong>${state.maxDistance}m</strong> | Sensed: 36 bays.`;
  }
}

function recomputeSlotDistancesLocally() {
  const dx = state.driverLocation.x;
  const dy = state.driverLocation.y;
  state.spaces.forEach(s => {
    s.distance = Math.round(Math.hypot(s.x - dx, s.y - dy) * 100) / 100;
  });
  filterAndRenderSlots();
}

// ============================================================================
// DATA FETCHING & API INTEGRATION
// ============================================================================
async function fetchParkingSpaces() {
  try {
    const res = await fetch(`/api/parking-spaces?driver_x=${state.driverLocation.x}&driver_y=${state.driverLocation.y}`);
    const data = await res.json();
    if (data.success) {
      state.spaces = data.spaces;
      state.statistics = data.statistics;
      updateMetrics(data.statistics);
      filterAndRenderSlots();
      updateCharts(data.statistics, data.spaces);
    }
  } catch (err) {
    console.error("Error fetching parking spaces:", err);
    showTicker("Network error communicating with parking telemetry service.");
  }
}

async function fetchAgentHistory() {
  try {
    const res = await fetch("/api/agent/history");
    const data = await res.json();
    if (data.success) {
      renderHistoryTable(data.history);
      if (data.metrics) {
        document.getElementById("valAgentSuccessRate").textContent = `${data.metrics.success_rate_percent}%`;
        document.getElementById("valAgentTotalAllocations").textContent = `${data.metrics.successful_recommendations} Allocations`;
      }
    }
  } catch (err) {
    console.error("Error fetching agent history:", err);
  }
}

// ============================================================================
// PARKING LOT RENDERING & FILTERING
// ============================================================================
function filterAndRenderSlots() {
  const search = document.getElementById("slotSearchInput").value.trim().toUpperCase();
  const typeFilter = document.getElementById("typeFilterSelect").value;
  const statusFilter = document.getElementById("statusFilterSelect").value;

  const rowA = document.getElementById("slotsRowZoneA");
  const rowB1 = document.getElementById("slotsRowZoneB1");
  const rowB2 = document.getElementById("slotsRowZoneB2");
  const rowC = document.getElementById("slotsRowZoneC");

  rowA.innerHTML = "";
  rowB1.innerHTML = "";
  rowB2.innerHTML = "";
  rowC.innerHTML = "";

  state.spaces.forEach(slot => {
    // Check search & filters
    const matchesSearch = !search || slot.id.toUpperCase().includes(search);
    const matchesType = typeFilter === "All" || slot.parking_type === typeFilter;
    const matchesStatus = statusFilter === "All" || slot.status === statusFilter;
    const isVisible = matchesSearch && matchesType && matchesStatus;

    const card = createSlotCardElement(slot, isVisible);

    // Distribute into zones
    if (slot.slot_number >= 1 && slot.slot_number <= 12) {
      rowA.appendChild(card);
    } else if (slot.slot_number >= 13 && slot.slot_number <= 18) {
      rowB1.appendChild(card);
    } else if (slot.slot_number >= 19 && slot.slot_number <= 24) {
      rowB2.appendChild(card);
    } else if (slot.slot_number >= 25 && slot.slot_number <= 36) {
      rowC.appendChild(card);
    }
  });
}

function createSlotCardElement(slot, isVisible) {
  const card = document.createElement("div");
  card.className = `parking-slot-card status-${slot.status.toLowerCase()}`;
  if (!isVisible) card.classList.add("slot-filtered-out");
  if (state.recommendedSlotId === slot.id) {
    card.classList.add("status-recommended");
  }

  // Type Icon
  let typeIcon = '<i class="fa-solid fa-car slot-type-icon icon-regular" title="Regular Vehicle"></i>';
  if (slot.parking_type === "EV") {
    typeIcon = '<i class="fa-solid fa-bolt slot-type-icon icon-ev" title="EV Fast Charger"></i>';
  } else if (slot.parking_type === "Disabled") {
    typeIcon = '<i class="fa-solid fa-wheelchair slot-type-icon icon-disabled" title="Accessible / Disabled"></i>';
  }

  // Center graphic based on status & recommendation
  let centerGraphic = '';
  if (state.recommendedSlotId === slot.id) {
    centerGraphic = `<div class="slot-ev-graphic text-cyan" title="AI Selected"><i class="fa-solid fa-star fa-bounce"></i></div>`;
  } else if (slot.status === "Occupied") {
    centerGraphic = `<div class="slot-car-graphic" title="Bay Occupied"><i class="fa-solid fa-car-side"></i></div>`;
  } else if (slot.status === "Reserved") {
    centerGraphic = `<div class="slot-reserved-lock" title="Bay Reserved"><i class="fa-solid fa-lock"></i></div>`;
  } else {
    centerGraphic = `<div class="slot-avail-circle" title="Available to Park"><i class="fa-solid fa-check"></i></div>`;
  }

  // Status pill class & label
  let pillClass = "pill-avail";
  let pillText = "AVAILABLE";
  if (state.recommendedSlotId === slot.id) {
    pillClass = "pill-rec";
    pillText = "BEST PICK";
  } else if (slot.status === "Occupied") {
    pillClass = "pill-occ";
    pillText = "OCCUPIED";
  } else if (slot.status === "Reserved") {
    pillClass = "pill-res";
    pillText = "RESERVED";
  }

  card.innerHTML = `
    <div class="slot-top-row">
      <span class="slot-id-badge">${slot.id}</span>
      ${typeIcon}
    </div>
    <div class="slot-visual-center">
      ${centerGraphic}
    </div>
    <div class="slot-bottom-row">
      <span class="slot-status-pill ${pillClass}">${pillText}</span>
      <span class="slot-distance-badge">${slot.distance !== undefined ? slot.distance + 'm' : ''}</span>
    </div>
  `;

  card.addEventListener("click", () => openSlotModal(slot.id));
  return card;
}

// ============================================================================
// METRICS & CHARTS
// ============================================================================
function updateMetrics(stats) {
  if (!stats) return;
  document.getElementById("valTotalSpaces").textContent = stats.total_spaces || 36;
  document.getElementById("valAvailableSpaces").textContent = stats.available_spaces;
  document.getElementById("valOccupiedSpaces").textContent = stats.occupied_spaces;
  document.getElementById("valReservedSpaces").textContent = stats.reserved_spaces;
  document.getElementById("valOccupancyRate").textContent = `${stats.occupancy_percentage}%`;

  const bar = document.getElementById("occupancyProgress");
  if (bar) bar.style.width = `${stats.occupancy_percentage}%`;
}

function initCharts() {
  const doughnutCtx = document.getElementById("occupancyDoughnutChart")?.getContext("2d");
  const barCtx = document.getElementById("typeBarChart")?.getContext("2d");

  if (doughnutCtx) {
    state.charts.occupancyDoughnut = new Chart(doughnutCtx, {
      type: "doughnut",
      data: {
        labels: ["Available", "Occupied", "Reserved"],
        datasets: [{
          data: [18, 14, 4],
          backgroundColor: ["#10B981", "#EF4444", "#F59E0B"],
          borderColor: "#090F1C",
          borderWidth: 2,
          hoverOffset: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "bottom",
            labels: { color: "#94A3B8", font: { size: 11 }, padding: 12 }
          }
        },
        cutout: "68%"
      }
    });
  }

  if (barCtx) {
    state.charts.typeBar = new Chart(barCtx, {
      type: "bar",
      data: {
        labels: ["Regular", "EV Charging", "Accessible"],
        datasets: [
          {
            label: "Available",
            data: [12, 4, 3],
            backgroundColor: "#10B981",
            borderRadius: 4
          },
          {
            label: "Occupied",
            data: [10, 1, 2],
            backgroundColor: "#EF4444",
            borderRadius: 4
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: {
            grid: { display: false },
            ticks: { color: "#94A3B8", font: { size: 10 } }
          },
          y: {
            grid: { color: "rgba(255, 255, 255, 0.05)" },
            ticks: { color: "#94A3B8", font: { size: 10 }, stepSize: 2 }
          }
        },
        plugins: {
          legend: {
            position: "bottom",
            labels: { color: "#94A3B8", font: { size: 11 } }
          }
        }
      }
    });
  }
}

function updateCharts(stats, spaces) {
  if (state.charts.occupancyDoughnut && stats) {
    state.charts.occupancyDoughnut.data.datasets[0].data = [
      stats.available_spaces,
      stats.occupied_spaces,
      stats.reserved_spaces
    ];
    state.charts.occupancyDoughnut.update();
  }

  if (state.charts.typeBar && stats && stats.type_stats) {
    const tStats = stats.type_stats;
    state.charts.typeBar.data.datasets[0].data = [
      tStats.Regular?.available || 0,
      tStats.EV?.available || 0,
      tStats.Disabled?.available || 0
    ];
    state.charts.typeBar.data.datasets[1].data = [
      tStats.Regular?.occupied || 0,
      tStats.EV?.occupied || 0,
      tStats.Disabled?.occupied || 0
    ];
    state.charts.typeBar.update();
  }
}

// ============================================================================
// AI AGENT DECISION-MAKING PIPELINE (MAIN AI CORE)
// ============================================================================
async function runIntelligentAgent() {
  const btn = document.getElementById("btnFindParking");
  btn.disabled = true;
  btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Perceiving Environment...';

  // Animate Workflow Pipeline Stepper
  await animateWorkflowStepper();

  try {
    const res = await fetch("/api/recommend", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        driver_x: state.driverLocation.x,
        driver_y: state.driverLocation.y,
        parking_type: state.preferredType,
        max_distance: state.maxDistance
      })
    });

    const result = await res.json();
    displayAgentRecommendation(result);

    // Refresh history log & metrics
    fetchAgentHistory();

  } catch (err) {
    console.error("AI recommendation error:", err);
    showTicker("Error executing AI decision algorithm.");
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> Find Best Parking Space';
  }
}

async function animateWorkflowStepper() {
  for (let i = 1; i <= 8; i++) {
    const step = document.getElementById(`wfStep${i}`);
    if (step) {
      step.classList.add("active");
      await new Promise(r => setTimeout(r, 80));
    }
  }
  // Remove active after animation
  setTimeout(() => {
    for (let i = 1; i <= 8; i++) {
      const step = document.getElementById(`wfStep${i}`);
      if (step) step.classList.remove("active");
    }
  }, 1800);
}

function displayAgentRecommendation(result) {
  const emptyState = document.getElementById("recEmptyState");
  const content = document.getElementById("recContent");
  const badgeStatus = document.getElementById("recBadgeStatus");

  emptyState.classList.add("hidden");
  content.classList.remove("hidden");

  if (result.success && result.recommended_slot) {
    const slot = result.recommended_slot;
    state.recommendedSlotId = slot.id;

    badgeStatus.className = "badge badge-success";
    badgeStatus.textContent = "Optimal Found";

    document.getElementById("recSlotId").textContent = slot.id;
    document.getElementById("recSlotZone").textContent = slot.zone;
    document.getElementById("recSlotDist").textContent = `${slot.distance} m`;
    document.getElementById("recSlotTime").textContent = `~${result.estimated_walking_time_min} min`;
    document.getElementById("recSlotType").textContent = slot.parking_type;
    document.getElementById("recSlotRate").textContent = slot.hourly_rate > 0 ? `$${slot.hourly_rate.toFixed(2)} / hr` : "Free";

    document.getElementById("recRationalText").textContent = result.rational_explanation;

    // Render reasoning steps
    const rList = document.getElementById("reasoningList");
    rList.innerHTML = "";
    result.reasoning_steps.forEach(step => {
      const item = document.createElement("div");
      item.className = "reasoning-item";
      item.innerHTML = `<i class="fa-solid fa-circle-arrow-right"></i> <span>${step}</span>`;
      rList.appendChild(item);
    });

    // Render Alternative Slots
    const altGrid = document.getElementById("alternativesGrid");
    altGrid.innerHTML = "";
    if (result.alternative_slots && result.alternative_slots.length > 0) {
      document.getElementById("alternativesBox").classList.remove("hidden");
      result.alternative_slots.forEach(alt => {
        const altCard = document.createElement("div");
        altCard.className = "alt-card";
        altCard.innerHTML = `
          <div>
            <span class="alt-id">${alt.id}</span>
            <span style="font-size:0.65rem; color:#94A3B8; margin-left:0.3rem;">${alt.zone}</span>
          </div>
          <span class="alt-dist">${alt.distance}m</span>
        `;
        altCard.addEventListener("click", () => openSlotModal(alt.id));
        altGrid.appendChild(altCard);
      });
    } else {
      document.getElementById("alternativesBox").classList.add("hidden");
    }

    showTicker(`AI Decision: Slot ${slot.id} allocated (${slot.distance}m, ${slot.parking_type}). Euclidean minimum.`);

  } else {
    // Failure / No suitable slot
    state.recommendedSlotId = null;
    badgeStatus.className = "badge text-red";
    badgeStatus.textContent = "No Feasible Bay";

    document.getElementById("recSlotId").textContent = "None";
    document.getElementById("recSlotZone").textContent = "N/A";
    document.getElementById("recSlotDist").textContent = "--";
    document.getElementById("recSlotTime").textContent = "--";
    document.getElementById("recSlotType").textContent = state.preferredType;
    document.getElementById("recSlotRate").textContent = "--";

    document.getElementById("recRationalText").textContent = result.rational_explanation;
    document.getElementById("alternativesBox").classList.add("hidden");

    showTicker(`AI Alert: No feasible '${state.preferredType}' bay within ${state.maxDistance}m. Adjust constraints.`);
  }

  // Refresh lot rendering to apply pulsing glow to winner
  filterAndRenderSlots();
}

async function parkInRecommendedSlot() {
  if (!state.recommendedSlotId) {
    alert("No slot is currently recommended. Run the agent first!");
    return;
  }

  try {
    const res = await fetch(`/api/slot/${state.recommendedSlotId}/park`, { method: "POST" });
    const data = await res.json();
    if (data.success) {
      showTicker(`Driver parked in ${state.recommendedSlotId}. Slot status marked Occupied.`);
      state.recommendedSlotId = null;
      fetchParkingSpaces();
      fetchAgentHistory();
      // Reset recommendation card
      document.getElementById("recEmptyState").classList.remove("hidden");
      document.getElementById("recContent").classList.add("hidden");
    }
  } catch (err) {
    console.error("Error parking in slot:", err);
  }
}

// ============================================================================
// SIMULATION & DATASET MANAGEMENT
// ============================================================================
async function simulateTrafficStep() {
  try {
    const res = await fetch("/api/dataset/simulate-step", { method: "POST" });
    const data = await res.json();
    if (data.success) {
      state.spaces = data.spaces;
      state.statistics = data.statistics;
      updateMetrics(data.statistics);
      filterAndRenderSlots();
      updateCharts(data.statistics, data.spaces);

      if (data.events && data.events.length > 0) {
        showTicker(`Traffic Step: ${data.events.join(" | ")}`);
      }

      // If recommended slot became occupied, warn user
      if (state.recommendedSlotId) {
        const slot = state.spaces.find(s => s.id === state.recommendedSlotId);
        if (slot && slot.status !== "Available") {
          showTicker(`Warning: Recommended slot ${slot.id} is now ${slot.status}! Recalculate.`);
        }
      }
    }
  } catch (err) {
    console.error("Simulation step error:", err);
  }
}

function toggleAutoSimulation() {
  const pill = document.getElementById("simStatusPill");
  const text = document.getElementById("simStatusText");
  const icon = document.getElementById("simPlayIcon");
  const label = document.getElementById("simBtnLabel");

  state.isAutoSimRunning = !state.isAutoSimRunning;

  if (state.isAutoSimRunning) {
    pill.classList.remove("paused");
    text.textContent = "Simulation: Live";
    icon.className = "fa-solid fa-pause";
    label.textContent = "Pause Traffic";
    showTicker("Live Traffic Simulation activated: Stochastic vehicle arrivals & departures active every 4s.");

    state.autoSimInterval = setInterval(() => {
      simulateTrafficStep();
    }, 4000);
  } else {
    pill.classList.add("paused");
    text.textContent = "Simulation: Paused";
    icon.className = "fa-solid fa-play";
    label.textContent = "Live Traffic";
    showTicker("Live Traffic Simulation paused.");

    clearInterval(state.autoSimInterval);
    state.autoSimInterval = null;
  }
}

async function randomizeLot() {
  try {
    const res = await fetch("/api/dataset/randomize", { method: "POST" });
    const data = await res.json();
    if (data.success) {
      state.spaces = data.spaces;
      state.statistics = data.statistics;
      state.recommendedSlotId = null;
      updateMetrics(data.statistics);
      filterAndRenderSlots();
      updateCharts(data.statistics, data.spaces);
      showTicker("Parking bay occupancy randomized with realistic probability distribution.");
    }
  } catch (err) {
    console.error("Error randomizing lot:", err);
  }
}

async function resetLot() {
  try {
    const res = await fetch("/api/dataset/reset", { method: "POST" });
    const data = await res.json();
    if (data.success) {
      state.spaces = data.spaces;
      state.statistics = data.statistics;
      state.recommendedSlotId = null;
      updateMetrics(data.statistics);
      filterAndRenderSlots();
      updateCharts(data.statistics, data.spaces);
      showTicker("Facility reset to default pristine baseline (18 Available, 14 Occupied, 4 Reserved).");
    }
  } catch (err) {
    console.error("Error resetting lot:", err);
  }
}

// ============================================================================
// SLOT INSPECTOR MODAL & OVERRIDE
// ============================================================================
function openSlotModal(slotId) {
  const slot = state.spaces.find(s => s.id === slotId);
  if (!slot) return;

  state.inspectedSlotId = slotId;

  document.getElementById("modalSlotId").textContent = slot.id;
  
  const statusBadge = document.getElementById("modalSlotStatusBadge");
  statusBadge.textContent = slot.status;
  statusBadge.className = `badge status-${slot.status.toLowerCase()}`;
  if (slot.status === "Available") statusBadge.classList.add("badge-success");

  document.getElementById("modalSlotZone").textContent = slot.zone;
  document.getElementById("modalSlotType").textContent = slot.parking_type;
  document.getElementById("modalSlotCoords").textContent = `(${slot.x.toFixed(1)}m, ${slot.y.toFixed(1)}m)`;
  document.getElementById("modalSlotDist").textContent = `${slot.distance !== undefined ? slot.distance : '--'} m`;
  document.getElementById("modalSlotRate").textContent = slot.hourly_rate > 0 ? `$${slot.hourly_rate.toFixed(2)} / hr` : "Free";
  document.getElementById("modalSlotFeatures").textContent = slot.features || "Standard Bay";

  document.getElementById("slotModalBackdrop").classList.remove("hidden");
}

function closeSlotModal() {
  document.getElementById("slotModalBackdrop").classList.add("hidden");
  state.inspectedSlotId = null;
}

async function toggleSlotStatus(slotId) {
  if (!slotId) return;
  try {
    const res = await fetch(`/api/slot/${slotId}/toggle`, { method: "POST" });
    const data = await res.json();
    if (data.success) {
      showTicker(`Manual Override: Slot ${slotId} toggled to '${data.new_status}'.`);
      closeSlotModal();
      fetchParkingSpaces();
    }
  } catch (err) {
    console.error("Error toggling status:", err);
  }
}

async function setSlotStatusExplicit(slotId, status) {
  if (!slotId) return;
  try {
    const res = await fetch(`/api/slot/${slotId}/set-status`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status })
    });
    const data = await res.json();
    if (data.success) {
      showTicker(`Slot ${slotId} manually set to '${status}'.`);
      closeSlotModal();
      fetchParkingSpaces();
    }
  } catch (err) {
    console.error("Error setting status:", err);
  }
}

// ============================================================================
// ACADEMIC DOCS MODAL
// ============================================================================
function openDocsModal() {
  document.getElementById("docsModalBackdrop").classList.remove("hidden");
}

function closeDocsModal() {
  document.getElementById("docsModalBackdrop").classList.add("hidden");
}

// ============================================================================
// HISTORY TABLE RENDERING
// ============================================================================
function renderHistoryTable(history) {
  const tbody = document.getElementById("historyTableBody");
  if (!history || history.length === 0) {
    tbody.innerHTML = '<tr class="empty-history-row"><td colspan="7" class="text-center text-muted">No decisions recorded yet. Run the agent above!</td></tr>';
    return;
  }

  tbody.innerHTML = "";
  history.slice(0, 15).forEach((item, idx) => {
    const tr = document.createElement("tr");
    const statusClass = item.status === "Success" ? "text-green" : "text-red";
    tr.innerHTML = `
      <td>${item.id || idx + 1}</td>
      <td style="font-size:0.68rem; color:#64748B;">${item.timestamp ? item.timestamp.split(" ")[1] : '--'}</td>
      <td>${item.driver_location}</td>
      <td>${item.preference}</td>
      <td><strong class="text-cyan">${item.recommended_slot}</strong></td>
      <td>${item.distance}</td>
      <td class="${statusClass}"><i class="fa-solid fa-circle" style="font-size:0.5rem;"></i> ${item.status}</td>
    `;
    tbody.appendChild(tr);
  });
}

// ============================================================================
// TICKER HELPER
// ============================================================================
function showTicker(msg) {
  const tickerMsg = document.getElementById("tickerMessage");
  const tickerTime = document.getElementById("tickerTime");
  if (tickerMsg) tickerMsg.textContent = msg;
  if (tickerTime) {
    const now = new Date();
    tickerTime.textContent = now.toLocaleTimeString();
  }
}
