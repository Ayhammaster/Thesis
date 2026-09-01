// ==================== API Helper ====================
async function api(endpoint, options = {}) {
    const defaultOptions = {
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin'
    };

    try {
        const response = await fetch(endpoint, { ...defaultOptions, ...options });
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error(`API Error: ${error.message}`);
        throw error;
    }
}

// ==================== Dashboard ====================
async function loadDashboard() {
    try {
        const [devices, alertsData, charts] = await Promise.all([
            api('/api/devices'),
            api('/api/alerts'),
            api('/api/charts')
        ]);

        document.getElementById('totalDevices').textContent = devices.length;
        document.getElementById('onlineDevices').textContent =
            devices.filter(d => d.status === 'online').length;
        document.getElementById('totalAlerts').textContent = alertsData.stats.total;
        document.getElementById('sentEmails').textContent = alertsData.stats.sent;

        updateChart('dashTempChart', charts.temperature, '#ff8c42', 'rgba(255,140,66,0.3)');
        updateChart('dashHumChart', charts.humidity, '#00d4ff', 'rgba(0,212,255,0.3)');
    } catch (e) { console.error(e); }
}

// ==================== Filters ====================
// ==================== Filters ====================
async function populateFilters(sensorType) {
    // ✅ تحويل الاسم الكامل إلى المختصر المستخدم في HTML (temp / hum)
    const prefix = sensorType === 'temperature' ? 'temp' : 'hum';
    const daySelect = document.getElementById(prefix + 'DayFilter');
    const deviceSelect = document.getElementById(prefix + 'DeviceFilter');

    if (!daySelect && !deviceSelect) {
        console.error("!!! لم يتم العثور على عناصر القوائم في HTML");
        return;
    }

    try {
        const devices = await api('/api/devices');
        const days = await api(`/api/available-days/${sensorType}`);

        if (deviceSelect) {
            let html = '<option value="">جميع الأجهزة</option>';
            if (Array.isArray(devices) && devices.length > 0) {
                html += devices.map(d =>
                    `<option value="${d.id}">${d.name} (${d.code || d.device_code})</option>`
                ).join('');
            }
            deviceSelect.innerHTML = html;
        }

        if (daySelect) {
            let html = '<option value="">كل الأيام (الأحدث)</option>';
            if (Array.isArray(days) && days.length > 0) {
                html += days.map(d => `<option value="${d}">${d}</option>`).join('');
            }
            daySelect.innerHTML = html;
        }
    } catch (e) {
        console.error('!!! خطأ أثناء جلب بيانات القوائم:', e);
    }
}

// ==================== Sensor View Init ====================
async function initSensorView(type) {
    await populateFilters(type);
    await loadSensorData(type);
}

// ==================== Sensor Data ====================
async function loadSensorData(type) {
    try {
        // ✅ استخدام نفس المختصر هنا أيضاً
        const prefix = type === 'temperature' ? 'temp' : 'hum';
        const deviceSelect = document.getElementById(prefix + 'DeviceFilter');
        const daySelect = document.getElementById(prefix + 'DayFilter');

        const selectedDay = daySelect ? daySelect.value : '';
        const selectedDevice = deviceSelect ? deviceSelect.value : '';

        const deviceParam = selectedDevice ? `&device_id=${selectedDevice}` : '';
        const deviceQuery = selectedDevice ? `?device_id=${selectedDevice}` : '';

        const [readings, stats, charts] = await Promise.all([
            api(`/api/current-readings${deviceQuery}`),
            api(`/api/sensor-stats/${type}${deviceQuery}`),
            api(`/api/charts?date=${encodeURIComponent(selectedDay)}${deviceParam}`)
        ]);

        const chartData = type === 'temperature' ? charts.temperature : charts.humidity;

        if (type === 'temperature') {
            updateBigNumber('tempValue', 'tempTime', readings.temperature, '°C');
            document.getElementById('tempMin').textContent = stats.min;
            document.getElementById('tempMax').textContent = stats.max;
            document.getElementById('tempAvg').textContent = stats.avg;
            document.getElementById('tempCount').textContent = stats.count;
            updateChart('tempChart', chartData, '#ff8c42', 'rgba(255,140,66,0.3)');
        } else {
            updateBigNumber('humValue', 'humTime', readings.humidity, '%');
            document.getElementById('humMin').textContent = stats.min;
            document.getElementById('humMax').textContent = stats.max;
            document.getElementById('humAvg').textContent = stats.avg;
            document.getElementById('humCount').textContent = stats.count;
            updateChart('humChart', chartData, '#00d4ff', 'rgba(0,212,255,0.3)');
        }

        await loadThresholdStatus(type);
    } catch (e) {
        console.error('loadSensorData error:', e);
    }
}

