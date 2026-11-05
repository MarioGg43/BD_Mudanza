import { api } from './api';

// Portal del personal (api/views_portal.py)
export const portalService = {
  mudanzas: async (signal) => (await api.get('/portal', { signal })).data,
  empezar: async (id) => (await api.post(`/portal/${id}/empezar`)).data,
  terminar: async (id) => (await api.post(`/portal/${id}/terminar`)).data,
  getRelevamiento: async (id, signal) => (await api.get(`/portal/${id}/relevamiento`, { signal })).data,
  guardarRelevamiento: async (id, datos) => (await api.post(`/portal/${id}/relevamiento`, datos)).data,
};
