import { fecha } from '../utils/formato';

const PASOS = [
  { titulo: 'Pedido enviado', icono: 'bi-send' },
  { titulo: 'Confirmado', icono: 'bi-check2-circle' },
  { titulo: 'En curso', icono: 'bi-truck' },
  { titulo: 'Finalizado', icono: 'bi-flag' },
];

// Hasta qué paso llegó el pedido (0 a 3)
function pasoActual(p) {
  if (p.estado === 'Finalizado') return 3;
  if (p.en_curso) return 2;
  if (p.estado === 'Confirmado') return 1;
  return 0;
}

const hora = (fechaHora) => fechaHora?.slice(11);

// El texto chico debajo de cada paso
function detalle(p, n) {
  if (n === 0) return fecha(p.fecha_pedido);
  if (n === 1) return p.estado === 'Pendiente' ? 'La empresa lo revisa' : p.chofer ? `Chofer: ${p.chofer}` : '';
  if (n === 2) return p.inicio_real ? `${fecha(p.inicio_real)} ${hora(p.inicio_real)}` : `${fecha(p.fecha_servicio)} ${p.hora_servicio}`;
  return p.fin_real ? `${fecha(p.fin_real)} ${hora(p.fin_real)}` : '';
}

/* Barra de pasos del pedido: Pedido enviado → Confirmado → En curso → Finalizado.
   Un pedido anulado o vencido corta la línea con un último paso en rojo o gris. */
export function LineaEstados({ pedido: p }) {
  const corte = p.estado === 'Anulado'
    ? { titulo: 'Anulado', icono: 'bi-x-lg', clase: 'cortado', texto: p.anulacion ? fecha(p.anulacion.fecha) : '' }
    : p.vencido
      ? { titulo: 'Vencido', icono: 'bi-hourglass-bottom', clase: 'vencido', texto: 'Nadie lo confirmó a tiempo' }
      : null;
  const actual = pasoActual(p);
  const pasos = corte ? [PASOS[0]] : PASOS;

  return (
    <ol className="linea-estados card-panel p-3 mb-3" aria-label="Estado del pedido">
      {pasos.map((paso, n) => {
        const estado = corte || n < actual ? 'hecho' : n === actual ? 'actual' : 'falta';
        return (
          <li key={paso.titulo} className={`paso paso-${estado}`} aria-current={estado === 'actual' ? 'step' : undefined}>
            <span className="paso-icono"><i className={`bi ${estado === 'hecho' ? 'bi-check-lg' : paso.icono}`} /></span>
            <span className="paso-titulo">{paso.titulo}</span>
            <span className="paso-detalle">{estado === 'falta' && n !== 1 ? '' : detalle(p, n)}</span>
          </li>
        );
      })}
      {corte && (
        <li className={`paso paso-${corte.clase}`} aria-current="step">
          <span className="paso-icono"><i className={`bi ${corte.icono}`} /></span>
          <span className="paso-titulo">{corte.titulo}</span>
          <span className="paso-detalle">{corte.texto}</span>
        </li>
      )}
    </ol>
  );
}
