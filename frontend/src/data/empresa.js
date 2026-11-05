// Datos e imágenes de la empresa para la página de inicio y su pie.
// Copiados de su sitio oficial, https://mudanzassalta.com.ar, con la autorización de la empresa.
// Las imágenes están en public/empresa/. Los servicios y camiones del sistema NO van acá: salen
// de la base de datos (GET /api/publico).
const IMG = '/empresa';

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
  direccion: 'Barrio El Huaico, Salta',
  zona: 'Salta y todo el país.',
  destinos: ['Interior de Salta', 'Jujuy', 'Tucumán', 'Córdoba', 'Santiago del Estero', 'Santa Fe', 'Buenos Aires'],
  pagos: 'Aceptamos todos los medios de pago, con descuentos en efectivo.',
  mapa: 'https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d28992.816061630812!2d-65.44276642009272!3d-24.72337799318718!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x941bc105df349b99%3A0xfd20bd337b006afb!2sBarrio%20El%20Huaico%2C%20A4400%2C%20Salta!5e0!3m2!1ses!2sar!4v1733250922680!5m2!1ses!2sar',
  resenas: 'https://www.google.com/search?q=Mudanzas+y+Fletes+Salta&kgmid=/g/11l6k_7chg',
  logo: `${IMG}/logo.png`,
  imagenes: {
    porQue: `${IMG}/metodologia.jpg`,
    pagos: `${IMG}/formas-de-pago.jpg`,
    resenas: `${IMG}/resenas.jpg`,
  },
};

// Las diapositivas de la portada (con sus fotos y frases)
export const DIAPOSITIVAS = [
  { imagen: `${IMG}/slider-bg-1.jpg`, titulo: 'Mudanzas sin límites', texto: 'Tu hogar o negocio en cualquier rincón del país.' },
  { imagen: `${IMG}/slider-bg-2.jpg`, titulo: 'Confianza y experiencia', texto: '15 años conectando destinos con seguridad y profesionalismo.' },
  { imagen: `${IMG}/slider-bg-3.jpg`, titulo: 'Servicio disponible y respuesta inmediata', texto: 'Dejá tus pertenencias en manos expertas. Nos ocupamos de todo.' },
];

// Lo que la empresa destaca de sí misma («¿Por qué elegir Mudanzas Salta?» en su sitio)
export const RAZONES = [
  { icono: 'bi-award', titulo: 'Más de 15 años', texto: 'Experiencia comprobada en el rubro.' },
  { icono: 'bi-truck', titulo: 'Vehículos adaptados', texto: 'Equipos especializados y unidades para cada necesidad.' },
  { icono: 'bi-shield-check', titulo: 'Cuidado extremo', texto: 'La seguridad de tus pertenencias en cada traslado.' },
  { icono: 'bi-clipboard-check', titulo: 'Presupuesto sin cargo', texto: 'Sin compromiso, en tu domicilio.' },
  { icono: 'bi-box-seam', titulo: 'Servicio completo', texto: 'Desde el embalaje hasta los izajes.' },
  { icono: 'bi-geo-alt', titulo: 'Seguimiento satelital', texto: 'Controlás cada paso de tu mudanza.' },
];

// Sus servicios, con la foto de cada uno
export const ESPECIALIDADES = [
  { imagen: `${IMG}/post-1.jpg`, titulo: 'Mudanzas puerta a puerta', texto: 'Llegamos donde necesites, dentro o fuera de tu ciudad, con unidades adaptadas a tu necesidad y presupuesto.' },
  { imagen: `${IMG}/post-2.jpg`, titulo: 'Embalaje, cuidado y seguimiento', texto: 'Personal calificado y ayudantes para el traslado, el embalaje, la carga y la descarga. Y seguís cada paso con seguimiento satelital.' },
  { imagen: `${IMG}/post-3.jpg`, titulo: 'Izajes de objetos pesados y frágiles', texto: 'Personal idóneo que cuida tus objetos más preciados con total seguridad y rapidez.' },
];

// «Nuestros trabajos»: algunos de los que la empresa hace a diario
export const TRABAJOS = Array.from({ length: 9 }, (_, n) => `${IMG}/trabajo-${n + 1}.jpg`);
