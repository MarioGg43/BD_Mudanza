import axios from 'axios';

export const CLAVE_SESION = 'mudanzas.sesion';

// Instancia única de Axios: la URL base sale de la variable de entorno de Vite (.env)
export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  headers: { 'Content-Type': 'application/json' },
  timeout: 15000,
});

// Antes de cada petición: si hay sesión, se manda el token
api.interceptors.request.use((config) => {
  try {
    const sesion = JSON.parse(localStorage.getItem(CLAVE_SESION));
    if (sesion?.token) config.headers.Authorization = `Bearer ${sesion.token}`;
  } catch {
    // sin sesión guardada (o almacenamiento bloqueado): la petición sale sin token
  }
  return config;
});

// Después de cada respuesta: los errores llegan siempre igual a los componentes
// { message, status, errores: {campo: mensaje} }
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (axios.isCancel(error)) return Promise.reject(error);
    const err = new Error('Ocurrió un error inesperado.');
    err.errores = {};
    if (error.response) {
      // 4xx / 5xx: el servidor contestó
      err.status = error.response.status;
      err.message = error.response.data?.error || `Error ${error.response.status} del servidor.`;
      err.errores = error.response.data?.errores || {};
      // token vencido o inválido: se avisa a la app para que cierre la sesión
      if (err.status === 401) window.dispatchEvent(new Event('sesion-vencida'));
    } else if (error.request) {
      err.message = 'Error de red: no se pudo conectar con el servidor.';
    }
    return Promise.reject(err);
  },
);
