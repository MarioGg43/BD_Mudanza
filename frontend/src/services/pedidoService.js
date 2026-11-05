import { api } from './api';

// Contrato con Django (api/urls.py):
// GET  /pedidos             POST /pedidos
// GET  /pedidos/:id         PUT  /pedidos/:id
// POST /pedidos/:id/cancelar
// GET  /pedidos/:id/comprobante (PDF)
export const pedidoService = {
  // { pedidos } para el cliente; el administrador recibe además { avisos }
  getAll: async (filtros = {}, signal) => {
    const { data } = await api.get('/pedidos', { params: filtros, signal });
    return data;
  },
  getById: async (id, signal) => {
    const { data } = await api.get(`/pedidos/${id}`, { signal });
    return data;
  },
  create: async (pedido) => {
    const { data } = await api.post('/pedidos', pedido);
    return data;
  },
  update: async (id, pedido) => {
    const { data } = await api.put(`/pedidos/${id}`, pedido);
    return data;
  },
  cancelar: async (id, motivo) => {
    const { data } = await api.post(`/pedidos/${id}/cancelar`, { motivo });
    return data;
  },
  // El PDF necesita el token, así que se baja con Axios y se abre como archivo
  descargarComprobante: async (id) => {
    const { data } = await api.get(`/pedidos/${id}/comprobante`, { responseType: 'blob' });
    const url = URL.createObjectURL(data);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Comprobante-pedido-${id}.pdf`;
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  },
};
