import { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  ArcElement, BarElement, CategoryScale, Chart as ChartJS, Legend, LinearScale, Tooltip,
} from 'chart.js';
import { Bar, Doughnut } from 'react-chartjs-2';
import { useCarga } from '../../hooks/useCarga';
import { analisisService } from '../../services/analisisService';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import { ErrorAlert } from '../../components/ErrorAlert';
import { EstadoBadge } from '../../components/EstadoBadge';

// Chart.js viene por partes: acá le decimos cuáles vamos a usar (barras, torta, leyenda...).
ChartJS.register(ArcElement, BarElement, CategoryScale, LinearScale, Legend, Tooltip);
ChartJS.defaults.font.family = "'Poppins', system-ui, sans-serif";
ChartJS.defaults.color = '#5E524B';

const AZUL = '#2a78d6', NARANJA = '#eb6834', GRIS = '#b9b7b0', GRILLA = '#ece7e2';
const ejes = (extra = {}) => ({
  x: { grid: { display: false }, ...extra.x },
  y: { beginAtZero: true, grid: { color: GRILLA }, border: { display: false }, ticks: { precision: 0 }, ...extra.y },
});

// Una tarjeta de indicador del mes, con cuánto cambió contra el mismo tramo del mes anterior
function Indicador({ color, icono, titulo, valor, variacion, sufijo = '%', detalle }) {
  const hay = variacion !== null && variacion !== undefined;
  return (
    <div className="col-6 col-xl-3">
      <div className={`kpi kpi-${color} h-100`}>
        <div className="d-flex justify-content-between align-items-start">
          <span className="kpi-titulo">{titulo}</span><i className={`bi ${icono} kpi-icono`} />
        </div>
        <div className="kpi-valor">{valor}</div>
        <div className="kpi-pie">
          {hay && <span className="kpi-variacion">{variacion >= 0 ? '▲' : '▼'} {Math.abs(variacion).toLocaleString('es-AR', { maximumFractionDigits: 1 })} {sufijo}</span>}
          {' '}{detalle}
        </div>
      </div>
    </div>
  );
}

/* Pantalla de inicio del administrador: lo de hoy, el mes contra el anterior y cuatro gráficos.
   Los datos los calcula Django (reportes/tablero.py), igual que en la pantalla de Django. */
