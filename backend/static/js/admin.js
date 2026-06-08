document.addEventListener('DOMContentLoaded', function(){
  try {
    // Prepare sales data
    const labels = DAILY_SALES.map(d => d.date);
    const data = DAILY_SALES.map(d => parseFloat(d.sales || 0));

    const salesCtx = document.getElementById('salesChart');
    if (salesCtx) {
      new Chart(salesCtx.getContext('2d'), {
        type: 'line',
        data: {
          labels: labels,
          datasets: [{
            label: 'Daily Sales (₹)',
            data: data,
            borderColor: '#d46a2f',
            backgroundColor: 'rgba(212,106,47,0.12)',
            tension: 0.3,
            pointRadius: 4,
            pointBackgroundColor: '#ff6b5f',
            fill: true,
          }]
        },
        options: {
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            x: { grid: { display: false } },
            y: { ticks: { callback: v => '₹' + v } }
          }
        }
      });
    }

    // Top products bar chart
    const prodCtx = document.getElementById('productsChart');
    if (prodCtx && Array.isArray(TOP_PRODUCTS)) {
      const prodLabels = TOP_PRODUCTS.map(p => p[0]);
      const prodData = TOP_PRODUCTS.map(p => p[1]);
      new Chart(prodCtx.getContext('2d'), {
        type: 'bar',
        data: {
          labels: prodLabels,
          datasets: [{
            label: 'Units sold',
            data: prodData,
            backgroundColor: '#2B2F6B',
          }]
        },
        options: {
          indexAxis: 'y',
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: { x: { grid: { display: false } } }
        }
      });
    }
  } catch (e) {
    console.error('Admin chart init failed', e);
  }
});
