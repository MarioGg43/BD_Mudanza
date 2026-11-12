import { useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { useCarga } from '../../hooks/useCarga';
import { analisisService } from '../../services/analisisService';
import { Campo } from '../../components/Campo';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import { ErrorAlert } from '../../components/ErrorAlert';

const NUMEROS = ['pesos', 'entero', 'horas', 'minutos', 'porcentaje'];
const hoy = () => new Date().toLocaleDateString('sv-SE');  // AAAA-MM-DD en la hora local
const primeroDeEnero = () => `${new Date().getFullYear()}-01-01`;

/* Un reporte consolidado: rango de fechas (obligatorio) más su filtro propio, la grilla con los
   totales, el resumen por motivo (en el de cambios) y el PDF. Los números llegan ya formateados. */
export function Reporte() {
  const { clave } = useParams();
  const { datos: lista } = useCarga((signal) => analisisService.reportes(signal), []);
  const info = lista?.reportes.find((r) => r.clave === clave);
  const [filtros, setFiltros] = useState({ desde: primeroDeEnero(), hasta: hoy() });
  const [aplicados, setAplicados] = useState(filtros);
  const [pagina, setPagina] = useState(1);
  const [bajando, setBajando] = useState(false);
  const activos = Object.fromEntries(Object.entries(aplicados).filter(([, v]) => v));
  const { datos, loading, error, refetch } = useCarga(
    (signal) => analisisService.reporte(clave, { ...activos, pagina }, signal), [clave, JSON.stringify(activos), pagina]);

  const cambiar = (e) => setFiltros({ ...filtros, [e.target.name]: e.target.value });
  const [errores, setErrores] = useState({});
  const filtrar = (e) => {
    e.preventDefault();
    if (filtros.desde && filtros.hasta && filtros.hasta < filtros.desde) {
      setErrores({ hasta: 'La fecha «Hasta» no puede ser anterior a «Desde».' });
      return;
    }
    setErrores({});
    setAplicados(filtros);
    setPagina(1);
  };
  const pdf = async () => {
    setBajando(true);
    try { await analisisService.pdfReporte(clave, datos?.titulo || 'Reporte', activos); } finally { setBajando(false); }
  };

  return (
    <div>
      <p className="mb-2"><Link to="/reportes" className="small"><i className="bi bi-arrow-left me-1" />Reportes</Link></p>
      <div className="d-flex flex-wrap justify-content-between align-items-start gap-2 mb-3">
        <div>
          <h1 className="h3 fw-bold mb-1">{info?.titulo || datos?.titulo || 'Reporte'}</h1>
          <p className="text-muted mb-0">{info?.descripcion}</p>
        </div>
        <button type="button" className="btn btn-outline-secondary" onClick={pdf} disabled={bajando || !datos}>
          <i className="bi bi-file-earmark-pdf me-1" />{bajando ? 'Generando...' : 'Descargar PDF'}
        </button>
      </div>

      <form className="card-panel p-3 mb-3" onSubmit={filtrar}>
        <div className="row g-2 align-items-end">
          <Campo col="col-6 col-md-3" chico tipo="date" label="Desde" name="desde" value={filtros.desde} onChange={cambiar} error={errores.desde} />
          <Campo col="col-6 col-md-3" chico tipo="date" label="Hasta" name="hasta" value={filtros.hasta} min={filtros.desde} onChange={cambiar} error={errores.hasta} />
          {info && (
            <Campo col="col-12 col-md-3" chico label={info.filtro.etiqueta} name={info.filtro.nombre}
              opciones={info.filtro.opciones} value={filtros[info.filtro.nombre] || ''} onChange={cambiar} />
          )}
          <div className="col-12 col-md-3"><button className="btn btn-primary btn-sm w-100"><i className="bi bi-funnel me-1" />Filtrar</button></div>
        </div>
      </form>

      {loading && <LoadingSpinner texto="Calculando el reporte..." />}
      {error && <ErrorAlert message={error} onRetry={refetch} />}
      {datos && !loading && (
        <>
          {datos.resumen.length > 0 && (
            <div className="card-panel p-3 mb-3">
              <h2 className="h6 fw-bold">Resumen por motivo</h2>
              <table className="table table-sm mb-0">
                <thead><tr><th>Tipo</th><th>Motivo</th><th className="text-end">Cantidad</th><th className="text-end">%</th></tr></thead>
                <tbody>{datos.resumen.map((r, i) => <tr key={i}><td>{r.tipo}</td><td>{r.motivo}</td><td className="text-end">{r.cantidad}</td><td className="text-end">{r.porcentaje}</td></tr>)}</tbody>
              </table>
            </div>
          )}
          <p className="small text-muted mb-2">{datos.total} fila{datos.total !== 1 && 's'} · {datos.filtros_usados.map(([e, v]) => `${e}: ${v}`).join(' · ')}</p>
          <div className="card-panel p-0 overflow-hidden">
            <div className="table-responsive">
              <table className="table table-hover align-middle mb-0">
                <thead><tr>{datos.columnas.map((c) => <th key={c.clave} className={NUMEROS.includes(c.tipo) ? 'text-end' : ''}>{c.titulo}</th>)}</tr></thead>
                <tbody>
                  {datos.filas.map((f, i) => (
                    <tr key={i}>{f.celdas.map((v, j) => (
                      <td key={j} className={NUMEROS.includes(datos.columnas[j].tipo) ? 'text-end text-nowrap' : ''}>
                        {datos.columnas[j].clave === 'pedido' && f.id_pedido ? <Link to={`/pedidos/${f.id_pedido}`}>{v}</Link> : v}
                      </td>))}
                    </tr>
                  ))}
                  {!datos.filas.length && <tr><td colSpan={datos.columnas.length} className="text-center text-muted py-3">No hay datos para esos filtros.</td></tr>}
                </tbody>
                {datos.totales.length > 0 && (
                  <tfoot><tr className="fw-bold">{datos.totales.map((v, j) => (
                    <td key={j} className={NUMEROS.includes(datos.columnas[j].tipo) ? 'text-end text-nowrap' : ''}>{j === 0 ? `Total: ${v}` : v}</td>))}
                  </tr></tfoot>
                )}
              </table>
            </div>
          </div>
          {datos.paginas > 1 && (
            <nav className="d-flex justify-content-between align-items-center mt-2 small">
              <button type="button" className="btn btn-link btn-sm" disabled={pagina <= 1} onClick={() => setPagina(pagina - 1)}>← Anterior</button>
              <span className="text-muted">Página {datos.pagina} de {datos.paginas}</span>
              <button type="button" className="btn btn-link btn-sm" disabled={pagina >= datos.paginas} onClick={() => setPagina(pagina + 1)}>Siguiente →</button>
            </nav>
          )}
          <p className="small text-muted mt-3">{datos.nota}</p>
        </>
      )}
    </div>
  );
}
