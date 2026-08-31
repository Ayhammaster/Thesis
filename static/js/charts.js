// ==================== Chart Management ====================
const chartInstances = {};

function initChart(canvasId, labels, data, borderColor, backgroundColor) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;

    if (chartInstances[canvasId]) {
        chartInstances[canvasId].destroy();
    }

    chartInstances[canvasId] = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'القيمة',
                data: data,
                borderColor: borderColor,
                backgroundColor: backgroundColor,
                fill: true,
                tension: 0.4,
                pointRadius: 4,
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(255,255,255,0.05)' },
                    ticks: { color: '#94a3b8' }
                },
                y: {
                    grid: { color: 'rgba(255,255,255,0.05)' },
                    ticks: { color: '#94a3b8' }
                }
            }
        }
    });

    return chartInstances[canvasId];
}

function updateChart(canvasId, chartData, borderColor, backgroundColor) {
    if (chartData && chartData.labels && chartData.labels.length > 0) {
        initChart(canvasId, chartData.labels, chartData.data, borderColor, backgroundColor);
    }
}
