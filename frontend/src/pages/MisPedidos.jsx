import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { usePedidos } from '../hooks/usePedidos';
import { useAuth } from '../context/AuthContext';
import { EstadoBadge } from '../components/EstadoBadge';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorAlert } from '../components/ErrorAlert';
import { dinero, fecha } from '../utils/formato';

const ESTADOS = ['', 'Pendiente', 'Confirmado', 'Finalizado', 'Anulado'];

export function MisPedidos() {
  const { puede } = useAuth();
  const location = useLocation();
  const [estado, setEstado] = useState('');
  const { pedidos, loading, error, refetch } = usePedidos(estado ? { estado } : {});

  return (
    <div>
      <div className="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-4">
        <div>
          <h1 className="h3 fw-bold mb-1">Mis pedidos</h1>
          <p className="text-muted mb-0">Tus mudanzas y en qué estado está cada una.</p>
        </div>
        {puede('PED_REGISTRAR') && (
          <Link to="/pedidos/nuevo" className="btn btn-primary"><i className="bi bi-plus-lg me-1" />Pedir mudanza</Link>
        )}
      </div>

      {location.state?.aviso && <div className="alert alert-success">{location.state.aviso}</div>}

      <div className="d-flex flex-wrap gap-2 mb-3" role="group" aria-label="Filtrar por estado">
        {ESTADOS.map((e) => (
          <button key={e} type="button" onClick={() => setEstado(e)}
                  className={`btn btn-sm rounded-pill ${estado === e ? 'btn-primary' : 'btn-outline-secondary'}`}>
            {e || 'Todos'}
          </button>
        ))}
      </div>

      {loading && <LoadingSpinner texto="Cargando tus pedidos..." />}
      {error && <ErrorAlert message={error} onRetry={refetch} />}

      {!loading && !error && pedidos.length === 0 && (
        <div className="card-panel p-5 text-center text-muted">
          {estado ? `No tenés pedidos en estado «${estado}».` : 'Todavía no pediste ninguna mudanza.'}
        </div>
      )}

      {!loading && !error && pedidos.length > 0 && (
        <div className="row row-cols-1 row-cols-md-2 g-3">
          {pedidos.map((p) => (
            <div key={p.id} className="col">
              <Link to={`/pedidos/${p.id}`} className="card-panel p-3 h-100 d-block text-decoration-none text-reset tarjeta-pedido">
                <div className="d-flex justify-content-between align-items-start gap-2 mb-2">
                  <span className="fw-bold">Pedido N° {p.id}</span>
                  <EstadoBadge pedido={p} />
                </div>
                <p className="mb-1"><i className="bi bi-calendar-event me-1 text-marca" />{fecha(p.fecha_servicio)} {p.horario}</p>
                <p className="mb-1 small text-muted text-truncate"><i className="bi bi-geo-alt me-1" />{p.origen} → {p.destino}</p>
                <p className="mb-0 fw-semibold">{dinero(p.total)}</p>
              </Link>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
