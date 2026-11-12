import { Link } from 'react-router-dom';
import { useCarga } from '../../hooks/useCarga';
import { analisisService } from '../../services/analisisService';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import { ErrorAlert } from '../../components/ErrorAlert';

// Los reportes consolidados (M2) que puede ver quien entró: el de la flota pide REP_FINANZAS
export function Reportes() {
  const { datos, loading, error, refetch } = useCarga((signal) => analisisService.reportes(signal), []);
  if (loading) return <LoadingSpinner texto="Cargando los reportes..." />;
  if (error) return <ErrorAlert message={error} onRetry={refetch} />;
  return (
    <div>
      <h1 className="h3 fw-bold mb-1">Reportes</h1>
      <p className="text-muted mb-4">Cada reporte cruza varias tablas, se filtra por fechas y se descarga en PDF.</p>
      <div className="row g-3">
        {datos.reportes.map((r) => (
          <div key={r.clave} className="col-md-6 col-xl-4">
            <Link to={`/reportes/${r.clave}`} className="card-panel tarjeta-reporte d-block h-100 p-4 text-decoration-none">
              <span className={`icono-reporte ${r.color}`}><i className={`bi ${r.icono}`} /></span>
              <h2 className="h5 fw-bold mt-3 mb-1 text-body">{r.titulo}</h2>
              <p className="text-muted mb-2">{r.descripcion}</p>
              <p className="small mb-0"><b>Cruza:</b> {r.cruza}</p>
            </Link>
          </div>
        ))}
      </div>
    </div>
  );
}
