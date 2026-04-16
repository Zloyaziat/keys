let charts = {};

function destroyChart(id) {
  if (charts[id]) {
    charts[id].destroy();
    delete charts[id];
  }
}

function getFilters() {
  return {
    sex: document.getElementById('sex')?.value || null,
    age_from: document.getElementById('min_age')?.value || null,
    age_to: document.getElementById('max_age')?.value || null,
    payment_method: document.getElementById('payment')?.value || null
  };
}

async function loadDashboard() {
  try {
    const filters = getFilters();
    console.log('Отправляю фильтры:', filters);

    const res = await fetch('/api/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(filters)
    });

    if (!res.ok) {
      throw new Error(`HTTP error! status: ${res.status}`);
    }

    const data = await res.json();
    console.log('Полученные данные:', data);

    // Проверяем наличие данных перед рендерингом
    if (data.ui && Array.isArray(data.ui)) {
      renderUI(data.ui);
      renderErrors(data.ui);
    } else {
      console.warn('Нет данных ui или неверный формат:', data.ui);
    }

    if (data.transtions && Array.isArray(data.transtions)) {
      renderTransactions(data.transtions);
    } else {
      console.warn('Нет данных транзакций или неверный формат:', data.transtions);
    }

  } catch (error) {
    console.error('Ошибка загрузки:', error);
    alert('Ошибка загрузки данных: ' + error.message);
  }
}

function renderUI(data) {
  console.log('Рендеринг UI графика с данными:', data);
  
  const canvas = document.getElementById('uiChart');
  if (!canvas) {
    console.error('Canvas uiChart не найден в DOM');
    return;
  }

  destroyChart('ui');

  if (!data || data.length === 0) {
    console.warn('Нет данных для UI графика');
    return;
  }

  const ctx = canvas.getContext('2d');
  
  try {
    charts['ui'] = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: data.map(x => x.type || 'Неизвестно'),
        datasets: [
          {
            label: 'New UI',
            data: data.map(x => x.clicks_new || 0),
            backgroundColor: 'rgba(54, 162, 235, 0.7)',
            borderColor: 'rgba(54, 162, 235, 1)',
            borderWidth: 1
          },
          {
            label: 'Old UI',
            data: data.map(x => x.clicks_old || 0),
            backgroundColor: 'rgba(255, 99, 132, 0.7)',
            borderColor: 'rgba(255, 99, 132, 1)',
            borderWidth: 1
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            labels: {
              color: '#e2e8f0'
            }
          }
        },
        scales: {
          x: {
            ticks: { color: '#e2e8f0' },
            grid: { color: '#334155' }
          },
          y: {
            beginAtZero: true,
            ticks: { color: '#e2e8f0' },
            grid: { color: '#334155' }
          }
        }
      }
    });
  } catch (error) {
    console.error('Ошибка создания UI графика:', error);
  }
}

function renderErrors(data) {
  console.log('Рендеринг графика ошибок с данными:', data);
  
  const canvas = document.getElementById('errorChart');
  if (!canvas) {
    console.error('Canvas errorChart не найден в DOM');
    return;
  }

  destroyChart('errors');

  if (!data || data.length === 0) {
    console.warn('Нет данных для графика ошибок');
    return;
  }

  const ctx = canvas.getContext('2d');
  
  // Группируем данные по версиям UI
  const versionMap = new Map();
  
  data.forEach(item => {
    const version = item.ui_version || 'Неизвестно';
    const errors = item.errors || 0;
    
    if (versionMap.has(version)) {
      versionMap.set(version, versionMap.get(version) + errors);
    } else {
      versionMap.set(version, errors);
    }
  });
  
  const labels = Array.from(versionMap.keys());
  const values = Array.from(versionMap.values());
  
  console.log('Сгруппированные данные ошибок:', { labels, values });
  
  try {
    charts['errors'] = new Chart(ctx, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [{
          label: 'Количество ошибок',
          data: values,
          borderColor: 'rgba(255, 99, 132, 1)',
          backgroundColor: 'rgba(255, 99, 132, 0.2)',
          tension: 0.1,
          fill: true
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            labels: {
              color: '#e2e8f0'
            }
          }
        },
        scales: {
          x: {
            ticks: { color: '#e2e8f0' },
            grid: { color: '#334155' }
          },
          y: {
            beginAtZero: true,
            ticks: { color: '#e2e8f0' },
            grid: { color: '#334155' }
          }
        }
      }
    });
  } catch (error) {
    console.error('Ошибка создания графика ошибок:', error);
  }
}

function renderTransactions(data) {
  console.log('Рендеринг графика транзакций с данными:', data);
  
  const canvas = document.getElementById('transactionChart');
  if (!canvas) {
    console.error('Canvas transactionChart не найден в DOM');
    return;
  }

  destroyChart('transactions');

  if (!data || data.length === 0) {
    console.warn('Нет данных для графика транзакций');
    return;
  }

  const ctx = canvas.getContext('2d');
  
  // Берём топ-10 категорий
  const topData = data.slice(0, 10);
  
  try {
    charts['transactions'] = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: topData.map(x => x.category || 'Неизвестно'),
        datasets: [{
          label: 'Средний чек (₽)',
          data: topData.map(x => x.avg_sum || 0),
          backgroundColor: 'rgba(75, 192, 192, 0.7)',
          borderColor: 'rgba(75, 192, 192, 1)',
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            labels: {
              color: '#e2e8f0'
            }
          },
          tooltip: {
            callbacks: {
              label: function(context) {
                const item = topData[context.dataIndex];
                return [
                  `Средний чек: ${item.avg_sum.toFixed(2)} ₽`,
                  `Количество: ${item.count}`
                ];
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
            grid: { color: '#334155' }
          },
          y: {
            beginAtZero: true,
            ticks: { 
              color: '#e2e8f0',
              callback: function(value) {
                return value + ' ₽';
              }
            },
            grid: { color: '#334155' }
          }
        }
      }
    });
  } catch (error) {
    console.error('Ошибка создания графика транзакций:', error);
  }
}

// Инициализация
function initEventListeners() {
  const filterElements = ['sex', 'min_age', 'max_age', 'payment'];
  
  filterElements.forEach(id => {
    const element = document.getElementById(id);
    if (element) {
      element.addEventListener('change', loadDashboard);
    }
  });

  const refreshBtn = document.getElementById('refreshBtn');
  if (refreshBtn) {
    refreshBtn.addEventListener('click', loadDashboard);
  }
}

// Запуск при загрузке
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    initEventListeners();
    loadDashboard();
  });
} else {
  initEventListeners();
  loadDashboard();
}