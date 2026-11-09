// Gráficos del tablero del administrador (reportes/tablero.html) con Chart.js.
// Los datos los arma Django (reportes/tablero.py) y llegan en <script id="datos-tablero">.
(function () {
  const datos = JSON.parse(document.getElementById('datos-tablero').textContent);
  const AZUL = '#2a78d6', NARANJA = '#eb6834', TINTA = '#231A15', TINTA_2 = '#5E524B', GRILLA = '#ece7e2';
  const numero = (n) => n.toLocaleString('es-AR', { maximumFractionDigits: 1 });

  Chart.defaults.font.family = "'Poppins', system-ui, sans-serif";
  Chart.defaults.font.size = 12;
  Chart.defaults.color = TINTA_2;
  Chart.defaults.plugins.legend.labels.usePointStyle = true;
  Chart.defaults.plugins.legend.labels.boxWidth = 8;
  Chart.defaults.plugins.tooltip.backgroundColor = '#2a170e';
  Chart.defaults.plugins.tooltip.padding = 10;
  Chart.defaults.plugins.tooltip.cornerRadius = 8;
  Chart.defaults.maintainAspectRatio = false;
  const ejes = (extra = {}) => ({
    x: { grid: { display: false }, border: { color: '#d8d1cb' }, ...extra.x },
    y: { beginAtZero: true, grid: { color: GRILLA }, border: { display: false }, ticks: { precision: 0 }, ...extra.y },
  });

  // 1. Mudanzas por día: las hechas y las que vienen (una sola escala: las dos son mudanzas)
  new Chart(document.getElementById('graficoDias'), {
    type: 'bar',
    data: {
      labels: datos.dias.etiquetas,
      datasets: [
        { label: 'Hechas o del día', data: datos.dias.hechas, backgroundColor: AZUL, borderRadius: 4, maxBarThickness: 22 },
        { label: 'Programadas (próximos 7 días)', data: datos.dias.programadas, backgroundColor: NARANJA, borderRadius: 4, maxBarThickness: 22 },
      ],
    },
    options: {
      interaction: { mode: 'index', intersect: false },
      plugins: { legend: { position: 'top', align: 'end' } },
      scales: ejes({ x: { stacked: true, ticks: { maxRotation: 0, autoSkip: true, maxTicksLimit: 12 } }, y: { stacked: true } }),
    },
  });

  // 2. Mudanzas por servicio (donut), con la leyenda y los números al lado (no solo el color)
  const totalServicios = datos.servicios.valores.reduce((a, b) => a + b, 0);
  new Chart(document.getElementById('graficoServicios'), {
    type: 'doughnut',
    data: {
      labels: datos.servicios.etiquetas,
      datasets: [{ data: datos.servicios.valores, backgroundColor: datos.servicios.colores, borderColor: '#fff', borderWidth: 2 }],
    },
    options: {
      cutout: '62%',
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: (c) => ` ${c.label}: ${c.parsed} (${numero(c.parsed / totalServicios * 100)} %)` } },
      },
    },
  });
  document.querySelectorAll('.leyenda-servicios li').forEach((li) => {
    const i = Number(li.dataset.indice), n = datos.servicios.valores[i];
    li.innerHTML = '<span class="punto"></span><span class="nombre"></span><b></b>';
    li.querySelector('.punto').style.background = datos.servicios.colores[i];
    li.querySelector('.nombre').textContent = datos.servicios.etiquetas[i];
    li.querySelector('b').textContent = `${numero(n / totalServicios * 100)} % · ${n}`;
  });

  // 3. Horarios pico
  new Chart(document.getElementById('graficoHoras'), {
    type: 'bar',
    data: { labels: datos.horas.etiquetas, datasets: [{ label: 'Mudanzas', data: datos.horas.valores, backgroundColor: AZUL, borderRadius: 4 }] },
    options: { plugins: { legend: { display: false } }, scales: ejes({ x: { ticks: { maxRotation: 0, autoSkip: true } } }) },
  });

  // 4. Vehículos más usados (barras horizontales: los nombres se leen enteros)
  new Chart(document.getElementById('graficoVehiculos'), {
    type: 'bar',
    data: { labels: datos.vehiculos.etiquetas, datasets: [{ label: 'Horas de uso', data: datos.vehiculos.valores, backgroundColor: AZUL, borderRadius: 4, maxBarThickness: 22 }] },
    options: {
      indexAxis: 'y',
      plugins: { legend: { display: false }, tooltip: { callbacks: { label: (c) => ` ${numero(c.parsed.x)} h de uso` } } },
      scales: {
        x: { beginAtZero: true, grid: { color: GRILLA }, border: { display: false }, ticks: { callback: (v) => `${numero(v)} h` } },
        y: { grid: { display: false }, border: { color: '#d8d1cb' }, ticks: { color: TINTA } },
      },
    },
  });
})();
