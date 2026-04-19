// app.js - версия с 5 графиками (исправленная)

let ageChart, ageChart2, transactionChart, transactionTypeChart, cityTransactionChart;
let trendChart, paymentTrendChart;

function renderTrendChart(trendData) {
    const canvas = document.getElementById('trendChart');
    if (!canvas) {
        console.warn('trendChart canvas not found');
        return;
    }

    const ctx = canvas.getContext('2d');

    if (trendChart) {
        trendChart.destroy();
    }

    const history = trendData.history || [];
    const forecast = trendData.forecast || [];
    const category = trendData.category || 'Все категории';

    // Формируем заголовок
    let chartTitle = `📈 Прогноз транзакций`;
    if (category && category !== 'Все категории') {
        chartTitle += ` для категории: ${category}`;
    } else {
        chartTitle += ` (Все категории)`;
    }

    const historyDates = history.map(d => {
        const date = new Date(d.ds);
        return date.toISOString().split('T')[0];
    });
    const forecastDates = forecast.map(d => {
        const date = new Date(d.ds);
        return date.toISOString().split('T')[0];
    });

    const labels = [...historyDates, ...forecastDates];

    const historyValues = history.map(d => d.y);

    const forecastValues = [
        ...Array(history.length).fill(null),
        ...forecast.map(d => d.yhat)
    ];

    trendChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: `Факт`,
                    data: historyValues,
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    tension: 0.3,
                    fill: false,
                    borderWidth: 2,
                    pointRadius: 2,
                    pointHoverRadius: 4
                },
                {
                    label: `Прогноз`,
                    data: forecastValues,
                    borderColor: '#ef4444',
                    borderDash: [5, 5],
                    tension: 0.3,
                    fill: false,
                    borderWidth: 2,
                    pointRadius: 2,
                    pointHoverRadius: 4
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
                legend: {
                    position: 'top',
                    labels: { 
                        color: '#e2e8f0',
                        usePointStyle: true,
                        boxWidth: 10,
                        padding: 15
                    }
                },
                title: {
                    display: true,
                    text: chartTitle,
                    color: '#e2e8f0',
                    font: { 
                        size: 14,
                        weight: 'bold'
                    },
                    padding: {
                        top: 10,
                        bottom: 20
                    }
                },
                tooltip: {
                    backgroundColor: '#1e293b',
                    titleColor: '#f8fafc',
                    bodyColor: '#cbd5e1',
                    borderColor: '#334155',
                    borderWidth: 1,
                    callbacks: {
                        label: function(context) {
                            let value = context.raw;
                            if (value === null) return null;
                            
                            let displayValue = 0;
                            if (typeof value === 'number') {
                                displayValue = value;
                            }
                            
                            return `${context.dataset.label}: ${displayValue.toFixed(2)} ₽`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    ticks: { 
                        color: '#e2e8f0',
                        maxRotation: 45,
                        minRotation: 45
                    },
                    grid: {
                        color: '#334155',
                        drawBorder: false
                    }
                },
                y: {
                    beginAtZero: true,
                    ticks: { 
                        color: '#e2e8f0',
                        callback: (value) => {
                            if (value >= 1000000) {
                                return (value / 1000000).toFixed(1) + 'M ₽';
                            } else if (value >= 1000) {
                                return (value / 1000).toFixed(0) + 'K ₽';
                            }
                            return value.toFixed(0) + ' ₽';
                        }
                    },
                    grid: {
                        color: '#334155',
                        drawBorder: false
                    }
                }
            }
        }
    });
}

