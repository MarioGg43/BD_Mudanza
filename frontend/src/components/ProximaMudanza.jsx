import { Link } from 'react-router-dom';
import { dinero, diaSemana, diasHasta, fecha } from '../utils/formato';

function cuandoEs(p) {
  const dias = diasHasta(p.fecha_servicio);
  if (p.en_curso || dias < 0) return 'En curso';
  if (dias === 0) return 'Es hoy';
  if (dias === 1) return 'Es mañana';
  return `Faltan ${dias} días`;
}

// La tarjeta grande de arriba de «Mis pedidos»: la mudanza que viene
export function ProximaMudanza({ pedido: p }) {
  return (
    <Link to={`/pedidos/${p.id}`} className="heroe-marca proxima-mudanza p-4 mb-4 d-block text-decoration-none text-white">
      <div className="d-flex flex-wrap justify-content-between align-items-center gap-2">
        <span className="etiqueta-blanca"><i className="bi bi-calendar-event" />Tu próxima mudanza · N° {p.id}</span>
        <span className="etiqueta-blanca">{p.estado === 'Confirmado' ? 'Confirmada' : 'Esperando confirmación'}</span>
      </div>
      <div className="d-flex flex-wrap justify-content-between align-items-end gap-3 mt-3">
        <div>
          <p className="display-6 fw-bold mb-1">{cuandoEs(p)}</p>
          <p className="fs-5 mb-1">{diaSemana(p.fecha_servicio)} {fecha(p.fecha_servicio)} · {p.horario}</p>
          <p className="texto-suave mb-0"><i className="bi bi-geo-alt me-1" />{p.origen} → {p.destino}</p>
        </div>
        <div className="text-md-end">
          <p className="texto-suave mb-0"><i className="bi bi-truck me-1" />{p.vehiculo_tipo}</p>
          <p className="fs-4 fw-bold mb-2">{dinero(p.total)}</p>
          <span className="btn btn-light btn-sm">Ver detalle <i className="bi bi-arrow-right" /></span>
        </div>
      </div>
    </Link>
  );
}