function updateBigNumber(valueId, timeId, reading, unit) {
    const valueEl = document.getElementById(valueId);
    const timeEl = document.getElementById(timeId);

    if (reading && reading.value !== undefined) {
        valueEl.textContent = reading.value;
        timeEl.textContent = 'آخر تحديث: ' + reading.timestamp;
    } else {
        valueEl.textContent = '--';
        timeEl.textContent = 'لا توجد بيانات بعد';
    }
}

// ==================== Threshold Status ====================
// ==================== Threshold Status ====================
async function loadThresholdStatus(sensorType) {
    try {
        // ✅ تحويل الاسم الكامل إلى المختصر المستخدم في HTML
        const prefix = sensorType === 'temperature' ? 'temp' : 'hum';
        const deviceSelect = document.getElementById(prefix + 'DeviceFilter');
        const statusEl = document.getElementById(prefix + 'ThresholdStatus');

        if (!statusEl) return;

        const selectedDevice = deviceSelect ? deviceSelect.value : '';
        const deviceQuery = selectedDevice ? `?device_id=${selectedDevice}` : '';

        const [thresholds, readings] = await Promise.all([
            api('/api/thresholds'),
            api(`/api/current-readings${deviceQuery}`)
        ]);

        const thresh = thresholds.find(t => t.sensor === sensorType);
        const reading = readings[sensorType];

        if (!thresh) {
            statusEl.innerHTML = '<div style="color:var(--text-muted); text-align:center; padding:20px;"><i class="fa-solid fa-circle-info"></i> لا توجد عتبة محددة لهذا المستشعر</div>';
            return;
        }

        const isTemp = sensorType === 'temperature';
        const accentColor = isTemp ? '#ff8c42' : '#00d4ff';
        const accentBg = isTemp ? 'rgba(255,140,66,0.1)' : 'rgba(0,212,255,0.1)';

        let html = `<div style="display:flex; gap:15px; align-items:center; flex-wrap:wrap; justify-content:center;">`;

        html += `
            <div style="background:${accentBg}; padding:15px 25px; border-radius:12px; text-align:center; min-width:130px; border:1px solid ${accentColor}30;">
                <small style="color:var(--text-muted); display:block; margin-bottom:6px; font-size:0.8rem;">الحد الأدنى</small>
                <div style="font-size:1.6rem; font-weight:900; color:${accentColor};">${thresh.min}</div>
            </div>
            <div style="background:rgba(59,130,246,0.1); padding:15px 25px; border-radius:12px; text-align:center; min-width:130px; border:1px solid rgba(59,130,246,0.3);">
                <small style="color:var(--text-muted); display:block; margin-bottom:6px; font-size:0.8rem;">الحد الأعلى</small>
                <div style="font-size:1.6rem; font-weight:900; color:#3b82f6;">${thresh.max}</div>
            </div>
        `;

        if (reading && reading.value !== undefined) {
            const val = parseFloat(reading.value);
            const isNormal = val >= thresh.min && val <= thresh.max;
            const statusColor = isNormal ? '#10b981' : '#ef4444';
            const statusBg = isNormal ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.15)';
            const statusText = isNormal ? 'القيمة ضمن الحدود المسموحة' : 'تنبيه! القيمة خارج الحدود';
            const statusIcon = isNormal ? 'fa-circle-check' : 'fa-triangle-exclamation';

            html += `
                <div style="background:${statusBg}; padding:15px 25px; border-radius:12px; text-align:center; min-width:200px; border:1px solid ${statusColor}40; flex:1;">
                    <small style="color:var(--text-muted); display:block; margin-bottom:6px; font-size:0.8rem;">القيمة الحالية</small>
                    <div style="font-size:2rem; font-weight:900; color:${statusColor}; line-height:1;">${val}</div>
                    <small style="color:${statusColor}; font-weight:700; font-size:0.85rem; display:block; margin-top:8px;">
                        <i class="fa-solid ${statusIcon}"></i> ${statusText}
                    </small>
                </div>
            `;
        } else {
            html += `
                <div style="background:rgba(255,255,255,0.03); padding:15px 25px; border-radius:12px; text-align:center; min-width:200px; border:1px solid var(--border); flex:1;">
                    <small style="color:var(--text-muted); display:block; margin-bottom:6px; font-size:0.8rem;">القيمة الحالية</small>
                    <div style="font-size:1.6rem; font-weight:900; color:var(--text-muted);">--</div>
                    <small style="color:var(--text-muted); font-size:0.8rem; display:block; margin-top:8px;">لا توجد بيانات حالياً</small>
                </div>
            `;
        }

        html += '</div>';
        statusEl.innerHTML = html;
    } catch (e) {
        console.error('loadThresholdStatus error:', e);
    }
}

