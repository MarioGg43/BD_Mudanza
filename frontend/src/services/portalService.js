import { api } from './api';

// Portal del personal (api/views_portal.py)
export const portalService = {
  mudanzas: async (signal) => (await api.get('/portal', { signal })).data,
  empezar: async (id) => (await api.post(`/portal/${id}/empezar`)).data,
  // los materiales que salieron, para contarlos antes de terminar
  getTerminar: async (id, signal) => (await api.get(`/portal/${id}/terminar`, { signal })).data,
  // usados: { id_material: cantidad } (lo que se gastó o, en los reutilizables, cuántos volvieron)
  terminar: async (id, usados = {}) => (await api.post(`/portal/${id}/terminar`, { usados })).data,
  getRelevamiento: async (id, signal) => (await api.get(`/portal/${id}/relevamiento`, { signal })).data,
  guardarRelevamiento: async (id, datos) => (await api.post(`/portal/${id}/relevamiento`, datos)).data,
};
