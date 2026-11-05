import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useCarga } from '../../hooks/useCarga';
import { abmService } from '../../services/abmService';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import { ErrorAlert } from '../../components/ErrorAlert';

export const COLOR_ESTADO = {
  Disponible: 'estado-finalizado', 'En Viaje': 'estado-confirmado',
  'En Mantenimiento': 'estado-pendiente', 'Fuera de Servicio': 'estado-anulado',
};

export function Vehiculos() {
  const navigate = useNavigate();
  const location = useLocation();
  const { datos, loading, error, refetch } = useCarga((signal) => abmService.vehiculos(signal), []);

  if (loading) return <LoadingSpinner texto="Cargando la flota..." />;
  if (error) return <ErrorAlert message={error} onRetry={refetch} />;
  const conAviso = datos.vehiculos.filter((v) => v.mudanzas_sin_chofer);

  return (
    <div>
      <div className="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-4">
        <div>
          <h1 className="h3 fw-bold mb-1">Vehículos</h1>
          <p className="text-muted mb-0">La flota, su estado y su chofer habitual.</p>
        </div>
        <Link to="/vehiculos/nuevo" className="btn btn-primary"><i className="bi bi-plus-lg me-1" />Nuevo vehículo</Link>
      </div>
      {location.state?.aviso && <div className="alert alert-success">{location.state.aviso}</div>}
      {conAviso.length > 0 && (
        <div className="alert alert-warning">
          <i className="bi bi-person-x me-1" /><b>Mudanzas sin chofer:</b>{' '}
          {conAviso.map((v) => `${v.patente} (${v.mudanzas_sin_chofer})`).join(', ')}. Asignalo desde cada pedido.
        </div>
      )}
      <div className="card-panel p-0 overflow-hidden">
        <div className="table-responsive">
          <table className="table table-hover align-middle mb-0">
            <thead><tr><th>Patente</th><th>Tipo</th><th>Marca y modelo</th><th>Capacidad</th><th>Chofer habitual</th><th>Estado</th><th className="text-end">Pedidos</th></tr></thead>
            <tbody>
              {datos.vehiculos.map((v) => (
                <tr key={v.patente} className="fila-click" onClick={() => navigate(`/vehiculos/${v.patente}`)}>
                  <td className="fw-bold text-nowrap"><Link to={`/vehiculos/${v.patente}`} onClick={(e) => e.stopPropagation()}>{v.patente}</Link></td>
                  <td className="text-nowrap">{v.tipo_vehiculo}</td>
                  <td>{v.marca_modelo}</td>
                  <td className="text-nowrap small">{v.capacidad_kg.toLocaleString('es-AR')} kg · {v.capacidad_m3.toLocaleString('es-AR')} m³</td>
                  <td>{v.chofer || <span className="text-muted">—</span>}</td>
                  <td><span className={`estado ${COLOR_ESTADO[v.estado]}`}>{v.estado}</span></td>
                  <td className="text-end">{v.cant_pedidos}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
