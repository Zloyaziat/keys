// app.js - исправленная версия

let uiChart, errorChart, transactionChart, transactionTypeChart;

// Функция для получения значений фильтров
function getFilters() {
    return {
        date_from: document.getElementById('date_from').value || null,
        date_to: document.getElementById('date_to').value || null,
        sex: document.getElementById('sex').value || null,
        age_from: document.getElementById('min_age').value ? parseInt(document.getElementById('min_age').value) : null,
        age_to: document.getElementById('max_age').value ? parseInt(document.getElementById('max_age').value) : null,
        city: document.getElementById('city').value || null,
        category: document.getElementById('category').value || null,
        payment_method: document.getElementById('payment').value ? parseInt(document.getElementById('payment').value) : null
    };
}

// Функция для отрисовки всех графиков
async function renderCharts() {
    try {
        const filters = getFilters();
        console.log('Filters:', filters);
        
        const response = await fetch('/api/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(filters)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('API Response:', data);
        
        // Отрисовываем каждый график
        renderUIChart(data.ui);
        renderErrorChart(data.errors);
        renderTransactionChart(data.transtions);
        renderTransactionTypeChart(data.transtions_type);
        
    } catch (error) {
        console.error('Error fetching data:', error);
    }
}

// График кликов по UI
function renderUIChart(uiData) {
    const ctx = document.getElementById('uiChart').getContext('2d');
    
    if (uiChart) {
        uiChart.destroy();
    }
    
    if (!uiData || uiData.length === 0) {
        console.warn('No UI data available');
        return;
    }
    
    const types = uiData.map(item => item.type);
    const oldClicks = uiData.map(item => item.clicks_old || 0);
    const newClicks = uiData.map(item => item.clicks_new || 0);
    
    uiChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: types,
            datasets: [
                {
                    label: 'Старый UI',
                    data: oldClicks,
                    backgroundColor: '#ef4444'
                },
                {
                    label: 'Новый UI',
                    data: newClicks,
                    backgroundColor: '#22c55e'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: '#e2e8f0' }
                }
            },
            scales: {
                y: {
                    ticks: { color: '#e2e8f0' },
                    grid: { color: '#334155' }
                },
                x: {
                    ticks: { color: '#e2e8f0' },
                    grid: { color: '#334155' }
                }
            }
        }
    });
}

