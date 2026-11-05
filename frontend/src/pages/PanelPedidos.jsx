import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { usePedidos } from '../hooks/usePedidos';
import { useCarga } from '../hooks/useCarga';
import { adminService } from '../services/adminService';
import { EstadoBadge } from '../components/EstadoBadge';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorAlert } from '../components/ErrorAlert';
import { dinero, fecha } from '../utils/formato';

// Los avisos que calcula Django (reglas.AVISOS), con su color y qué significan
const AVISOS = [
  { nombre: 'Atrasada', icono: 'bi-alarm', clase: 'aviso-rojo', ayuda: 'Ya debían terminar y otra mudanza las espera' },
  { nombre: 'Para finalizar', icono: 'bi-flag', clase: 'aviso-naranja', ayuda: 'Ya empezaron y nadie las finalizó' },
  { nombre: 'Por confirmar', icono: 'bi-hourglass-split', clase: 'aviso-amarillo', ayuda: 'Pendientes de los próximos 2 días' },
  { nombre: 'Sin chofer', icono: 'bi-person-x', clase: 'aviso-rojo', ayuda: 'Confirmadas por venir sin chofer' },
  { nombre: 'Vencido', icono: 'bi-calendar-x', clase: 'aviso-gris', ayuda: 'Pendientes cuya fecha ya pasó' },
];

const VACIO = { estado: '', desde: '', hasta: '', cliente: '', vehiculo: '' };

