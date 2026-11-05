import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useCarga } from '../../hooks/useCarga';
import { portalService } from '../../services/portalService';
import { ConfirmarAccion } from '../../components/ConfirmarAccion';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import { ErrorAlert } from '../../components/ErrorAlert';
import { diaSemana, diasHasta, fecha } from '../../utils/formato';

function Estado({ m }) {
  if (m.en_curso) return <span className="estado estado-finalizado">En curso desde las {m.inicio_real}</span>;
  if (m.estado === 'Confirmado') return <span className="estado estado-confirmado">Confirmada</span>;
  return <span className="estado estado-pendiente">A confirmar</span>;
}

function cuando(iso) {
  const dias = diasHasta(iso);
  if (dias === 0) return 'Hoy';
  if (dias === 1) return 'Mañana';
  return dias > 1 ? `En ${dias} días` : 'Ya pasó';
}

// Una mudanza del portal: datos, botones del chofer y qué hay que llevar (sin precios)
function TarjetaMudanza({ m, onEmpezar, onTerminar }) {
  const [verObjetos, setVerObjetos] = useState(false);
  return (
    <div className={`card-panel p-3 p-md-4 ${m.en_curso ? 'mudanza-en-curso' : ''}`}>
      <div className="d-flex flex-wrap justify-content-between align-items-start gap-2 mb-2">
        <div>
          <p className="small text-muted mb-0">{cuando(m.fecha_servicio)} · pedido N° {m.id}</p>
          <h2 className="h5 fw-bold mb-0">{diaSemana(m.fecha_servicio)} {fecha(m.fecha_servicio)} · {m.hora_servicio} a {m.hasta}</h2>
        </div>
        <Estado m={m} />
      </div>

      {/* lo que puede hacer el chofer */}
      {m.soy_chofer && m.estado === 'Confirmado' && (
        <div className="caja-acciones p-3 mb-3">
          {m.en_curso ? (
            <>
              <div className="d-flex flex-wrap gap-2 mb-2">
                <button type="button" className="btn btn-primary fw-bold" onClick={() => onTerminar(m)}><i className="bi bi-flag me-1" />Terminamos</button>
                <Link to={`/portal/${m.id}/relevamiento`} className="btn btn-outline-secondary fw-bold"><i className="bi bi-clipboard-check me-1" />Relevamiento</Link>
              </div>
              <p className="small text-muted mb-0">Empezaron a las {m.inicio_real}. Fin estimado: {m.fin_esperado}. Si hay más cosas de las declaradas, cargalo en «Relevamiento».</p>
            </>
          ) : m.puede_empezar ? (
            <div className="d-flex flex-wrap align-items-center gap-2">
              <button type="button" className="btn btn-primary fw-bold" onClick={() => onEmpezar(m)}><i className="bi bi-play-fill me-1" />Empezamos</button>
              {m.empieza_tarde && <span className="estado estado-atrasada"><i className="bi bi-clock me-1" />Atrasada: tenía que empezar a las {m.hora_servicio}</span>}
            </div>
          ) : m.ya_paso ? (
            <p className="small text-danger mb-0"><i className="bi bi-exclamation-triangle me-1" />Esta mudanza ya pasó. Si la hicieron, avisale al administrador para que la finalice.</p>
          ) : (
            <p className="small text-muted mb-0"><i className="bi bi-info-circle me-1" />El día de la mudanza vas a poder marcar «Empezamos» y «Terminamos».</p>
          )}
        </div>
      )}

      <div className="row g-2 small">
        <div className="col-md-6"><i className="bi bi-geo-alt me-1 text-marca" /><b>Desde:</b> {m.origen}</div>
        <div className="col-md-6"><i className="bi bi-flag me-1 text-marca" /><b>Hasta:</b> {m.destino}</div>
        <div className="col-md-6"><i className="bi bi-truck me-1 text-marca" /><b>Vehículo:</b> {m.vehiculo}</div>
        <div className="col-md-6"><i className="bi bi-list-check me-1 text-marca" /><b>Servicios:</b> {m.servicios.join(', ')}</div>
        <div className="col-md-6"><i className="bi bi-people me-1 text-marca" /><b>Equipo:</b> {m.equipo.join(', ')}</div>
        <div className="col-md-6"><i className="bi bi-person me-1 text-marca" /><b>Cliente:</b> {m.cliente}
          {m.telefono && <> · <a href={`tel:${m.telefono.replace(/\D/g, '')}`}>{m.telefono}</a></>}</div>
      </div>

      <button type="button" className="btn btn-link px-0 mt-2" onClick={() => setVerObjetos(!verObjetos)} aria-expanded={verObjetos}>
        <i className={`bi ${verObjetos ? 'bi-chevron-up' : 'bi-chevron-down'} me-1`} />Qué hay que llevar ({m.inventario.length})
      </button>
      {verObjetos && (
        <ul className="list-group list-group-flush small">
          {m.inventario.map((i, k) => (
            <li key={k} className="list-group-item px-0">
              <b>{i.cantidad} × {i.nombre}</b>{i.fragil && <span className="badge text-bg-warning ms-1">frágil</span>}
              {i.observacion && <span className="text-muted"> — {i.observacion}</span>}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export function Portal() {
  const { usuario } = useAuth();
  const location = useLocation();
  const { datos, loading, error, refetch } = useCarga((signal) => portalService.mudanzas(signal), []);
  const [preguntar, setPreguntar] = useState(null); // { tipo: 'empezar' | 'terminar', m }
  const [aviso, setAviso] = useState(location.state?.aviso);

  if (loading) return <LoadingSpinner texto="Cargando tus mudanzas..." />;
  if (error) return <ErrorAlert message={error} onRetry={refetch} />;

  const marcar = async () => {
    const { tipo, m } = preguntar;
    if (tipo === 'empezar') {
      const r = await portalService.empezar(m.id);
      setAviso(`Mudanza N° ${m.id} en curso desde las ${r.hora}. Cuando terminen, tocá «Terminamos».`);
    } else {
      await portalService.terminar(m.id);
      setAviso(`Mudanza N° ${m.id} terminada y finalizada. ¡Buen trabajo!`);
    }
    setPreguntar(null);
    refetch();
  };

  return (
    <div className="mx-auto" style={{ maxWidth: 900 }}>
      <h1 className="h3 fw-bold mb-1">Hola, {usuario.nombre}</h1>
      <p className="text-muted mb-4">Tus mudanzas asignadas. El día de cada una, el chofer marca cuándo empiezan y cuándo terminan.</p>
      {aviso && <div className="alert alert-success">{aviso}</div>}

      {datos.mudanzas.length === 0 ? (
        <div className="card-panel p-5 text-center">
          <i className="bi bi-truck fs-1 text-marca" />
          <p className="fw-semibold mt-2 mb-1">No tenés mudanzas asignadas por ahora</p>
          <p className="text-muted mb-0">Cuando el administrador te asigne a una, la vas a ver acá con la fecha, las direcciones y lo que hay que llevar.</p>
        </div>
      ) : (
        <div className="d-flex flex-column gap-3 mb-4">
          {datos.mudanzas.map((m) => (
            <TarjetaMudanza key={m.id} m={m} onEmpezar={(x) => setPreguntar({ tipo: 'empezar', m: x })}
                            onTerminar={(x) => setPreguntar({ tipo: 'terminar', m: x })} />
          ))}
        </div>
      )}

      {datos.vehiculos.length > 0 && (
        <section className="mt-4">
          <h2 className="h6 fw-bold text-uppercase text-muted mb-2">Vehículos que manejás habitualmente</h2>
          <div className="row row-cols-1 row-cols-sm-2 g-2">
            {datos.vehiculos.map((v) => (
              <div key={v.patente} className="col">
                <div className="card-panel p-3 d-flex align-items-center gap-3">
                  <i className="bi bi-truck fs-3 text-marca" />
                  <div><b>{v.patente}</b> · {v.modelo}<br /><span className="small text-muted">{v.tipo}{v.anio ? ` · ${v.anio}` : ''} · {v.estado}</span></div>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {preguntar && (
        <ConfirmarAccion titulo={preguntar.tipo === 'empezar' ? '¿Empiezan la mudanza?' : '¿Terminaron la mudanza?'}
                         boton={preguntar.tipo === 'empezar' ? 'Empezamos' : 'Terminamos'}
                         accion={marcar} onHide={() => setPreguntar(null)}>
          <p className="mb-0">
            {preguntar.tipo === 'empezar'
              ? `Se guarda la hora de inicio real del pedido N° ${preguntar.m.id}. Después podés cargar el relevamiento.`
              : `Se guarda la hora de fin y el pedido N° ${preguntar.m.id} queda finalizado. Si encontraron más cosas, cargá antes el relevamiento.`}
          </p>
        </ConfirmarAccion>
      )}
    </div>
  );
}