function renderPaymentTrendChart(paymentData) {
    const canvas = document.getElementById('paymentTrendChart');
    if (!canvas) {
        console.warn('paymentTrendChart canvas not found');
        return;
    }
    
    const ctx = canvas.getContext('2d');
    
    // Уничтожаем существующий график
    if (paymentTrendChart) {
        paymentTrendChart.destroy();
    }
    
    // Проверяем наличие данных
    if (!paymentData || (!paymentData.all_methods && !paymentData.payment_name)) {
        console.warn('No payment trend data available');
        return;
    }
    
    // Создаем датасеты для каждого метода оплаты
    const datasets = [];
    const colors = {
        1: '#10b981', // наличные - зеленый
        2: '#3b82f6', // карта - синий
        3: '#f59e0b'  // QR - оранжевый
    };
    
    let allLabels = new Set();
    
    // Определяем заголовок графика на основе контекста
    let chartTitle = '📈 Прогноз сумм по методам оплаты';
    
    if (paymentData.context) {
        if (paymentData.context.has_category_filter) {
            chartTitle += ` (Категория: ${paymentData.context.category_name})`;
        } else {
            chartTitle += ` (Все категории)`;
        }
        
        if (paymentData.context.has_payment_filter) {
            chartTitle += ` - ${paymentData.context.payment_name}`;
        }
    }
    
    // Если есть данные по всем методам
    if (paymentData.all_methods) {
        Object.entries(paymentData.all_methods).forEach(([method, data]) => {
            const historyDates = data.history.map(d => d.ds);
            const forecastDates = data.forecast.map(d => d.ds);
            
            historyDates.forEach(date => allLabels.add(date));
            forecastDates.forEach(date => allLabels.add(date));
            
            const historyValues = data.history.map(d => d.y);
            const forecastValues = [
                ...Array(historyValues.length).fill(null),
                ...data.forecast.map(d => d.yhat)
            ];
            
            datasets.push({
                label: `${data.method_name} (факт)`,
                data: historyValues,
                borderColor: colors[method] || '#6b7280',
                backgroundColor: 'transparent',
                tension: 0.3,
                fill: false,
                borderWidth: 2,
                pointRadius: 2,
                pointHoverRadius: 4
            });
            
            datasets.push({
                label: `${data.method_name} (прогноз)`,
                data: forecastValues,
                borderColor: colors[method] || '#6b7280',
                backgroundColor: 'transparent',
                borderDash: [5, 5],
                tension: 0.3,
                fill: false,
                borderWidth: 2,
                pointRadius: 2,
                pointHoverRadius: 4
            });
        });
    } 
    // Если выбран конкретный метод
    else if (paymentData.history && paymentData.forecast) {
        const historyDates = paymentData.history.map(d => d.ds);
        const forecastDates = paymentData.forecast.map(d => d.ds);
        
        historyDates.forEach(date => allLabels.add(date));
        forecastDates.forEach(date => allLabels.add(date));
        
        const historyValues = paymentData.history.map(d => d.y);
        const forecastValues = [
            ...Array(historyValues.length).fill(null),
            ...paymentData.forecast.map(d => d.yhat)
        ];
        
        const methodName = paymentData.payment_name || 'Метод оплаты';
        const methodId = paymentData.payment_method || 1;
        
        datasets.push({
            label: `${methodName} (факт)`,
            data: historyValues,
            borderColor: colors[methodId] || '#6b7280',
            backgroundColor: 'transparent',
            tension: 0.3,
            fill: false,
            borderWidth: 2,
            pointRadius: 2,
            pointHoverRadius: 4
        });
        
        datasets.push({
            label: `${methodName} (прогноз)`,
            data: forecastValues,
            borderColor: colors[methodId] || '#6b7280',
            backgroundColor: 'transparent',
            borderDash: [5, 5],
            tension: 0.3,
            fill: false,
            borderWidth: 2,
            pointRadius: 2,
            pointHoverRadius: 4
        });
    }
    
    const labels = Array.from(allLabels).sort();
    
    // Приводим данные к единой длине
    datasets.forEach(dataset => {
        if (dataset.data.length < labels.length) {
            const padding = Array(labels.length - dataset.data.length).fill(null);
            dataset.data = [...dataset.data, ...padding];
        }
    });
    
    paymentTrendChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: {
                    position: 'top',
                    labels: { 
                        color: '#e2e8f0',
                        usePointStyle: true,
                        boxWidth: 10,
                        padding: 15
                    }
                },
                title: {
                    display: true,
                    text: chartTitle,
                    color: '#e2e8f0',
                    font: { 
                        size: 14,
                        weight: 'bold'
                    },
                    padding: {
                        top: 10,
                        bottom: 20
                    }
                },
                tooltip: {
                    backgroundColor: '#1e293b',
                    titleColor: '#f8fafc',
                    bodyColor: '#cbd5e1',
                    borderColor: '#334155',
                    borderWidth: 1,
                    callbacks: {
                        label: function(context) {
                            let value = context.raw;
                            if (value === null) return null;
                            
                            let displayValue = 0;
                            if (typeof value === 'number') {
                                displayValue = value;
                            }
                            
                            return `${context.dataset.label}: ${displayValue.toFixed(2)} ₽`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    ticks: { 
                        color: '#e2e8f0',
                        maxRotation: 45,
                        minRotation: 45
                    },
                    grid: {
                        color: '#334155',
                        drawBorder: false
                    }
                },
                y: {
                    beginAtZero: true,
                    ticks: { 
                        color: '#e2e8f0',
                        callback: (value) => {
                            if (value >= 1000000) {
                                return (value / 1000000).toFixed(1) + 'M ₽';
                            } else if (value >= 1000) {
                                return (value / 1000).toFixed(0) + 'K ₽';
                            }
                            return value.toFixed(0) + ' ₽';
                        }
                    },
                    grid: {
                        color: '#334155',
                        drawBorder: false
                    }
                }
            }
        }
    });
}

