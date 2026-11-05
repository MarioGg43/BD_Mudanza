import { api } from './api';

export const authService = {
  login: async (usuario, clave) => {
    const { data } = await api.post('/auth/login', { usuario, clave });
    return data; // { token, usuario }
  },
  registro: async (datos) => {
    const { data } = await api.post('/auth/registro', datos);
    return data;
  },
  // { usuario, clave (la provisoria), nueva, confirmar } → { token, usuario }
  cambiarClave: async (datos) => {
    const { data } = await api.post('/auth/cambiar-clave', datos);
    return data;
  },
  yo: async () => {
    const { data } = await api.get('/auth/yo');
    return data.usuario;
  },
};
