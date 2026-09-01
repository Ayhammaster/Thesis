// ==================== Navigation ====================
const navLinks = document.querySelectorAll('.nav-link');
const views = document.querySelectorAll('.view');
let currentPage = 1;

navLinks.forEach(link => {
    link.addEventListener('click', (e) => {
        e.preventDefault();
        const view = link.dataset.view;

        navLinks.forEach(l => l.classList.remove('active'));
        link.classList.add('active');

        views.forEach(v => v.classList.remove('active'));
        document.getElementById('view-' + view).classList.add('active');

        switch(view) {
            case 'alerts': currentPage = 1; loadAlerts(); break;
            case 'devices': loadDevices(); break;
            case 'thresholds': loadThresholds(); break;
            case 'temperature': populateFilters('temperature'); loadSensorData('temperature'); break;
            case 'humidity': populateFilters('humidity'); loadSensorData('humidity'); break;
            case 'dashboard': loadDashboard(); break;
            case 'models': loadModelsComparison(); break;
            case 'latency': loadLatencyComparison(); break;
        }

        if (window.innerWidth <= 992) {
            document.getElementById('sidebar').classList.remove('open');
        }
    });
});

function toggleSidebar() {
    document.getElementById('sidebar').classList.toggle('open');
}

// ==================== Toast Notifications ====================
function showToast(message, type = 'success') {
    const colors = { success: '#10b981', error: '#ef4444', info: '#00d4ff' };
    const toast = document.createElement('div');
    toast.className = 'toast-msg';
    toast.style.borderRightColor = colors[type];
    toast.innerHTML = `<i class="fa-solid fa-circle-info" style="color:${colors[type]}"></i> ${message}`;
    document.getElementById('toastContainer').appendChild(toast);
    setTimeout(() => { toast.remove(); }, 3000);
}

// ==================== Modal Helpers ====================
function openModal(modalId) {
    document.getElementById(modalId).classList.add('active');
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
}

// ==================== Auto Refresh ====================
setInterval(() => {
    const activeView = document.querySelector('.view.active').id;
    switch(activeView) {
        case 'view-alerts': loadAlerts(); break;
        case 'view-dashboard': loadDashboard(); break;
        case 'view-temperature': loadSensorData('temperature'); break;
        case 'view-humidity': loadSensorData('humidity'); break;
    }
}, 10000);

// ==================== Initialize ====================
document.addEventListener('DOMContentLoaded', () => {
     loadDashboard()
        .then(() => populateFilters('temperature'))
        .then(() => populateFilters('humidity'))
        .catch(e => console.error('Init error:', e));
});