// ==================== Devices ====================
// ==================== Devices ====================
let allDevices = [];

async function loadDevices() {
    try {
        allDevices = await api('/api/devices');
        document.getElementById('devTotal').textContent = allDevices.length;
        document.getElementById('devOnline').textContent =
            allDevices.filter(d => d.status === 'online').length;
        document.getElementById('devOffline').textContent =
            allDevices.filter(d => d.status !== 'online').length;

        document.getElementById('devicesTableBody').innerHTML = allDevices.map((d, i) =>
            `<tr>
                <td>${i+1}</td>
                <td>${d.code}</td>
                <td>${d.name}</td>
                <td><span class="badge protocol-badge">${d.protocol || 'HTTP'}</span></td>
                <td><span class="status-badge status-${d.status}">${d.status === 'online' ? '🟢 متصل' : '🔴 غير متصل'}</span></td>
                <td>
                    <button class="btn-icon" onclick="viewDevice(${d.id})" title="عرض"><i class="fa-solid fa-eye"></i></button>
                    <button class="btn-icon" onclick="editDevice(${d.id})" title="تعديل"><i class="fa-solid fa-edit"></i></button>
                    <button class="btn-icon" onclick="deleteDevice(${d.id})" title="حذف"><i class="fa-solid fa-trash"></i></button>
                </td>
            </tr>`
        ).join('');

        // تطبيق البحث
        document.getElementById('deviceSearch').addEventListener('input', function(e) {
            filterDevices(e.target.value);
        });
    } catch (e) { console.error(e); }
}

function filterDevices(searchTerm) {
    const rows = document.querySelectorAll('#devicesTableBody tr');
    const term = searchTerm.toLowerCase();
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(term) ? '' : 'none';
    });
}

async function addDevice(e) {
    e.preventDefault();
    try {
        const res = await api('/api/devices', {
            method: 'POST',
            body: JSON.stringify({
                device_code: document.getElementById('newDeviceCode').value,
                name: document.getElementById('newDeviceName').value,
                encryption_key: document.getElementById('newEncryptionKey').value,
                protocol: document.getElementById('newProtocol').value
            })
        });
        showToast('تم الإضافة', 'success');
        closeModal('deviceModal');
        document.getElementById('newDeviceCode').value = '';
        document.getElementById('newDeviceName').value = '';
        document.getElementById('newEncryptionKey').value = '';
        loadDevices();
    } catch (e) {
        showToast('موجود مسبقاً أو خطأ', 'error');
    }
}