export function Tablero() {
  const [periodo, setPeriodo] = useState('30');
  // Django ya manda los números calculados; nosotros solo se los pasamos a los gráficos.
  // Si cambia el período, se vuelve a pedir todo y los gráficos se redibujan solos.
  const { datos, loading, error, refetch } = useCarga((signal) => analisisService.tablero(periodo, signal), [periodo]);
  if (loading) return <LoadingSpinner texto="Armando el tablero..." />;
  if (error) return <ErrorAlert message={error} onRetry={refetch} />;
  const { hoy_resumen: h, mes, variacion: v, graficos: g } = datos;
  const totalServicios = g.servicios.valores.reduce((a, b) => a + b, 0);

  return (
    <div>
      <div className="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-4">
        <div>
          <h1 className="h3 fw-bold mb-1">{datos.saludo}</h1>
          <p className="text-muted mb-0">
            Hoy: <b>{h.mudanzas_hoy}</b> mudanza{h.mudanzas_hoy !== 1 && 's'} · <b>{h.en_curso}</b> en curso ·{' '}
            <Link to="/pedidos">{h.por_confirmar} por confirmar</Link> · {h.disponibles} de {h.flota} vehículos disponibles
          </p>
        </div>
      </div>

      <div className="row g-3 mb-4">
        <Indicador color="naranja" icono="bi-truck" titulo="Mudanzas del mes" valor={mes.mudanzas} variacion={v.mudanzas} detalle="vs. el mismo tramo del mes anterior" />
        <Indicador color="verde" icono="bi-cash-stack" titulo="Facturación del mes" valor={mes.facturacion} variacion={v.facturacion} detalle="· mudanzas finalizadas" />
        <Indicador color="azul" icono="bi-receipt" titulo="Ticket promedio" valor={mes.ticket} variacion={v.ticket} detalle="· por mudanza finalizada" />
        <Indicador color="rojo" icono="bi-x-circle" titulo="Cancelaciones del mes" valor={`${mes.anulados} (${mes.cancelacion.toLocaleString('es-AR')} %)`} variacion={v.cancelacion} sufijo="pts" detalle="vs. el mes anterior" />
      </div>

      <div className="card-panel p-3 mb-4">
        <div className="d-flex flex-wrap justify-content-between align-items-start gap-2 mb-2">
          <div>
            <h2 className="h6 fw-bold mb-0">Mudanzas por día</h2>
            <p className="small text-muted mb-0">{datos.total_periodo} en el período y lo que viene en los próximos 7 días</p>
          </div>
          <select className="form-select form-select-sm w-auto" value={periodo} onChange={(e) => setPeriodo(e.target.value)} aria-label="Período">
            {datos.periodos.map((p) => <option key={p.value} value={p.value}>{p.label}</option>)}
          </select>
        </div>
        <div className="grafico-alto">
          <Bar
            aria-label="Mudanzas por día: finalizadas, sin finalizar y programadas"
            data={{ labels: g.dias.etiquetas, datasets: [
              { label: 'Finalizadas', data: g.dias.finalizadas, backgroundColor: AZUL, borderRadius: 4, maxBarThickness: 22 },
              { label: 'Sin finalizar', data: g.dias.sin_finalizar, backgroundColor: GRIS, borderRadius: 4, maxBarThickness: 22 },
              { label: 'Programadas (próximos 7 días)', data: g.dias.programadas, backgroundColor: NARANJA, borderRadius: 4, maxBarThickness: 22 },
            ] }}
            options={{ maintainAspectRatio: false, interaction: { mode: 'index', intersect: false },
              plugins: { legend: { position: 'top', align: 'end', labels: { usePointStyle: true, boxWidth: 8 } } },
              scales: ejes({ x: { stacked: true, ticks: { maxRotation: 0, autoSkip: true, maxTicksLimit: 12 } }, y: { stacked: true } }) }}
          />
        </div>
      </div>

      <div className="row g-4 mb-4">
        <div className="col-lg-4">
          <div className="card-panel p-3 h-100">
            <h2 className="h6 fw-bold mb-0">Mudanzas por servicio</h2>
            <p className="small text-muted">Servicio principal, en el período</p>
            {totalServicios ? (
              <div className="grafico-medio">
                <Doughnut aria-label="Mudanzas por servicio"
                  data={{ labels: g.servicios.etiquetas, datasets: [{ data: g.servicios.valores, backgroundColor: g.servicios.colores, borderWidth: 2 }] }}
                  options={{ maintainAspectRatio: false, cutout: '62%', plugins: { legend: { position: 'bottom', labels: { usePointStyle: true, boxWidth: 8 } },
                    tooltip: { callbacks: { label: (c) => ` ${c.label}: ${c.parsed} (${(c.parsed / totalServicios * 100).toLocaleString('es-AR', { maximumFractionDigits: 1 })} %)` } } } }}
                />
              </div>
            ) : <p className="text-muted small">Sin mudanzas en el período.</p>}
          </div>
        </div>
        <div className="col-lg-4">
          <div className="card-panel p-3 h-100">
            <h2 className="h6 fw-bold mb-0">Horarios pico</h2>
            <p className="small text-muted">A qué hora empiezan las mudanzas</p>
            <div className="grafico-medio">
              <Bar aria-label="Horarios pico"
                data={{ labels: g.horas.etiquetas, datasets: [{ label: 'Mudanzas', data: g.horas.valores, backgroundColor: AZUL, borderRadius: 4 }] }}
                options={{ maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: ejes() }} />
            </div>
          </div>
        </div>
        <div className="col-lg-4">
          <div className="card-panel p-3 h-100">
            <h2 className="h6 fw-bold mb-0">Vehículos más usados</h2>
            <p className="small text-muted">Horas de uso en el período</p>
            <div className="grafico-medio">
              <Bar aria-label="Vehículos más usados"
                data={{ labels: g.vehiculos.etiquetas, datasets: [{ label: 'Horas de uso', data: g.vehiculos.valores, backgroundColor: AZUL, borderRadius: 4, maxBarThickness: 22 }] }}
                options={{ maintainAspectRatio: false, indexAxis: 'y', plugins: { legend: { display: false },
                  tooltip: { callbacks: { label: (c) => ` ${c.parsed.x.toLocaleString('es-AR')} h de uso` } } },
                  scales: { x: { beginAtZero: true, grid: { color: GRILLA } }, y: { grid: { display: false } } } }} />
            </div>
          </div>
        </div>
      </div>

      <div className="card-panel p-0 overflow-hidden">
        <h2 className="h6 fw-bold m-3">Próximas mudanzas</h2>
        <div className="table-responsive">
          <table className="table table-hover align-middle mb-0">
            <thead><tr><th>Fecha</th><th>Cliente</th><th>Recorrido</th><th>Vehículo</th><th>Chofer</th><th>Estado</th></tr></thead>
            <tbody>
              {datos.proximas.map((p) => (
                <tr key={p.id}>
                  <td className="text-nowrap"><Link to={`/pedidos/${p.id}`}>{p.fecha} · {p.hora}</Link></td>
                  <td>{p.cliente}</td>
                  <td className="small">{p.origen} → {p.destino}</td>
                  <td>{p.vehiculo}</td>
                  <td>{p.chofer || <span className="text-danger small">Sin chofer</span>}</td>
                  <td><EstadoBadge pedido={p} /></td>
                </tr>
              ))}
              {!datos.proximas.length && <tr><td colSpan="6" className="text-center text-muted py-3">No hay mudanzas por venir.</td></tr>}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
