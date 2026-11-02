import { api } from './api';

// Lo que se ve sin iniciar sesión (no lleva token)
export const publicoService = {
  getInfo: async (signal) => {
    const { data } = await api.get('/publico', { signal });
    return data; // { principales, adicionales, camiones, horas_limite }
  },
};
