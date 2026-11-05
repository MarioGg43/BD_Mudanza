import { Link } from 'react-router-dom';

/* Las partes del detalle del pedido que ve solo el administrador (vienen en pedido.gestion). */

// Mudanza atrasada: esta ya debía terminar y otra la espera, o la anterior a esta se atrasó
export function AvisosAtraso({ pedido: p }) {
  const g = p.gestion;
  return (
    <>
      {g.atrasada && (
        <div className="alert alert-danger" role="alert">
          <i className="bi bi-alarm me-1" /><b>Mudanza atrasada:</b> tenía que terminar a las {g.atrasada.fin} (aprox.) y nadie la finalizó.{' '}
          {g.atrasada.ya_empezo ? 'El ' : `A las ${g.atrasada.hora} empieza el `}
          <Link to={`/pedidos/${g.atrasada.id}`} className="alert-link">pedido N° {g.atrasada.id}</Link>
          {g.atrasada.ya_empezo && ' ya tendría que haber empezado'} con {g.atrasada.comparte}.
          Si ya terminó, finalizala; si no, reprogramá el pedido N° {g.atrasada.id} y avisale al cliente.
          <div className="mt-2">
            <Link to={`/pedidos/${g.atrasada.id}/reprogramar?motivo=Demora en una mudanza anterior`} className="btn btn-sm btn-danger">
              <i className="bi bi-calendar2-week me-1" />Reprogramar el pedido N° {g.atrasada.id}
            </Link>
          </div>
        </div>
      )}
      {g.anterior && (
        <div className="alert alert-warning" role="alert">
          <i className="bi bi-alarm me-1" /><b>Puede empezar tarde:</b> la mudanza anterior con {g.anterior.comparte}{' '}
          (<Link to={`/pedidos/${g.anterior.id}`} className="alert-link">pedido N° {g.anterior.id}</Link>) tenía que
          terminar a las {g.anterior.fin} y nadie la finalizó.
          <div className="mt-2">
            <Link to={`/pedidos/${p.id}/reprogramar?motivo=Demora en una mudanza anterior`} className="btn btn-sm btn-outline-dark">
              <i className="bi bi-calendar2-week me-1" />Reprogramar este pedido
            </Link>
          </div>
        </div>
      )}
    </>
  );
}

export function TarjetaCliente({ cliente }) {
  return (
    <div className="card-panel p-3 h-100">
      <h2 className="h6 fw-bold text-uppercase text-muted">Cliente</h2>
      <p className="mb-1 fw-semibold">{cliente.nombre} <span className="text-muted fw-normal">· DNI {cliente.dni}</span></p>
      <p className="mb-1"><i className="bi bi-envelope me-1 text-marca" /><a href={`mailto:${cliente.correo}`}>{cliente.correo}</a></p>
      <p className="mb-0"><i className="bi bi-telephone me-1 text-marca" />{cliente.telefono || <span className="text-muted">sin teléfono cargado</span>}</p>
    </div>
  );
}

export function TarjetaPersonal({ pedido: p }) {
  const g = p.gestion;
  return (
    <div className="card-panel p-3 h-100">
      <div className="d-flex justify-content-between align-items-center gap-2 mb-2">
        <h2 className="h6 fw-bold text-uppercase text-muted mb-0">Personal</h2>
        {g.puede_asignar && (
          <Link to={`/pedidos/${p.id}/personal`} className="btn btn-sm btn-outline-secondary">
            <i className="bi bi-person-gear me-1" />{g.chofer ? 'Cambiar' : 'Asignar'}
          </Link>
        )}
      </div>
      {g.chofer ? (
        <>
          <p className="mb-1"><strong>Chofer:</strong> {g.chofer.nombre}</p>
          <p className="mb-0"><strong>Ayudantes:</strong> {g.ayudantes.length ? g.ayudantes.map((a) => a.nombre).join(', ') : 'ninguno'}</p>
        </>
      ) : (
        <p className={`mb-0 ${p.estado === 'Confirmado' ? 'text-danger fw-semibold' : 'text-muted'}`}>
          Sin personal asignado.{p.estado === 'Pendiente' && g.puede_asignar && ' Hace falta el chofer para confirmar.'}
        </p>
      )}
    </div>
  );
}

export function HistorialCambios({ pedido: p }) {
  const g = p.gestion;
  if (!g.reprogramaciones.length) return null;
  return (
    <div className="card-panel p-3 mb-3">
      <div className="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-2">
        <h2 className="h6 fw-bold text-uppercase text-muted mb-0"><i className="bi bi-clock-history me-1" />Cambios de horario</h2>
        {g.whatsapp ? (
          <a href={g.whatsapp} target="_blank" rel="noopener noreferrer" className="btn btn-sm btn-whatsapp">
            <i className="bi bi-whatsapp me-1" />Avisar al cliente por WhatsApp
          </a>
        ) : p.estado !== 'Anulado' && (
          <span className="small text-muted">El cliente no tiene teléfono cargado para avisarle por WhatsApp.</span>
        )}
      </div>
      <ul className="list-unstyled mb-0 small">
        {g.reprogramaciones.map((r, n) => (
          <li key={n} className={n < g.reprogramaciones.length - 1 ? 'border-bottom pb-2 mb-2' : ''}>
            <b>{r.antes}</b> → <b>{r.despues}</b>{r.vehiculo && ` · vehículo ${r.vehiculo}`}
            <br />Motivo: {r.motivo} · {r.por}, {r.cuando} ·{' '}
            {r.visto ? <span className="text-success">el cliente ya lo vio</span> : <span className="text-muted">el cliente todavía no lo vio</span>}
          </li>
        ))}
      </ul>
    </div>
  );
}