async function viewDevice(id) {
    try {
        const device = await api(`/api/devices/${id}`);
        document.getElementById('viewDeviceCode').textContent = device.code;
        document.getElementById('viewDeviceName').textContent = device.name;
        document.getElementById('viewDeviceStatus').textContent = device.status === 'online' ? '🟢 متصل' : '🔴 غير متصل';
        document.getElementById('viewEncryptionKey').textContent = device.encryption_key || 'لا يوجد';
        document.getElementById('viewProtocol').textContent = device.protocol || 'HTTP';
        document.getElementById('viewInterval').textContent = device.interval ? `${device.interval} ثانية` : '10 ثانية';
        document.getElementById('viewLastSeen').textContent = device.last_seen || 'لا توجد بيانات';
        document.getElementById('viewUuid').textContent = device.uuid || 'لا يوجد';
        openModal('viewDeviceModal');
    } catch (e) {
        showToast('خطأ في تحميل البيانات', 'error');
    }
}

async function editDevice(id) {
    try {
        const device = await api(`/api/devices/${id}`);
        document.getElementById('editDeviceId').value = device.id;
        document.getElementById('editDeviceCode').value = device.code;
        document.getElementById('editDeviceName').value = device.name;
        document.getElementById('editEncryptionKey').value = device.encryption_key || '';
        document.getElementById('editProtocol').value = device.protocol || 'HTTP';
        document.getElementById('editInterval').value = device.interval || 10;
        openModal('editDeviceModal');
    } catch (e) {
        showToast('خطأ في تحميل البيانات', 'error');
    }
}

async function updateDevice(e) {
    e.preventDefault();
    try {
        const id = document.getElementById('editDeviceId').value;
        await api(`/api/devices/${id}`, {
            method: 'PUT',
            body: JSON.stringify({
                name: document.getElementById('editDeviceName').value,
                encryption_key: document.getElementById('editEncryptionKey').value,
                protocol: document.getElementById('editProtocol').value,
                interval: parseInt(document.getElementById('editInterval').value)
            })
        });
        showToast('تم التحديث', 'success');
        closeModal('editDeviceModal');
        loadDevices();
    } catch (e) {
        showToast('خطأ في التحديث', 'error');
    }
}

async function deleteDevice(id) {
    if (!confirm('هل أنت متأكد من حذف هذا الجهاز؟')) return;
    try {
        await api(`/api/devices/${id}`, { method: 'DELETE' });
        showToast('تم الحذف', 'success');
        loadDevices();
    } catch (e) { showToast('خطأ', 'error'); }
}

// ==================== Thresholds ====================
async function loadThresholds() {
    try {
        const [thresholds, settings] = await Promise.all([
            api('/api/thresholds'),
            api('/api/settings')
        ]);

        const tempT = thresholds.find(t => t.sensor === 'temperature');
        const humT = thresholds.find(t => t.sensor === 'humidity');

        if (tempT) {
            document.getElementById('tempThreshMin').textContent = tempT.min;
            document.getElementById('tempThreshMax').textContent = tempT.max;
        }
        if (humT) {
            document.getElementById('humThreshMin').textContent = humT.min;
            document.getElementById('humThreshMax').textContent = humT.max;
        }
        if (settings.alert_email) {
            document.getElementById('alertEmailInput').value = settings.alert_email;
        }
    } catch (e) { console.error(e); }
}

async function updateThreshold(e, sensorType) {
    e.preventDefault();
    const minVal = document.getElementById(sensorType === 'temperature' ? 'tempNewMin' : 'humNewMin').value;
    const maxVal = document.getElementById(sensorType === 'temperature' ? 'tempNewMax' : 'humNewMax').value;

    try {
        await api('/api/thresholds', {
            method: 'POST',
            body: JSON.stringify({ sensor_type: sensorType, min_value: minVal, max_value: maxVal })
        });
        showToast('تم التحديث', 'success');
        loadThresholds();
    } catch (e) { showToast('خطأ', 'error'); }
}

async function updateEmail(e) {
    e.preventDefault();
    try {
        await api('/api/settings', {
            method: 'POST',
            body: JSON.stringify({ alert_email: document.getElementById('alertEmailInput').value })
        });
        showToast('تم الحفظ', 'success');
    } catch (e) { showToast('خطأ', 'error'); }
}

