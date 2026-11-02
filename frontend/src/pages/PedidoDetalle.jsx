import { useState } from 'react';
import { Link, useLocation, useParams } from 'react-router-dom';
import { usePedido } from '../hooks/usePedido';
import { pedidoService } from '../services/pedidoService';
import { EstadoBadge } from '../components/EstadoBadge';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorAlert } from '../components/ErrorAlert';
import { dinero, diaSemana, fecha } from '../utils/formato';

export function PedidoDetalle() {
  const { id } = useParams();
  const location = useLocation();
  const { pedido: p, loading, error, refetch } = usePedido(id);
  const [bajando, setBajando] = useState(false);
  const [errorPdf, setErrorPdf] = useState(null);

  if (loading) return <LoadingSpinner texto="Cargando el pedido..." />;
  if (error) return <ErrorAlert message={error} onRetry={refetch} />;

  const descargar = async () => {
    setBajando(true);
    setErrorPdf(null);
    try {
      await pedidoService.descargarComprobante(p.id);
    } catch (err) {
      setErrorPdf(err.message);
    } finally {
      setBajando(false);
    }
  };

  const activo = p.estado === 'Pendiente' || p.estado === 'Confirmado';
  const c = p.ultimo_cambio;

  return (
    <div className="mx-auto" style={{ maxWidth: 900 }}>
      <Link to="/pedidos" className="small text-decoration-none"><i className="bi bi-arrow-left" /> Volver a mis pedidos</Link>
      <div className="d-flex flex-wrap justify-content-between align-items-center gap-2 mt-2 mb-4">
        <h1 className="h3 fw-bold mb-0">Pedido N° {p.id} <EstadoBadge pedido={p} /></h1>
        <div className="d-flex flex-wrap gap-2">
          {p.puede_comprobante && (
            <button type="button" className="btn btn-outline-secondary" onClick={descargar} disabled={bajando}>
              <i className="bi bi-file-earmark-pdf me-1" />{bajando ? 'Generando...' : 'Comprobante PDF'}
            </button>
          )}
          {p.puede_cambiar && (
            <>
              <Link to={`/pedidos/${p.id}/modificar`} className="btn btn-outline-primary"><i className="bi bi-pencil-square me-1" />Modificar</Link>
              <Link to={`/pedidos/${p.id}/cancelar`} className="btn btn-outline-danger"><i className="bi bi-x-circle me-1" />Cancelar mudanza</Link>
            </>
          )}
        </div>
      </div>

      {location.state?.aviso && <div className="alert alert-success">{location.state.aviso}</div>}
      {errorPdf && <div className="alert alert-danger">{errorPdf}</div>}

      {c && p.estado !== 'Anulado' && (
        <div className="alert alert-info" role="status">
          <i className="bi bi-calendar2-week me-1" />
          {c.nuevo && <span className="badge text-bg-primary me-1">Nuevo</span>}
          <b>Tu mudanza cambió de horario.</b> Era el {fecha(c.fecha_anterior)} a las {c.hora_anterior}; ahora es el{' '}
          <b>{diaSemana(c.fecha_nueva).toLowerCase()} {fecha(c.fecha_nueva)} a las {c.hora_nueva}</b>. Motivo: {c.motivo}.
          {c.vehiculo_nuevo && ` Va el vehículo ${c.vehiculo_nuevo}.`}
        </div>
      )}
      {p.es_mio && !p.puede_cambiar && activo && (
        <p className="small text-muted"><i className="bi bi-info-circle me-1" />Faltan menos de 24 horas para la mudanza: para cambiarla o cancelarla, comunicate con la empresa.</p>
      )}
      {p.vencido && (
        <div className="alert alert-warning">
          <i className="bi bi-exclamation-triangle me-1" /><b>Pedido vencido:</b> la mudanza era el {fecha(p.fecha_servicio)} a las {p.hora_servicio} y nadie lo confirmó. Si todavía la necesitás, pedí una fecha nueva.
        </div>
      )}
      {p.anulacion && (
        <div className="alert alert-secondary">
          <strong>Anulado</strong> el {fecha(p.anulacion.fecha)} {p.anulacion.fecha.slice(11)} por {p.anulacion.por}. Motivo: {p.anulacion.motivo}
        </div>
      )}

      <div className="row g-3 mb-3">
        <div className="col-md-6">
          <div className="card-panel p-3 h-100">
            <h2 className="h6 fw-bold text-uppercase text-muted">Mudanza</h2>
            <p className="mb-1"><strong>Fecha:</strong> {diaSemana(p.fecha_servicio)} {fecha(p.fecha_servicio)} {p.horario}</p>
            {p.inicio_real && (
              <p className="mb-1"><strong>Real:</strong> empezó {fecha(p.inicio_real)} {p.inicio_real.slice(11)}
                {p.fin_real ? ` · terminó ${p.fin_real.slice(11)}` : <span className="text-success fw-semibold"> · en curso</span>}</p>
            )}
            <p className="mb-1"><strong>Desde:</strong> {p.origen}</p>
            <p className="mb-1"><strong>Hasta:</strong> {p.destino}</p>
            <p className="mb-0"><strong>Vehículo:</strong> {p.vehiculo} · {p.vehiculo_tipo} · {p.vehiculo_modelo}</p>
          </div>
        </div>
        <div className="col-md-6">
          <div className="card-panel p-3 h-100">
            <h2 className="h6 fw-bold text-uppercase text-muted">Personal</h2>
            <p className="mb-1"><strong>Chofer:</strong> {p.chofer || <span className="text-muted">todavía sin asignar</span>}</p>
            <p className="mb-0 text-muted small">Pedido registrado el {fecha(p.fecha_pedido)}. {p.estado === 'Pendiente' && 'La empresa lo revisa y lo confirma.'}</p>
          </div>
        </div>
      </div>

      <div className="card-panel p-3 mb-3">
        <h2 className="h6 fw-bold text-uppercase text-muted">Servicios</h2>
        <div className="table-responsive">
          <table className="table mb-0">
            <thead><tr><th>Servicio</th><th className="text-end">Precio</th></tr></thead>
            <tbody>
              {p.servicios.map((s) => (
                <tr key={s.id}><td>{s.nombre}{s.adicional && <i> (adicional)</i>}</td><td className="text-end">{dinero(s.subtotal)}</td></tr>
              ))}
              {p.recargo > 0 && (
                <tr><td>Recargo del relevamiento <i>({p.motivo_recargo})</i></td><td className="text-end">{dinero(p.recargo)}</td></tr>
              )}
            </tbody>
            <tfoot><tr><th className="text-end">Total</th><th className="text-end">{dinero(p.total)}</th></tr></tfoot>
          </table>
        </div>
      </div>

      <div className="card-panel p-3">
        <h2 className="h6 fw-bold text-uppercase text-muted">Qué se lleva</h2>
        <div className="table-responsive">
          <table className="table mb-0">
            <thead><tr><th>Objeto</th><th className="text-end">Cantidad</th><th>Frágil</th><th>Observación</th></tr></thead>
            <tbody>
              {p.inventario.map((i, k) => (
                <tr key={k}>
                  <td>{i.nombre}</td>
                  <td className="text-end">{i.cantidad}{i.declarada != null && i.declarada !== i.cantidad && <i> (declaraste {i.declarada})</i>}</td>
                  <td>{i.fragil ? 'Sí' : 'No'}</td>
                  <td>{i.observacion || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
