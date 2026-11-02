// Mismos colores que _estado.html de Django
export function EstadoBadge({ pedido }) {
  if (pedido.vencido) return <span className="estado estado-anulado">Vencido</span>;
  if (pedido.en_curso) return <span className="estado estado-finalizado">En curso</span>;
  return <span className={`estado estado-${pedido.estado.toLowerCase()}`}>{pedido.estado}</span>;
}