// ==================== Alerts ====================
async function loadAlerts() {
    try {
        const data = await api(`/api/alerts?page=${currentPage}`);
        document.getElementById('alertTotal').textContent = data.stats.total;
        document.getElementById('alertSent').textContent = data.stats.sent;
        document.getElementById('alertFailed').textContent = data.stats.failed;

        document.getElementById('alertsTableBody').innerHTML = data.alerts.map((a, i) =>
            `<tr><td>${i+1}</td><td>${a.msg}</td><td>${a.time}</td><td>${a.email_sent ? 'نعم' : 'لا'}</td>
             <td><button class="btn-icon" onclick="deleteAlert(${a.id})"><i class="fa-solid fa-trash"></i></button></td></tr>`
        ).join('');

        renderPagination(data);
    } catch (e) { console.error(e); }
}

function renderPagination(data) {
    const container = document.getElementById('alertsPagination');
    if (!container || data.total_pages <= 1) {
        if (container) container.innerHTML = '';
        return;
    }

    let html = '';
    if (data.has_prev) {
        html += `<button class="page-btn" onclick="currentPage--; loadAlerts();">السابق</button>`;
    }

    for (let i = 1; i <= data.total_pages; i++) {
        html += `<button class="page-btn ${i === data.page ? 'active' : ''}" onclick="currentPage=${i}; loadAlerts();">${i}</button>`;
    }

    if (data.has_next) {
        html += `<button class="page-btn" onclick="currentPage++; loadAlerts();">التالي</button>`;
    }

    container.innerHTML = html;
}

async function deleteAlert(id) {
    if (!confirm('هل أنت متأكد؟')) return;
    try {
        await api(`/api/alerts/${id}`, { method: 'DELETE' });
        showToast('تم الحذف', 'success');
        loadAlerts();
    } catch (e) { showToast('خطأ', 'error'); }
}

// ==================== Clear Data ====================
async function clearAllSensorData() {
    if (!confirm('حذف جميع البيانات؟')) return;
    try {
        await api('/api/sensor-data', { method: 'DELETE' });
        showToast('تم الحذف', 'success');
        loadDashboard();
    } catch (e) { showToast('خطأ', 'error'); }
}

async function clearSensorDataByType(sensorType) {
    if (!confirm(`حذف بيانات ${sensorType}؟`)) return;
    try {
        await api(`/api/sensor-data?sensor_type=${sensorType}`, { method: 'DELETE' });
        showToast('تم الحذف', 'success');
        loadSensorData(sensorType);
    } catch (e) { showToast('خطأ', 'error'); }
}





// ==================== Latency Comparison (HTTP vs MQTT) ====================
let latencyBarChart = null;

async function loadLatencyComparison() {
    try {
        const data = await api('/api/latency-comparison');

        document.getElementById('latAvgHttp').textContent = data.HTTP.avg;
        document.getElementById('latAvgMqtt').textContent = data.MQTT.avg;
        document.getElementById('latDiff').textContent = data.difference.avg;
        document.getElementById('latFaster').textContent = data.difference.faster_protocol;

        document.getElementById('latAvgHttpT').textContent = data.HTTP.avg;
        document.getElementById('latMaxHttp').textContent = data.HTTP.max;
        document.getElementById('latMinHttp').textContent = data.HTTP.min;
        document.getElementById('latCountHttp').textContent = data.HTTP.count;

        document.getElementById('latAvgMqttT').textContent = data.MQTT.avg;
        document.getElementById('latMaxMqtt').textContent = data.MQTT.max;
        document.getElementById('latMinMqtt').textContent = data.MQTT.min;
        document.getElementById('latCountMqtt').textContent = data.MQTT.count;

        const ctx = document.getElementById('latencyBarChart').getContext('2d');
        if (latencyBarChart) latencyBarChart.destroy();

        latencyBarChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['متوسط التأخير', 'أعلى تأخير', 'أدنى تأخير'],
                datasets: [
                    {
                        label: 'HTTP (ms)',
                        data: [data.HTTP.avg, data.HTTP.max, data.HTTP.min],
                        backgroundColor: 'rgba(0,212,255,0.5)',
                        borderColor: '#00d4ff',
                        borderWidth: 2,
                        borderRadius: 8
                    },
                    {
                        label: 'MQTT (ms)',
                        data: [data.MQTT.avg, data.MQTT.max, data.MQTT.min],
                        backgroundColor: 'rgba(139,92,246,0.5)',
                        borderColor: '#8b5cf6',
                        borderWidth: 2,
                        borderRadius: 8
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { labels: { color: '#94a3b8' } }
                },
                scales: {
                    x: {
                        grid: { color: 'rgba(255,255,255,0.05)' },
                        ticks: { color: '#94a3b8' }
                    },
                    y: {
                        beginAtZero: true,
                        grid: { color: 'rgba(255,255,255,0.05)' },
                        ticks: { color: '#94a3b8' }
                    }
                }
            }
        });
    } catch (e) { console.error('loadLatencyComparison error:', e); }
}

