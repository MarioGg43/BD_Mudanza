import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useState } from 'react';
import { useCarga } from '../../hooks/useCarga';
import { materialesService } from '../../services/materialesService';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import { ErrorAlert } from '../../components/ErrorAlert';

// Una fila de movimiento: el signo dice qué le hizo al stock (Consumo y Pérdida no lo cambian)
export function FilaMovimiento({ mv, conMaterial }) {
  return (
    <tr>
      <td className="small text-nowrap">{mv.fecha}</td>
      {conMaterial && <td><Link to={`/materiales/${mv.id_material}`}>{mv.material}</Link></td>}
      <td><span className={`mov mov-${mv.tipo.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()}`}>{mv.tipo}</span>
        {mv.observacion && <span className="small text-muted"> · {mv.observacion}</span>}</td>
      <td className={`text-end text-nowrap fw-semibold ${mv.cambia_stock ? '' : 'text-muted fw-normal'}`}>{mv.efecto}</td>
      <td>{mv.pedido ? <Link to={`/pedidos/${mv.pedido}`}>N° {mv.pedido}</Link> : '—'}</td>
      <td className="small">{mv.quien}</td>
    </tr>
  );
}

function Resumen({ icono, color, numero, texto, detalle, onClick }) {
  return (
    <div className="col-6 col-xl-3">
      <button type="button" className={`aviso-tarjeta w-100 text-start ${numero ? color : 'apagada'}`} onClick={onClick} disabled={!onClick || !numero}>
        <span className="aviso-icono"><i className={`bi ${icono}`} /></span>
        <span className="aviso-texto"><b>{numero}</b><span>{texto}</span><small>{detalle}</small></span>
      </button>
    </div>
  );
}

/* Lo que se lleva a las mudanzas, con su stock. Sale con «Empezamos» y vuelve (o se descuenta lo
   gastado) con «Terminamos». */
export function Materiales() {
  const navigate = useNavigate();
  const location = useLocation();
  const [soloBajos, setSoloBajos] = useState(false);
  const { datos, loading, error, refetch } = useCarga((signal) => materialesService.lista(signal), []);
  if (loading) return <LoadingSpinner texto="Cargando los materiales..." />;
  if (error) return <ErrorAlert message={error} onRetry={refetch} />;
  const r = datos.resumen;
  const lista = soloBajos ? datos.materiales.filter((m) => m.bajo_minimo) : datos.materiales;

  return (
    <div>
      <div className="d-flex flex-wrap justify-content-between align-items-start gap-2 mb-4">
        <div>
          <h1 className="h3 fw-bold mb-1">Materiales</h1>
          <p className="text-muted mb-0">Lo que se lleva a las mudanzas. Sale del stock con «Empezamos» y vuelve (o se descuenta lo gastado) con «Terminamos».</p>
        </div>
        <Link to="/materiales/nuevo" className="btn btn-primary"><i className="bi bi-plus-lg me-1" />Nuevo material</Link>
      </div>
      {location.state?.aviso && <div className="alert alert-success">{location.state.aviso}</div>}

      <div className="row g-3 mb-4">
        <Resumen icono="bi-boxes" color="azul" numero={r.activos} texto="Materiales activos" detalle="Los que se pueden usar en los servicios" />
        <Resumen icono="bi-exclamation-octagon" color="rojo" numero={r.bajo_minimo} texto="Bajo el mínimo" detalle="Conviene reponerlos" onClick={() => setSoloBajos(true)} />
        <Resumen icono="bi-truck" color="violeta" numero={r.afuera} texto="Afuera ahora" detalle="Reutilizables en mudanzas en curso" />
        <Resumen icono="bi-arrow-left-right" color="verde" numero={r.movimientos_mes} texto="Movimientos del mes" detalle="Ingresos, salidas, devoluciones…" />
      </div>
      {soloBajos && <p className="small"><i className="bi bi-funnel me-1" />Mostrando solo los que están bajo el mínimo · <button type="button" className="btn btn-link btn-sm p-0" onClick={() => setSoloBajos(false)}>Ver todos</button></p>}

      <div className="card-panel p-0 overflow-hidden mb-4">
        <div className="table-responsive">
          <table className="table table-hover align-middle mb-0">
            <thead><tr><th>Material</th><th>Tipo</th><th style={{ minWidth: 170 }}>Stock</th><th className="text-end">Afuera</th><th className="text-end">Mínimo</th><th className="text-end">Servicios</th><th>Estado</th></tr></thead>
            <tbody>
              {lista.map((m) => (
                <tr key={m.id} className={`fila-click ${m.activo ? '' : 'text-muted'}`} onClick={() => navigate(`/materiales/${m.id}`)}>
                  <td className="fw-semibold"><Link to={`/materiales/${m.id}`} onClick={(e) => e.stopPropagation()}>{m.nombre}</Link></td>
                  <td className="small text-nowrap">{m.reutilizable ? <><i className="bi bi-arrow-repeat me-1" />Reutilizable</> : <><i className="bi bi-box2 me-1" />Se gasta</>}</td>
                  <td>
                    <b className={m.bajo_minimo ? 'text-danger' : ''}>{m.stock}</b> <span className="small text-muted">{m.unidad}</span>
                    <div className={`barra-stock ${m.bajo_minimo ? 'baja' : ''}`}><span style={{ width: `${m.minimo ? Math.min(100, Math.round(m.stock * 100 / (m.minimo * 2))) : 100}%` }} /></div>
                  </td>
                  <td className="text-end">{m.reutilizable ? m.en_uso : '—'}</td>
                  <td className="text-end">{m.minimo}</td>
                  <td className="text-end">{m.servicios}</td>
                  <td>{!m.activo ? <span className="estado estado-anulado">Dado de baja</span>
                    : m.bajo_minimo ? <span className="estado estado-atrasada">Reponer</span>
                    : <span className="estado estado-finalizado">Bien</span>}</td>
                </tr>
              ))}
              {!lista.length && <tr><td colSpan="7" className="text-center text-muted py-4">{soloBajos ? 'Ningún material está bajo el mínimo.' : 'Todavía no hay materiales cargados.'}</td></tr>}
            </tbody>
          </table>
        </div>
      </div>

      <h2 className="h6 fw-bold mb-2"><i className="bi bi-clock-history me-1" />Últimos movimientos</h2>
      <div className="card-panel p-0 overflow-hidden">
        <div className="table-responsive">
          <table className="table table-sm align-middle mb-0">
            <thead><tr><th>Fecha</th><th>Material</th><th>Movimiento</th><th className="text-end">Stock</th><th>Mudanza</th><th>Quién</th></tr></thead>
            <tbody>
              {datos.ultimos.map((mv) => <FilaMovimiento key={mv.id} mv={mv} conMaterial />)}
              {!datos.ultimos.length && <tr><td colSpan="6" className="text-center text-muted py-3">Sin movimientos todavía.</td></tr>}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