export function PanelPedidos() {
  const navigate = useNavigate();
  const [filtros, setFiltros] = useState(VACIO);
  // solo se mandan los filtros con valor
  const activos = Object.fromEntries(Object.entries(filtros).filter(([, v]) => v));
  const { pedidos, avisos, loading, error, refetch } = usePedidos(activos);
  const { datos: opciones } = useCarga((signal) => adminService.opciones(signal), []);

  const cambiar = (e) => setFiltros({ ...filtros, [e.target.name]: e.target.value });
  const verAviso = (nombre) => setFiltros({ ...VACIO, estado: filtros.estado === nombre ? '' : nombre });

  return (
    <div>
      <div className="mb-4">
        <h1 className="h3 fw-bold mb-1">Pedidos</h1>
        <p className="text-muted mb-0">Todas las mudanzas. Tocá un aviso para ver solo esos pedidos.</p>
      </div>

      {/* ---------- avisos ---------- */}
      <div className="row row-cols-2 row-cols-md-3 row-cols-lg-5 g-2 mb-4">
        {AVISOS.map((a) => {
          const cantidad = avisos[a.nombre] ?? 0;
          return (
            <div key={a.nombre} className="col">
              <button type="button" onClick={() => verAviso(a.nombre)} title={a.ayuda}
                      aria-pressed={filtros.estado === a.nombre}
                      className={`tarjeta-aviso ${cantidad ? a.clase : 'aviso-cero'} ${filtros.estado === a.nombre ? 'aviso-activo' : ''}`}>
                <span className="d-flex justify-content-between align-items-center">
                  <i className={`bi ${a.icono} fs-5`} />
                  <span className="fs-3 fw-bold">{cantidad}</span>
                </span>
                <span className="fw-semibold small">{a.nombre === 'Vencido' ? 'Vencidos' : a.nombre === 'Atrasada' ? 'Atrasadas' : a.nombre}</span>
              </button>
            </div>
          );
        })}
      </div>

      {/* ---------- filtros ---------- */}
      <div className="card-panel p-3 mb-3">
        <div className="row g-2 align-items-end">
          <div className="col-6 col-md-3 col-lg-2">
            <label htmlFor="estado" className="form-label small mb-1">Estado</label>
            <select id="estado" name="estado" className="form-select form-select-sm" value={filtros.estado} onChange={cambiar}>
              <option value="">Todos</option>
              {opciones?.estados.map((e) => <option key={e} value={e}>{e}</option>)}
              {opciones && <optgroup label="Avisos">{opciones.avisos.map((a) => <option key={a} value={a}>{a}</option>)}</optgroup>}
            </select>
          </div>
          <div className="col-6 col-md-3 col-lg-2">
            <label htmlFor="desde" className="form-label small mb-1">Desde</label>
            <input id="desde" name="desde" type="date" className="form-control form-control-sm" value={filtros.desde} onChange={cambiar} />
          </div>
          <div className="col-6 col-md-3 col-lg-2">
            <label htmlFor="hasta" className="form-label small mb-1">Hasta</label>
            <input id="hasta" name="hasta" type="date" className="form-control form-control-sm" value={filtros.hasta} onChange={cambiar} />
          </div>
          <div className="col-6 col-md-3 col-lg-3">
            <label htmlFor="cliente" className="form-label small mb-1">Cliente</label>
            <select id="cliente" name="cliente" className="form-select form-select-sm" value={filtros.cliente} onChange={cambiar}>
              <option value="">Todos</option>
              {opciones?.clientes.map((c) => <option key={c.id} value={c.id}>{c.nombre}</option>)}
            </select>
          </div>
          <div className="col-6 col-md-3 col-lg-2">
            <label htmlFor="vehiculo" className="form-label small mb-1">Vehículo</label>
            <select id="vehiculo" name="vehiculo" className="form-select form-select-sm" value={filtros.vehiculo} onChange={cambiar}>
              <option value="">Todos</option>
              {opciones?.vehiculos.map((v) => <option key={v} value={v}>{v}</option>)}
            </select>
          </div>
          <div className="col-6 col-md-3 col-lg-1">
            <button type="button" className="btn btn-sm btn-outline-secondary w-100" onClick={() => setFiltros(VACIO)}>Limpiar</button>
          </div>
        </div>
      </div>

      {loading && <LoadingSpinner texto="Cargando pedidos..." />}
      {error && <ErrorAlert message={error} onRetry={refetch} />}

      {!loading && !error && (
        <>
          <p className="small text-muted">{pedidos.length} pedido{pedidos.length === 1 ? '' : 's'}</p>
          {pedidos.length === 0 ? (
            <div className="card-panel p-5 text-center text-muted">No hay pedidos con esos filtros.</div>
          ) : (
            <div className="card-panel p-0 overflow-hidden">
              <div className="table-responsive">
                <table className="table table-hover align-middle mb-0 tabla-pedidos">
                  <thead>
                    <tr><th>N°</th><th>Mudanza</th><th>Cliente</th><th>Recorrido</th><th>Vehículo</th><th>Estado</th><th className="text-end">Total</th></tr>
                  </thead>
                  <tbody>
                    {pedidos.map((p) => {
                      const activo = p.estado === 'Pendiente' || p.estado === 'Confirmado';
                      return (
                        <tr key={p.id} onClick={() => navigate(`/pedidos/${p.id}`)} className="fila-click">
                          <td><Link to={`/pedidos/${p.id}`} className="fw-bold" onClick={(e) => e.stopPropagation()}>{p.id}</Link></td>
                          <td className="text-nowrap">{fecha(p.fecha_servicio)}<br /><span className="small text-muted">{p.hora_servicio} h</span></td>
                          <td>{p.cliente}</td>
                          <td className="small text-muted recorrido">{p.origen} → {p.destino}</td>
                          <td className="text-nowrap small">{p.vehiculo}</td>
                          <td>
                            <div className="d-flex flex-wrap gap-1">
                              <EstadoBadge pedido={p} />
                              {p.atrasada && <span className="estado estado-atrasada">Atrasada</span>}
                              {activo && !p.vencido && !p.tiene_chofer && <span className="estado estado-sin-chofer">Sin chofer</span>}
                            </div>
                          </td>
                          <td className="text-end text-nowrap fw-semibold">{dinero(p.total)}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
