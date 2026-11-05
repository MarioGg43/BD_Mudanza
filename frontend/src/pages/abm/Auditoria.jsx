import { Fragment, useState } from 'react';
import { Link } from 'react-router-dom';
import { useCarga } from '../../hooks/useCarga';
import { abmService } from '../../services/abmService';
import { Campo, opcionesDe } from '../../components/Campo';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import { ErrorAlert } from '../../components/ErrorAlert';

const VACIO = { desde: '', hasta: '', tabla: '', accion: '', usuario: '', registro: '' };
const COLOR = { 'Anulación': 'estado-atrasada', 'Eliminación': 'estado-atrasada', Baja: 'estado-atrasada',
                'Reactivación': 'estado-finalizado', 'Modificación': 'estado-confirmado' };

/* El log de auditoría: cada modificación, anulación, baja o borrado, con la frase de qué pasó y
   cada campo en Antes / Después. Las frases y los valores legibles los arma Django. */
export function Auditoria() {
  const [filtros, setFiltros] = useState(VACIO);
  const [pagina, setPagina] = useState(1);
  const [bajando, setBajando] = useState(false);
  const [errorPdf, setErrorPdf] = useState(null);
  const activos = Object.fromEntries(Object.entries(filtros).filter(([, v]) => v));
  const clave = JSON.stringify(activos);

  const { datos: opciones } = useCarga((signal) => abmService.opcionesAuditoria(signal), []);
  const { datos, loading, error, refetch } = useCarga(
    (signal) => abmService.auditoria({ ...activos, pagina }, signal), [clave, pagina]);

  const cambiar = (e) => {
    setFiltros({ ...filtros, [e.target.name]: e.target.value });
    setPagina(1);
  };
  const descargar = async () => {
    setBajando(true);
    setErrorPdf(null);
    try {
      await abmService.pdfAuditoria(activos);
    } catch (err) {
      setErrorPdf(err.message);
    } finally {
      setBajando(false);
    }
  };
  const campo = (name) => ({ name, value: filtros[name], onChange: cambiar, error: datos?.errores?.[name], chico: true });

  return (
    <div>
      <div className="d-flex flex-wrap justify-content-between align-items-start gap-2 mb-4">
        <div>
          <h1 className="h3 fw-bold mb-1">Log de auditoría</h1>
          <p className="text-muted mb-0">Cada modificación, anulación, baja o borrado de un registro, con los valores de antes y de después, la fecha y hora y quién lo hizo.</p>
        </div>
        <button type="button" className="btn btn-outline-secondary fw-bold" onClick={descargar} disabled={bajando}>
          <i className="bi bi-file-earmark-pdf me-1" />{bajando ? 'Generando...' : 'Descargar PDF'}
        </button>
      </div>
      {errorPdf && <div className="alert alert-danger">{errorPdf}</div>}

      <div className="card-panel p-3 mb-3">
        <div className="row g-2 align-items-end">
          <Campo label="Desde" col="col-6 col-md-4 col-lg-2" tipo="date" {...campo('desde')} />
          <Campo label="Hasta" col="col-6 col-md-4 col-lg-2" tipo="date" {...campo('hasta')} />
          <Campo label="Tabla" col="col-6 col-md-4 col-lg-2" {...campo('tabla')}
                 vacio="Todas" opciones={opciones?.tablas ?? []} />
          <Campo label="Acción" col="col-6 col-md-4 col-lg-2" {...campo('accion')}
                 vacio="Todas" opciones={opcionesDe(opciones?.acciones ?? [])} />
          <Campo label="Usuario" col="col-6 col-md-4 col-lg-2" {...campo('usuario')}
                 vacio="Todos" opciones={opciones?.usuarios ?? []} />
          <Campo label="Registro" col="col-6 col-md-3 col-lg-1" {...campo('registro')} maxLength={60} placeholder="N°" />
          <div className="col-12 col-md-1">
            <button type="button" className="btn btn-sm btn-outline-secondary w-100" onClick={() => { setFiltros(VACIO); setPagina(1); }}>Limpiar</button>
          </div>
        </div>
      </div>

      {loading && <LoadingSpinner texto="Cargando el log..." />}
      {error && <ErrorAlert message={error} onRetry={refetch} />}
      {datos && (
        <>
          <p className="small text-muted">{datos.total} registro{datos.total === 1 ? '' : 's'}</p>
          <div className="card-panel p-0 overflow-hidden">
            <div className="table-responsive">
              <table className="table align-middle mb-0 small tabla-auditoria">
                <thead className="table-light">
                  <tr><th style={{ width: '9rem' }}>Fecha y hora</th><th style={{ width: '7rem' }}>Acción</th><th>Qué pasó</th><th>Antes</th><th>Después</th></tr>
                </thead>
                <tbody>
                  {datos.registros.length === 0 && (
                    <tr><td colSpan={5} className="text-center text-muted py-4">No hay registros con esos filtros.</td></tr>
                  )}
                  {datos.registros.map((log) => (
                    <Fragment key={log.id}>
                      <tr className="fila-log">
                        <td rowSpan={log.cambios.length + 1} className="text-nowrap align-top">{log.fecha}<br /><span className="text-muted">{log.hora}</span></td>
                        <td rowSpan={log.cambios.length + 1} className="align-top"><span className={`estado ${COLOR[log.accion] || 'estado-confirmado'}`}>{log.accion}</span></td>
                        <td colSpan={3}>
                          <span className="fw-bold">{log.frase}</span>
                          {log.link && <Link to={log.link} className="ms-2 small text-decoration-none">Ver <i className="bi bi-arrow-right" /></Link>}
                          {log.detalle && <div className="text-muted">{log.detalle}</div>}
                        </td>
                      </tr>
                      {log.cambios.map(([campo, antes, despues]) => (
                        <tr key={campo}>
                          <td className="ps-4 text-muted">{campo}</td>
                          <td className="text-danger">{antes}</td>
                          <td className="text-success">{log.accion === 'Eliminación' ? <span className="text-muted">(se quitó)</span> : despues}</td>
                        </tr>
                      ))}
                    </Fragment>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          {datos.paginas > 1 && (
            <nav className="d-flex justify-content-center align-items-center gap-2 mt-3" aria-label="Páginas">
              <button type="button" className="btn btn-sm btn-outline-secondary" disabled={datos.pagina <= 1} onClick={() => setPagina(datos.pagina - 1)}>Anterior</button>
              <span className="small">Página {datos.pagina} de {datos.paginas}</span>
              <button type="button" className="btn btn-sm btn-outline-secondary" disabled={datos.pagina >= datos.paginas} onClick={() => setPagina(datos.pagina + 1)}>Siguiente</button>
            </nav>
          )}
        </>
      )}
    </div>
  );
}
