import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useCarga } from '../../hooks/useCarga';
import { useAuth } from '../../context/AuthContext';
import { analisisService } from '../../services/analisisService';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import { ErrorAlert } from '../../components/ErrorAlert';

const ICONO = {
  'Pedido sin confirmar': 'bi-hourglass-split', 'Mudanza atrasada': 'bi-alarm', 'Cliente con cancelaciones': 'bi-x-octagon',
  'Mudanza confirmada': 'bi-check-circle', 'Mudanza reprogramada': 'bi-calendar-event', 'Stock bajo': 'bi-box-seam',
};

// avisa a la barra de arriba que cambió la cantidad sin leer (la campanita)
const avisarCampanita = () => window.dispatchEvent(new Event('notificaciones-cambiaron'));

/* La bandeja de notificaciones (M3): las del perfil de quien entró y las suyas propias. */
export function Bandeja() {
  const navigate = useNavigate();
  const { puede } = useAuth();
  const [ver, setVer] = useState('sin_leer');
  const [pagina, setPagina] = useState(1);
  const { datos, loading, error, refetch } = useCarga(
    (signal) => analisisService.notificaciones({ ver, pagina }, signal), [ver, pagina]);

  const abrir = async (n) => {
    const r = await analisisService.leerNotificacion(n.id);
    avisarCampanita();
    if (r.enlace) navigate(r.enlace); else refetch();
  };
  const leerTodas = async () => {
    await analisisService.leerTodas();
    avisarCampanita();
    refetch();
  };

  return (
    <div>
      <div className="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-3">
        <div>
          <h1 className="h3 fw-bold mb-1">Notificaciones</h1>
          <p className="text-muted mb-0">Los avisos que generan las reglas automáticas del sistema.</p>
        </div>
        <div className="d-flex gap-2">
          {puede('CFG_GESTIONAR') && <Link to="/notificaciones/umbrales" className="btn btn-outline-secondary"><i className="bi bi-sliders me-1" />Umbrales</Link>}
          {datos?.sin_leer > 0 && <button type="button" className="btn btn-primary" onClick={leerTodas}><i className="bi bi-check2-all me-1" />Marcar todas como leídas</button>}
        </div>
      </div>
      <div className="btn-group mb-3" role="group" aria-label="Qué notificaciones ver">
        {[['sin_leer', 'Sin leer'], ['todas', 'Todas']].map(([v, t]) => (
          <button key={v} type="button" className={`btn btn-sm ${ver === v ? 'btn-dark' : 'btn-outline-secondary'}`}
            onClick={() => { setVer(v); setPagina(1); }}>{t}{v === 'sin_leer' && datos ? ` (${datos.sin_leer})` : ''}</button>
        ))}
      </div>
      {loading && <LoadingSpinner texto="Cargando las notificaciones..." />}
      {error && <ErrorAlert message={error} onRetry={refetch} />}
      {datos && !loading && (
        <div className="d-flex flex-column gap-2">
          {datos.notificaciones.map((n) => (
            <div key={n.id} className={`card-panel p-3 d-flex gap-3 align-items-start notificacion ${n.leida ? 'leida' : ''}`}>
              <span className="icono-notificacion"><i className={`bi ${ICONO[n.tipo] || 'bi-bell'}`} /></span>
              <div className="flex-grow-1">
                <div className="d-flex flex-wrap justify-content-between gap-2">
                  <b>{n.tipo}</b><span className="small text-muted">{n.fecha}</span>
                </div>
                <p className="mb-1">{n.mensaje}</p>
                {n.correo && <p className="small text-muted mb-1"><i className="bi bi-envelope me-1" />{n.correo}</p>}
                <button type="button" className="btn btn-link btn-sm p-0" onClick={() => abrir(n)}>
                  {n.enlace ? 'Ver' : n.leida ? '' : 'Marcar como leída'}
                </button>
              </div>
            </div>
          ))}
          {!datos.notificaciones.length && (
            <div className="card-panel p-4 text-center text-muted">{ver === 'sin_leer' ? 'No tenés notificaciones sin leer.' : 'Todavía no hay notificaciones.'}</div>
          )}
          {datos.paginas > 1 && (
            <nav className="d-flex justify-content-between align-items-center small">
              <button type="button" className="btn btn-link btn-sm" disabled={pagina <= 1} onClick={() => setPagina(pagina - 1)}>← Más nuevas</button>
              <span className="text-muted">Página {datos.pagina} de {datos.paginas}</span>
              <button type="button" className="btn btn-link btn-sm" disabled={pagina >= datos.paginas} onClick={() => setPagina(pagina + 1)}>Más viejas →</button>
            </nav>
          )}
        </div>
      )}
    </div>
  );
}
