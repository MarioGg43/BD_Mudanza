// La lista de la ventana «Agregar objeto» ({ id, nombre, nuevo, cantidad, fragil, detalle }) y lo
// que guarda la API ({ objeto, cantidad, fragil, observacion }). Un objeto «Otro» guarda su nombre en
// la observación: «Piano — se desarma». Lo usan el pedido del cliente y el relevamiento del chofer.
export const SEP = ' — ';

export function desdeServidor(i) {
  if (i.otro) {
    const [nombre, ...resto] = (i.observacion || '').split(SEP);
    return { id: i.objeto, nombre: nombre.trim(), nuevo: true, cantidad: i.cantidad, fragil: i.fragil, detalle: resto.join(SEP).trim() };
  }
  return { id: i.objeto, nombre: i.nombre, nuevo: false, cantidad: i.cantidad, fragil: i.fragil, detalle: i.observacion || '' };
}

export const haciaServidor = (it) => ({
  objeto: it.id, cantidad: it.cantidad, fragil: it.fragil,
  observacion: it.nuevo ? it.nombre + (it.detalle ? SEP + it.detalle : '') : it.detalle,
});