// Вспомогательная функция для получения всех дат (больше не нужна, но оставим)
function getAllDates(paymentData) {
    const allDates = new Set();
    if (paymentData.all_methods) {
        Object.values(paymentData.all_methods).forEach(data => {
            data.history.forEach(d => allDates.add(d.ds));
            data.forecast.forEach(d => allDates.add(d.ds));
        });
    }
    return Array.from(allDates).sort();
}

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
        
        // Отрисовываем все графики
        if (data.trend) {
            console.log('Rendering trend chart with data:', data.trend);
            renderTrendChart(data.trend);
        }
        
        if (data.payment_trend) {
            console.log('Rendering payment trend chart with data:', data.payment_trend);
            renderPaymentTrendChart(data.payment_trend);
        }
        
        if (data.age_categories) {
            renderAgeCategoryChart(data.age_categories, 'ageCategoryChart', 'ageChart');
        }
        
        if (data.age_categories_2) {
            renderAgeCategoryChart(data.age_categories_2, 'ageCategoryChart2', 'ageChart2');
        }
        
        if (data.transtions) {
            renderTransactionChart(data.transtions);
        }
        
        if (data.transtions_type) {
            renderTransactionTypeChart(data.transtions_type);
        }
        
        if (data.transtions_by_city) {
            renderCityTransactionChart(data.transtions_by_city);
        }
        
    } catch (error) {
        console.error('Error fetching data:', error);
    }
}

// Универсальная функция для круговых диаграмм
function renderAgeCategoryChart(ageData, canvasId, chartVar) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) {
        console.warn(`Canvas "${canvasId}" not found`);
        return;
    }
    
    const ctx = canvas.getContext('2d');
    
    // Уничтожаем существующий график
    if (chartVar === 'ageChart' && ageChart) {
        ageChart.destroy();
    } else if (chartVar === 'ageChart2' && ageChart2) {
        ageChart2.destroy();
    }
    
    if (!ageData || ageData.length === 0) {
        console.warn(`No data available for ${canvasId}`);
        return;
    }
    
    const categories = ageData.map(item => item.category);
    const counts = ageData.map(item => item.count || 0);
    
    // Цветовая палитра для секторов
    const colors = [
        '#ef4444', '#f97316', '#f59e0b', '#eab308', '#84cc16',
        '#22c55e', '#10b981', '#14b8a6', '#06b6d4', '#0ea5e9',
        '#3b82f6', '#6366f1', '#8b5cf6', '#a855f7', '#d946ef'
    ];
    
    const newChart = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: categories,
            datasets: [{
                label: 'Количество транзакций',
                data: counts,
                backgroundColor: colors.slice(0, categories.length),
                borderColor: '#1e293b',
                borderWidth: 2,
                hoverOffset: 10
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: { 
                        color: '#e2e8f0',
                        font: { size: 11 },
                        padding: 10,
                        usePointStyle: true,
                        pointStyle: 'circle'
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            
                            return [
                                `${label}: ${value} транзакций`,
                                `${percentage}% от общего числа`
                            ];
                        }
                    },
                    backgroundColor: '#1e293b',
                    titleColor: '#e2e8f0',
                    bodyColor: '#cbd5e1',
                    borderColor: '#334155',
                    borderWidth: 1
                }
            },
            layout: {
                padding: 10
            }
        }
    });
    
    // Сохраняем график в соответствующую переменную
    if (chartVar === 'ageChart') {
        ageChart = newChart;
    } else if (chartVar === 'ageChart2') {
        ageChart2 = newChart;
    }
}

