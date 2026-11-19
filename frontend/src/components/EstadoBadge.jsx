// La etiqueta del estado, igual que _estado.html de Django: el estado y, al lado, lo que haga falta
// saber (vencido, en curso, y para el administrador: atrasada o para finalizar).
export function EstadoBadge({ pedido: p }) {
  const atrasada = p.atrasada ?? p.gestion?.atrasada;
  const paraFinalizar = p.para_finalizar ?? p.gestion?.para_finalizar;
  return (
    <>
      <span className={`estado estado-${p.estado.toLowerCase()}`}>{p.estado}</span>
      {p.vencido && <> <span className="estado estado-anulado" title="Pendiente con la fecha pasada: nadie lo confirmó">Vencido</span></>}
      {p.en_curso && <> <span className="estado estado-confirmado" title="El chofer marcó «Empezamos»"><i className="bi bi-play-fill" /> En curso</span></>}
      {atrasada
        ? <> <span className="estado estado-atrasada" title="Ya tenía que terminar y otra mudanza la espera"><i className="bi bi-alarm" /> Atrasada</span></>
        : paraFinalizar && <> <span className="estado estado-pendiente" title="La mudanza ya empezó: falta finalizarla">Para finalizar</span></>}
    </>
  );
}
