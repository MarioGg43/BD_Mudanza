import { useState } from 'react';
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom';
import { useCarga } from '../../hooks/useCarga';
import { abmService } from '../../services/abmService';
import { ConfirmarAccion } from '../../components/ConfirmarAccion';
import { EstadoBadge } from '../../components/EstadoBadge';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import { ErrorAlert } from '../../components/ErrorAlert';
import { fecha } from '../../utils/formato';
import { COLOR_ESTADO } from './Vehiculos';

function Agenda({ titulo, pedidos, vacio }) {
  return (
    <div className="card-panel p-3 mb-3">
      <h2 className="h6 fw-bold text-uppercase text-muted">{titulo}</h2>
      {pedidos.length === 0 ? <p className="text-muted small mb-0">{vacio}</p> : (
        <div className="table-responsive">
          <table className="table table-sm align-middle mb-0">
            <thead><tr><th>N°</th><th>Fecha</th><th>Cliente</th><th>Chofer</th><th>Estado</th></tr></thead>
            <tbody>
              {pedidos.map((p) => (
                <tr key={p.id}>
                  <td><Link to={`/pedidos/${p.id}`} className="fw-bold">{p.id}</Link></td>
                  <td className="small">{fecha(p.fecha_servicio)} {p.horario}</td>
                  <td>{p.cliente}</td>
                  <td>{p.chofer || <span className="text-danger small fw-semibold">sin chofer</span>}</td>
                  <td><EstadoBadge pedido={p} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export function VehiculoDetalle() {
  const { patente } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const [preguntar, setPreguntar] = useState(false);
  const { datos: v, loading, error, refetch } = useCarga((signal) => abmService.vehiculo(patente, signal), [patente]);

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorAlert message={error} onRetry={refetch} />;

  const darDeBaja = async () => {
    await abmService.bajaVehiculo(patente);
    setPreguntar(false);
    navigate('.', { replace: true, state: { aviso: `El vehículo ${patente} quedó fuera de servicio.` } });
    refetch();
  };

  return (
    <div className="mx-auto" style={{ maxWidth: 900 }}>
      <Link to="/vehiculos" className="small text-decoration-none"><i className="bi bi-arrow-left" /> Volver a vehículos</Link>
      <div className="d-flex flex-wrap justify-content-between align-items-center gap-2 mt-2 mb-4">
        <h1 className="h3 fw-bold mb-0">{v.patente} <span className={`estado ${COLOR_ESTADO[v.estado]}`}>{v.estado}</span></h1>
        <div className="d-flex gap-2">
          <Link to={`/vehiculos/${patente}/editar`} className="btn btn-outline-primary"><i className="bi bi-pencil me-1" />Editar</Link>
          {v.estado !== 'Fuera de Servicio' && (
            <button type="button" className="btn btn-outline-danger" onClick={() => setPreguntar(true)}><i className="bi bi-slash-circle me-1" />Dar de baja</button>
          )}
        </div>
      </div>
      {location.state?.aviso && <div className="alert alert-success">{location.state.aviso}</div>}

      <div className="card-panel p-3 mb-3">
        <div className="row g-2">
          <div className="col-sm-6"><b>Tipo:</b> {v.tipo_vehiculo} {v.recargo ? `(+${v.recargo} % al servicio)` : '(sin recargo)'}</div>
          <div className="col-sm-6"><b>Marca y modelo:</b> {v.marca_modelo}</div>
          <div className="col-sm-6"><b>Capacidad:</b> {v.capacidad_kg.toLocaleString('es-AR')} kg · {v.capacidad_m3.toLocaleString('es-AR')} m³</div>
          <div className="col-sm-6"><b>Año:</b> {v.anio || '—'} · <b>Km:</b> {v.kilometraje.toLocaleString('es-AR')}</div>
          <div className="col-sm-6"><b>Chofer habitual:</b> {v.chofer || '—'}</div>
          {v.observaciones && <div className="col-12"><b>Observaciones:</b> {v.observaciones}</div>}
        </div>
      </div>

      {v.agenda && (
        <>
          <Agenda titulo="Próximas mudanzas" pedidos={v.agenda.proximos} vacio="No tiene mudanzas por venir." />
          {v.agenda.para_cerrar.length > 0 && <Agenda titulo="Para cerrar (finalizar o anular)" pedidos={v.agenda.para_cerrar} />}
          <Agenda titulo="Historial" pedidos={v.agenda.historial} vacio="Todavía no hizo mudanzas." />
        </>
      )}

      {preguntar && (
        <ConfirmarAccion titulo={`Dar de baja el ${v.patente}`} boton="Dar de baja" claseBoton="btn-danger"
                         accion={darDeBaja} onHide={() => setPreguntar(false)}>
          <p className="mb-0">Queda <b>Fuera de Servicio</b> y no se ofrece en los pedidos nuevos. No se borra: conserva su historial
            y se reactiva editando el estado.</p>
        </ConfirmarAccion>
      )}
    </div>
  );
}
