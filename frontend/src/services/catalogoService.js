import { api } from './api';

export const catalogoService = {
  // servicios principales y adicionales, objetos, límites
  get: async (signal) => {
    const { data } = await api.get('/catalogo', { signal });
    return data;
  },
  vehiculosLibres: async ({ fecha, hora, servicio, pedido }, signal) => {
    const { data } = await api.get('/vehiculos-libres', { params: { fecha, hora, servicio, pedido }, signal });
    return data; // { vehiculos, motivo }
  },
};
