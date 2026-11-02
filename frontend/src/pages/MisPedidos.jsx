import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { usePedidos } from '../hooks/usePedidos';
import { useAuth } from '../context/AuthContext';
import { EstadoBadge } from '../components/EstadoBadge';
import { ProximaMudanza } from '../components/ProximaMudanza';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorAlert } from '../components/ErrorAlert';
import { dinero, fecha } from '../utils/formato';

const ESTADOS = ['', 'Pendiente', 'Confirmado', 'Finalizado', 'Anulado'];

// Por venir = activo y no vencido; se ordenan de la más cercana a la más lejana
const porVenir = (p) => (p.estado === 'Pendiente' || p.estado === 'Confirmado') && !p.vencido;
const cuando = (p) => p.fecha_servicio + p.hora_servicio;

function TarjetaPedido({ pedido: p, pasado }) {
  return (
    <div className="col">
      <Link to={`/pedidos/${p.id}`}
            className={`card-panel p-3 h-100 d-block text-decoration-none text-reset tarjeta-pedido ${pasado ? 'tarjeta-pasada' : ''}`}>
        <div className="d-flex justify-content-between align-items-start gap-2 mb-2">
          <span className="fw-bold">Pedido N° {p.id}</span>
          <EstadoBadge pedido={p} />
        </div>
        <p className="mb-1"><i className="bi bi-calendar-event me-1 text-marca" />{fecha(p.fecha_servicio)} {p.horario}</p>
        <p className="mb-1 small text-muted text-truncate"><i className="bi bi-geo-alt me-1" />{p.origen} → {p.destino}</p>
        <p className="mb-0 fw-semibold">{dinero(p.total)}</p>
      </Link>
    </div>
  );
}

function Grilla({ titulo, pedidos, pasado }) {
  if (!pedidos.length) return null;
  return (
    <section className="mb-4">
      {titulo && <h2 className="h6 fw-bold text-uppercase text-muted mb-3">{titulo}</h2>}
      <div className="row row-cols-1 row-cols-md-2 g-3">
        {pedidos.map((p) => <TarjetaPedido key={p.id} pedido={p} pasado={pasado} />)}
      </div>
    </section>
  );
}

export function MisPedidos() {
  const { puede } = useAuth();
  const location = useLocation();
  const [estado, setEstado] = useState('');
  const { pedidos, loading, error, refetch } = usePedidos(estado ? { estado } : {});

  const [proxima, ...otrasProximas] = pedidos.filter(porVenir).sort((a, b) => cuando(a).localeCompare(cuando(b)));
  const anteriores = pedidos.filter((p) => !porVenir(p)).sort((a, b) => cuando(b).localeCompare(cuando(a)));

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
          <button key={e} type="button" onClick={() => setEstado(e)} aria-pressed={estado === e}
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
        estado ? (
          // con un filtro, una sola lista
          <Grilla pedidos={[...(proxima ? [proxima] : []), ...otrasProximas, ...anteriores]} />
        ) : (
          <>
            {proxima && <ProximaMudanza pedido={proxima} />}
            <Grilla titulo="Próximas" pedidos={otrasProximas} />
            <Grilla titulo="Terminadas y anuladas" pedidos={anteriores} pasado />
          </>
        )
      )}
    </div>
  );
}
