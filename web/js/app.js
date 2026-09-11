const API_BASE = "http://localhost:8000";
const WS_URL = "ws://localhost:8000/ws/status";

let ws = null;
let currentStepIndex = 0;

// Navigation
function nav(viewId) {
    document.querySelectorAll('.view').forEach(el => el.classList.remove('active'));
    document.getElementById(`view-${viewId}`).classList.add('active');
}

// API Calls
async function selectExperiment(protocolId) {
    try {
        await fetch(`${API_BASE}/experiment/select`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({protocol_id: protocolId})
        });
        nav('monitor');
    } catch (e) {
        showError("Backend unavailable");
    }
}

async function startPipeline() {
    try {
        resetUI();
        await fetch(`${API_BASE}/experiment/start`, { method: 'POST' });
        document.getElementById('video-stream').src = `${API_BASE}/video_feed?t=${new Date().getTime()}`;
        document.getElementById('home-status-text').innerText = "Mission Active";
        connectWebSocket();
    } catch (e) {
        showError("Failed to start pipeline. Is backend running?");
    }
}

async function stopPipeline() {
    try {
        await fetch(`${API_BASE}/experiment/stop`, { method: 'POST' });
        document.getElementById('video-stream').src = "";
        document.getElementById('home-status-text').innerText = "System Idle";
        if(ws) ws.close();
    } catch (e) {
        showError("Failed to stop pipeline");
    }
}

async function resetPipeline() {
    try {
        await fetch(`${API_BASE}/experiment/reset`, { method: 'POST' });
        resetUI();
    } catch (e) {
        showError("Failed to reset pipeline");
    }
}

// WebSocket connection
function connectWebSocket() {
    if (ws && ws.readyState === WebSocket.OPEN) return;
    
    ws = new WebSocket(WS_URL);
    
    ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        if (msg.type === "telemetry") {
            updateTelemetry(msg.data);
        } else if (msg.type === "log_update") {
            appendLog(msg.data);
        } else if (msg.type === "error") {
            showError(msg.message);
        }
    };
    
    ws.onerror = () => showError("WebSocket connection failed.");
    ws.onclose = () => console.log("WebSocket closed");
}

function updateTelemetry(data) {
    document.getElementById('error-banner').classList.add('hidden');
    
    // Update active states
    const statesEl = document.getElementById('active-states');
    statesEl.innerHTML = data.active_states.length ? 
        data.active_states.map(s => `<span class="badge active">${s}</span>`).join(' ') : 'None';

    // Update timeline (backend is 0-indexed, UI is 1-indexed)
    const idx = data.step_index + 1;
    if (idx !== currentStepIndex) {
        currentStepIndex = idx;
        updateTimelineUI(idx);
    }
    
    // Check completion
    if (data.is_completed) {
        document.getElementById('mission-complete-msg').classList.remove('hidden');
        setTimeout(() => nav('report'), 2000);
        stopPipeline();
    }
}

function updateTimelineUI(activeIndex) {
    for (let i = 1; i <= 5; i++) {
        const li = document.getElementById(`step-${i}`);
        const badge = li.querySelector('.badge');
        
        li.className = '';
        badge.className = 'badge';
        
        if (i < activeIndex) {
            li.classList.add('completed');
            badge.classList.add('completed');
            badge.innerText = 'COMPLETED';
        } else if (i === activeIndex) {
            li.classList.add('active');
            badge.classList.add('active');
            badge.innerText = 'ACTIVE';
        } else {
            badge.innerText = 'LOCKED';
        }
    }
}

function resetUI() {
    currentStepIndex = 1;
    updateTimelineUI(1);
    document.getElementById('mission-complete-msg').classList.add('hidden');
    document.getElementById('log-body').innerHTML = '';
}

function appendLog(log) {
    const tbody = document.getElementById('log-body');
    const tr = document.createElement('tr');
    tr.innerHTML = `
        <td>${log.timestamp}</td>
        <td><strong>${log.event}</strong></td>
        <td>${log.message}</td>
    `;
    tbody.prepend(tr);
}

function showError(msg) {
    const banner = document.getElementById('error-banner');
    banner.innerText = msg;
    banner.classList.remove('hidden');
}

// Init
resetUI();
