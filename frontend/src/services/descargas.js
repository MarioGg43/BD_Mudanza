import { api } from './api';

// Los PDF piden el token, así que se bajan con Axios y se guardan como archivo
export async function descargarPdf(url, nombre, params) {
  const { data } = await api.get(url, { params, responseType: 'blob' });
  const enlace = URL.createObjectURL(data);
  const a = document.createElement('a');
  a.href = enlace;
  a.download = nombre;
  a.click();
  setTimeout(() => URL.revokeObjectURL(enlace), 1000);
}