// График ошибок по версиям
function renderErrorChart(errorsData) {
    const ctx = document.getElementById('errorChart').getContext('2d');
    
    if (errorChart) {
        errorChart.destroy();
    }
    
    if (!errorsData || !errorsData.combined) {
        console.warn('No error data available');
        return;
    }
    
    errorChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: errorsData.combined.labels,
            datasets: errorsData.combined.datasets.map(ds => ({
                ...ds,
                backgroundColor: ds.label.includes('Последние') ? '#3b82f6' : '#94a3b8'
            }))
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: '#e2e8f0' }
                }
            },
            scales: {
                y: {
                    ticks: { color: '#e2e8f0' },
                    grid: { color: '#334155' }
                },
                x: {
                    ticks: { color: '#e2e8f0' },
                    grid: { color: '#334155' }
                }
            }
        }
    });
}
// График ошибок по версиям - ЛИНЕЙНЫЙ с трендом
function renderErrorChart(errorsData) {
    const ctx = document.getElementById('errorChart').getContext('2d');
    
    if (errorChart) {
        errorChart.destroy();
    }
    
    if (!errorsData || !errorsData.combined) {
        console.warn('No error data available');
        return;
    }
    
    const labels = errorsData.combined.labels;
    const currentPeriod = errorsData.combined.datasets[0].data;
    const previousPeriod = errorsData.combined.datasets[1].data;
    
    // Считаем изменение в процентах
    const changes = labels.map((_, i) => {
        const prev = previousPeriod[i] || 0;
        const curr = currentPeriod[i] || 0;
        if (prev === 0) return 0;
        return ((curr - prev) / prev * 100).toFixed(1);
    });
    
    errorChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: errorsData.combined.datasets[0].label,
                    data: currentPeriod,
                    borderColor: '#ef4444',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    tension: 0.3,
                    fill: true,
                    pointStyle: 'circle',
                    pointRadius: 6,
                    pointHoverRadius: 8
                },
                {
                    label: errorsData.combined.datasets[1].label,
                    data: previousPeriod,
                    borderColor: '#6b7280',
                    backgroundColor: 'transparent',
                    tension: 0.3,
                    borderDash: [5, 5],
                    pointStyle: 'rectRot',
                    pointRadius: 5,
                    pointHoverRadius: 7
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Динамика ошибок по версиям приложения',
                    color: '#e2e8f0',
                    font: { size: 14, weight: 'bold' }
                },
                legend: {
                    labels: { 
                        color: '#e2e8f0',
                        usePointStyle: true
                    }
                },
                tooltip: {
                    callbacks: {
                        footer: function(tooltipItems) {
                            const index = tooltipItems[0].dataIndex;
                            const change = changes[index];
                            const color = change > 0 ? '#ef4444' : '#22c55e';
                            const arrow = change > 0 ? '↑' : '↓';
                            return [
                                `Изменение: ${arrow} ${Math.abs(change)}%`,
                                `Текущий: ${currentPeriod[index]}`,
                                `Предыдущий: ${previousPeriod[index]}`
                            ];
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { color: '#e2e8f0' },
                    grid: { color: '#334155' },
                    title: {
                        display: true,
                        text: 'Количество ошибок',
                        color: '#e2e8f0'
                    }
                },
                x: {
                    ticks: { color: '#e2e8f0' },
                    grid: { display: false },
                    title: {
                        display: true,
                        text: 'Версия приложения',
                        color: '#e2e8f0'
                    }
                }
            }
        }
    });
}
// График среднего чека по категориям
function renderTransactionChart(transactionsData) {
    const ctx = document.getElementById('transactionChart').getContext('2d');
    
    if (transactionChart) {
        transactionChart.destroy();
    }
    
    if (!transactionsData || transactionsData.length === 0) {
        console.warn('No transaction data available');
        return;
    }
    
    const categories = transactionsData.map(item => item.category);
    const avgSums = transactionsData.map(item => item.avg_sum || 0);
    
    transactionChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: categories,
            datasets: [{
                label: 'Средний чек',
                data: avgSums,
                backgroundColor: '#8b5cf6'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: '#e2e8f0' }
                }
            },
            scales: {
                y: {
                    ticks: { color: '#e2e8f0' },
                    grid: { color: '#334155' }
                },
                x: {
                    ticks: { color: '#e2e8f0' },
                    grid: { color: '#334155' }
                }
            }
        }
    });
}

// График популярных акций
function renderTransactionTypeChart(typesData) {
    const ctx = document.getElementById('transactionTypeChart').getContext('2d');
    
    if (transactionTypeChart) {
        transactionTypeChart.destroy();
    }
    
    if (!typesData || !typesData.combined) {
        console.warn('No transaction type data available');
        return;
    }
    
    transactionTypeChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: typesData.combined.labels,
            datasets: typesData.combined.datasets.map(ds => ({
                ...ds,
                backgroundColor: ds.label.includes('Последние') ? '#10b981' : '#6b7280'
            }))
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: '#e2e8f0' }
                }
            },
            scales: {
                y: {
                    ticks: { color: '#e2e8f0' },
                    grid: { color: '#334155' }
                },
                x: {
                    ticks: { color: '#e2e8f0' },
                    grid: { color: '#334155' }
                }
            }
        }
    });
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    console.log('Dashboard initialized');
    
    // Устанавливаем даты по умолчанию
    const today = new Date();
    const thirtyDaysAgo = new Date(today);
    thirtyDaysAgo.setDate(today.getDate() - 30);
    
    document.getElementById('date_from').value = thirtyDaysAgo.toISOString().split('T')[0];
    document.getElementById('date_to').value = today.toISOString().split('T')[0];
    
    // Загружаем данные
    renderCharts();
    
    // Добавляем обработчик на кнопку обновления
    document.getElementById('refreshBtn').addEventListener('click', renderCharts);
});