// 3. Столбчатая диаграмма - Средний чек по категориям
function renderTransactionChart(transactionsData) {
    const canvas = document.getElementById('transactionChart');
    if (!canvas) {
        console.warn('Canvas "transactionChart" not found');
        return;
    }
    
    const ctx = canvas.getContext('2d');
    
    if (transactionChart) {
        transactionChart.destroy();
    }
    
    if (!transactionsData || transactionsData.length === 0) {
        console.warn('No transaction data available');
        return;
    }
    
    const categories = transactionsData.map(item => item.category || 'Неизвестно');
    const avgSums = transactionsData.map(item => {
        const val = item.avg_sum;
        if (typeof val === 'number') return val;
        if (typeof val === 'string') return parseFloat(val) || 0;
        return 0;
    });
    
    const counts = transactionsData.map(item => {
        const val = item.count;
        if (typeof val === 'number') return val;
        if (typeof val === 'string') return parseInt(val) || 0;
        return 0;
    });
    
    transactionChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: categories,
            datasets: [{
                label: 'Средний чек',
                data: avgSums,
                backgroundColor: '#8b5cf6',
                borderRadius: 8,
                barPercentage: 0.8,
                categoryPercentage: 0.9
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: '#e2e8f0' }
                },
                tooltip: {
                    enabled: true,
                    backgroundColor: '#1e293b',
                    titleColor: '#f8fafc',
                    bodyColor: '#cbd5e1',
                    borderColor: '#334155',
                    borderWidth: 1,
                    callbacks: {
                        label: function(context) {
                            try {
                                const index = context.dataIndex;
                                const rawValue = context.raw;
                                
                                let value = 0;
                                if (typeof rawValue === 'number') {
                                    value = rawValue;
                                } else if (typeof rawValue === 'object' && rawValue !== null) {
                                    value = rawValue.y || rawValue.x || 0;
                                }
                                
                                const count = counts[index] || 0;
                                
                                return [
                                    `💰 Средний чек: ${value.toFixed(2)} ₽`,
                                    `📊 Количество: ${count} транзакций`
                                ];
                            } catch (error) {
                                console.error('Tooltip error:', error);
                                return ['Ошибка отображения данных'];
                            }
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { 
                        color: '#e2e8f0',
                        callback: function(value) {
                            try {
                                const numValue = typeof value === 'number' ? value : parseFloat(value) || 0;
                                return numValue.toFixed(0) + ' ₽';
                            } catch (e) {
                                return value;
                            }
                        }
                    },
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

// 4. Столбчатая диаграмма - Популярные акции
function renderTransactionTypeChart(typesData) {
    const canvas = document.getElementById('transactionTypeChart');
    if (!canvas) {
        console.warn('Canvas "transactionTypeChart" not found');
        return;
    }
    
    const ctx = canvas.getContext('2d');
    
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
            datasets: typesData.combined.datasets.map((ds, index) => ({
                ...ds,
                backgroundColor: ds.label.includes('Последние') ? '#10b981' : '#6b7280',
                borderRadius: 8,
                barPercentage: 0.8,
                categoryPercentage: 0.9
            }))
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: '#e2e8f0' }
                },
                tooltip: {
                    backgroundColor: '#1e293b',
                    titleColor: '#f8fafc',
                    bodyColor: '#cbd5e1',
                    borderColor: '#334155',
                    borderWidth: 1,
                    callbacks: {
                        label: function(context) {
                            const value = context.raw;
                            const datasetLabel = context.dataset.label;
                            
                            let displayValue = 0;
                            if (typeof value === 'number') {
                                displayValue = value;
                            } else if (typeof value === 'object' && value !== null) {
                                displayValue = value.y || value.x || 0;
                            }
                            
                            return `${datasetLabel}: ${displayValue} транзакций`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
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

// 5. Самые популярные категории по городам
function renderCityTransactionChart(cityData) {
    const canvas = document.getElementById('cityTransactionChart');
    if (!canvas) {
        console.warn('Canvas "cityTransactionChart" not found');
        return;
    }
    
    const ctx = canvas.getContext('2d');
    
    if (cityTransactionChart) {
        cityTransactionChart.destroy();
    }
    
    if (!cityData || Object.keys(cityData).length === 0) {
        console.warn('No city transaction data available');
        return;
    }
    
    const cities = Object.keys(cityData).sort();
    
    const categoryColors = [
        '#ef4444', '#f97316', '#f59e0b', '#eab308', '#84cc16',
        '#22c55e', '#10b981', '#14b8a6', '#06b6d4', '#0ea5e9',
        '#3b82f6', '#6366f1', '#8b5cf6', '#a855f7', '#d946ef',
        '#ec4899',
    ];
    
    const allCategories = new Set();
    cities.forEach(city => {
        cityData[city].forEach(item => {
            allCategories.add(item.category);
        });
    });
    
    const datasets = Array.from(allCategories).map((category, index) => {
        const data = cities.map(city => {
            const cityCategory = cityData[city].find(item => item.category === category);
            return cityCategory ? cityCategory.count : 0;
        });
        
        return {
            label: category,
            data: data,
            backgroundColor: categoryColors[index % categoryColors.length],
            borderRadius: 8,
            barPercentage: 4,
            categoryPercentage: 0.9
        };
    });
    
    cityTransactionChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: cities,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: { 
                        color: '#e2e8f0',
                        font: { size: 11 },
                        usePointStyle: true,
                        boxWidth: 12
                    }
                },
                tooltip: {
                    enabled: true,
                    backgroundColor: '#1e293b',
                    titleColor: '#f8fafc',
                    bodyColor: '#cbd5e1',
                    borderColor: '#334155',
                    borderWidth: 1,
                    callbacks: {
                        title: function(context) {
                            return `🏙️ ${context[0].label}`;
                        },
                        label: function(context) {
                            const city = context.label;
                            const category = context.dataset.label;
                            
                            let value = 0;
                            if (typeof context.raw === 'number') {
                                value = context.raw;
                            } else if (typeof context.raw === 'object' && context.raw !== null) {
                                value = context.raw.y || context.raw.x || 0;
                            }
                            
                            const cityCatData = cityData[city]?.find(item => item.category === category);
                            const avgSum = cityCatData ? cityCatData.avg_sum : 0;
                            
                            return [
                                `📂 Категория: ${category}`,
                                `📊 Количество: ${value} транзакций`,
                                `💰 Средний чек: ${avgSum.toFixed(2)} ₽`
                            ];
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { 
                        color: '#e2e8f0'
                    },
                    grid: { color: '#334155' },
                    title: {
                        display: true,
                        text: 'Количество транзакций',
                        color: '#e2e8f0'
                    }
                },
                x: {
                    ticks: { 
                        color: '#e2e8f0',
                        maxRotation: 45,
                        minRotation: 45
                    },
                    grid: { display: false }
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
    
    const dateFromInput = document.getElementById('date_from');
    const dateToInput = document.getElementById('date_to');
    
    if (dateFromInput) {
        dateFromInput.value = thirtyDaysAgo.toISOString().split('T')[0];
    }
    
    if (dateToInput) {
        dateToInput.value = today.toISOString().split('T')[0];
    }
    
    // Загружаем данные
    renderCharts();
    
    // Добавляем обработчик на кнопку обновления
    const refreshBtn = document.getElementById('refreshBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', renderCharts);
    }
});