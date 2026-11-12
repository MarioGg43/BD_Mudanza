import { api } from './api';
import { descargarPdf } from './descargas';

const get = async (url, signal, params) => (await api.get(url, { signal, params })).data;
const post = async (url, datos) => (await api.post(url, datos)).data;

// Parcial N° 2: tablero, reportes (M2) y notificaciones (M3) — api/views_analisis.py
export const analisisService = {
  tablero: (periodo, signal) => get('/tablero', signal, { periodo }),

  reportes: (signal) => get('/reportes', signal),
  reporte: (clave, filtros, signal) => get(`/reportes/${clave}`, signal, filtros),
  pdfReporte: (clave, titulo, filtros) => descargarPdf(`/reportes/${clave}/pdf`, `${titulo.replaceAll(' ', '_')}.pdf`, filtros),

  notificaciones: (filtros, signal) => get('/notificaciones', signal, filtros),
  contarNotificaciones: (signal) => get('/notificaciones/contar', signal),
  leerNotificacion: (id) => post(`/notificaciones/${id}/leer`),
  leerTodas: () => post('/notificaciones/leer-todas'),

  configuracion: (signal) => get('/configuracion', signal),
  guardarConfiguracion: async (valores) => (await api.put('/configuracion', valores)).data,
  evaluarAlertas: () => post('/alertas/evaluar'),
};
