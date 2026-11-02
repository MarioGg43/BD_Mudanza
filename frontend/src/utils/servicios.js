// Ícono y descripción según el nombre del servicio (los servicios los carga el administrador,
// así que se reconocen por palabras; uno nuevo usa los valores generales)
export function iconoServicio(nombre) {
  const n = nombre.toLowerCase();
  if (n.includes('flete')) return 'bi-box-seam';
  if (n.includes('nacional')) return 'bi-signpost-split';
  if (n.includes('mudanza')) return 'bi-house-door';
  if (n.includes('embalaje')) return 'bi-boxes';
  if (n.includes('armado')) return 'bi-tools';
  return 'bi-stars';
}

export function descripcionServicio(nombre) {
  const n = nombre.toLowerCase();
  if (n.includes('flete')) return 'Para pocos muebles, compras grandes o un traslado rápido dentro de la ciudad.';
  if (n.includes('nacional')) return 'Llevamos tu mudanza a cualquier provincia, con el camión y el personal de punta a punta.';
  if (n.includes('mudanza')) return 'Tu casa, departamento u oficina completa dentro de Salta, con carga y descarga.';
  return 'Un servicio de la empresa con personal propio.';
}
