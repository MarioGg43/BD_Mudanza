// Ícono según el nombre del servicio (los servicios los carga el administrador,
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