let radarChart = null;

async function loadModelsComparison() {
    try {
        const sensorSel = document.getElementById('modelSensorSelect');
        const sensorType = sensorSel ? sensorSel.value : 'temperature';
        const data = await api(`/api/models-comparison?sensor_type=${sensorType}`);
        const tableEl = document.getElementById('modelsTable');

        if (data.message) {
            tableEl.innerHTML = `<div class="alert alert-info">${data.message}</div>`;
            return;
        }

        const models = data.models;
        const sensorLabel = data.sensor_type === 'temperature' ? '🌡️ حرارة' : '💧 رطوبة';
        const icons = { statistical: 'fa-calculator', ml_sensor: 'fa-robot', ml_latency: 'fa-tree' };
        const rows = Object.entries(models).map(([key, m]) => `
            <tr>
                <td><i class="fa-solid ${icons[key] || 'fa-microchip'}"></i> ${m.name}</td>
                <td>${key === 'statistical' ? m.score : m.score + ' %'}</td>
                <td>${m.is_anomaly ? '<span class="badge bg-danger">شذوذ</span>' : '<span class="badge bg-success">طبيعي</span>'}</td>
            </tr>`).join('');
        let html = `
            <table class="table table-custom">
                <thead>
                    <tr>
                        <th>النموذج</th>
                        <th>الدرجة (Score)</th>
                        <th>الحالة</th>
                    </tr>
                </thead>
                <tbody>${rows}</tbody>
            </table>
            <div class="mt-3 text-center">
                <small class="text-muted">المستشعر المقيَّم: ${sensorLabel} | القيمة: ${data.value} | زمن الاستجابة: ${data.latency_ms}ms</small><br>
                <strong>القرار النهائي للنظام: </strong>
                ${data.is_anomaly ? '<span class="text-danger fw-bold">⚠️ حالة شاذة</span>' : '<span class="text-success fw-bold">✓ حالة طبيعية</span>'}
            </div>
        `;
        tableEl.innerHTML = html;

        // تحديث الرسم البياني (أعمدة أفقية متناسقة)
        const ctx = document.getElementById('modelsRadarChart').getContext('2d');
        if (radarChart) radarChart.destroy();

        // تحويل الدرجات لنسب مئوية لتظهر بشكل متناسق في الرسم البياني
        const statScore = Math.min(models.statistical.score / 3.0 * 100, 100); // 3.0 is threshold
        const chartScores = [
            statScore,
            Math.min(models.ml_sensor.score, 100),
            Math.min(models.ml_latency.score, 100)
        ];
        const chartLabels = ['إحصائي (Z-Score)', 'شبكة LSTM المدربة', 'غابة العزل Isolation Forest'];

        radarChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: chartLabels,
                datasets: [{
                    label: 'نسبة السلوك غير الاعتيادي (%)',
                    data: chartScores,
                    backgroundColor: [
                        'rgba(139, 92, 246, 0.5)',
                        'rgba(0, 212, 255, 0.5)',
                        'rgba(255, 140, 66, 0.5)'
                    ],
                    borderColor: ['#8b5cf6', '#00d4ff', '#ff8c42'],
                    borderWidth: 2,
                    borderRadius: 8
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        max: 100,
                        grid: { color: 'rgba(255,255,255,0.05)' },
                        ticks: { color: '#94a3b8', callback: v => v + '%' }
                    },
                    y: {
                        grid: { display: false },
                        ticks: { color: '#94a3b8' }
                    }
                }
            }
        });

    } catch (e) { console.error(e); }
}
