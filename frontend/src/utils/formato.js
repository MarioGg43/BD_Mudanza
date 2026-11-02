export const dinero = (n) =>
  '$' + Number(n || 0).toLocaleString('es-AR', { minimumFractionDigits: 0, maximumFractionDigits: 2 });

// '2026-11-05' → '05/11/2026' (sin pasar por Date, para que no se corra por la zona horaria)
export const fecha = (iso) => (iso ? iso.slice(0, 10).split('-').reverse().join('/') : '');

export const diaSemana = (iso) => {
  const [a, m, d] = iso.split('-').map(Number);
  const texto = new Date(a, m - 1, d).toLocaleDateString('es-AR', { weekday: 'long' });
  return texto.charAt(0).toUpperCase() + texto.slice(1);
};

// Días que faltan desde hoy hasta esa fecha (0 = hoy, negativo = ya pasó)
export const diasHasta = (iso) => {
  const [a, m, d] = iso.split('-').map(Number);
  const hoy = new Date();
  hoy.setHours(0, 0, 0, 0);
  return Math.round((new Date(a, m - 1, d) - hoy) / 86400000);
};

// Igual que reglas.clave_objeto de Django: sin mayúsculas, tildes ni signos, y en singular.
// «Sillas», «silla» y «SILLA» dan lo mismo.
export function clave(texto) {
  return (texto || '')
    .normalize('NFKD')
    .replace(/[^\x00-\x7f]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9 ]/g, ' ')
    .split(/\s+/)
    .filter(Boolean)
    .map((p) => (p.endsWith('es') && p.length > 4 ? p.slice(0, -2) : p.endsWith('s') && p.length > 3 ? p.slice(0, -1) : p))
    .join(' ');
}

export const conMayuscula = (t) => t.charAt(0).toUpperCase() + t.slice(1);
