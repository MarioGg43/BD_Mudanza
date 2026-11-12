import { api } from './api';

const get = async (url, signal, params) => (await api.get(url, { signal, params })).data;

// Control de materiales (api/views_materiales.py)
export const materialesService = {
  lista: (signal) => get('/materiales', signal),
  ficha: (id, pagina, signal) => get(`/materiales/${id}`, signal, { pagina }),
  crear: async (datos) => (await api.post('/materiales', datos)).data,
  editar: async (id, datos) => (await api.put(`/materiales/${id}`, datos)).data,
  movimiento: async (id, datos) => (await api.post(`/materiales/${id}/movimiento`, datos)).data,
  baja: async (id) => (await api.post(`/materiales/${id}/baja`)).data,
  // los activos, para elegirlos en un servicio
  catalogo: (signal) => get('/materiales/catalogo', signal),
};
