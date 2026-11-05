import { api } from './api';

// Lo que hace el administrador con los pedidos (api/views_admin.py)
export const adminService = {
  opciones: async (signal) => (await api.get('/admin/opciones', { signal })).data,

  confirmar: async (id) => (await api.post(`/pedidos/${id}/confirmar`)).data,
  finalizar: async (id) => (await api.post(`/pedidos/${id}/finalizar`)).data,
  anular: async (id, motivo) => (await api.post(`/pedidos/${id}/anular`, { motivo })).data,

  getPersonal: async (id, signal) => (await api.get(`/pedidos/${id}/personal`, { signal })).data,
  asignarPersonal: async (id, chofer, ayudantes) => (await api.put(`/pedidos/${id}/personal`, { chofer, ayudantes })).data,

  getServicios: async (id, signal) => (await api.get(`/pedidos/${id}/servicios`, { signal })).data,
  editarServicios: async (id, servicio, adicionales) => (await api.put(`/pedidos/${id}/servicios`, { servicio, adicionales })).data,

  // con fecha y hora, trae los vehículos libres en ese horario
  getReprogramar: async (id, { fecha, hora } = {}, signal) =>
    (await api.get(`/pedidos/${id}/reprogramar`, { params: { fecha, hora }, signal })).data,
  reprogramar: async (id, datos) => (await api.post(`/pedidos/${id}/reprogramar`, datos)).data,
};
