// Datos de la empresa que muestran la página de inicio y su pie.
// Tomados de su sitio oficial: https://mudanzassalta.com.ar (noviembre de 2026).
// Los servicios y camiones NO van acá: salen de la base de datos (GET /api/publico).
export const EMPRESA = {
  nombre: 'Mudanzas y Fletes Salta',
  eslogan: 'Mudanzas puerta a puerta',
  bajada: 'Llegamos donde necesites, dentro o fuera de tu ciudad, con unidades adaptadas a tu necesidad y presupuesto.',
  anios: 15, // años en el rubro
  telefono: '387 473-2192',
  whatsapp: '5493874732192', // con código de país, sin + ni espacios (para el enlace wa.me)
  correo: 'info@mudanzassalta.com.ar',
  instagram: 'mudanzas_fletes_salta',
  facebook: 'MudanzasFletesSalta',
  sitio: 'https://mudanzassalta.com.ar',
  zona: 'Salta y todo el país.',
  destinos: ['Interior de Salta', 'Jujuy', 'Tucumán', 'Córdoba', 'Santiago del Estero', 'Santa Fe', 'Buenos Aires'],
  pagos: 'Aceptamos todos los medios de pago, con descuentos en efectivo.',
};

// Lo que la empresa destaca de sí misma («¿Por qué elegir Mudanzas Salta?» en su sitio)
export const RAZONES = [
  { icono: 'bi-award', titulo: 'Más de 15 años', texto: 'Experiencia comprobada en el rubro.' },
  { icono: 'bi-truck', titulo: 'Vehículos adaptados', texto: 'Equipos especializados y unidades para cada necesidad.' },
  { icono: 'bi-shield-check', titulo: 'Cuidado extremo', texto: 'La seguridad de tus pertenencias en cada traslado.' },
  { icono: 'bi-clipboard-check', titulo: 'Presupuesto sin cargo', texto: 'Sin compromiso, en tu domicilio.' },
  { icono: 'bi-box-seam', titulo: 'Servicio completo', texto: 'Desde el embalaje hasta los izajes.' },
  { icono: 'bi-geo-alt', titulo: 'Seguimiento satelital', texto: 'Controlás cada paso de tu mudanza.' },
];

// Servicios que ofrece la empresa además de los que se piden por el sistema
export const ESPECIALIDADES = [
  { icono: 'bi-house-door', titulo: 'Mudanzas puerta a puerta', texto: 'Dentro o fuera de tu ciudad, con unidades adaptadas a tu necesidad y presupuesto.' },
  { icono: 'bi-boxes', titulo: 'Embalaje, cuidado y seguimiento', texto: 'Personal calificado y ayudantes para el embalaje, la carga y la descarga.' },
  { icono: 'bi-arrow-up-square', titulo: 'Izajes de objetos pesados y frágiles', texto: 'Personal idóneo que cuida tus objetos más preciados con seguridad y rapidez.' },
];
