import { api } from './api';

// Un link común no manda el token, por eso el PDF se pide con Axios y después se «descarga» a mano.
export async function descargarPdf(url, nombre, params) {
  const { data } = await api.get(url, { params, responseType: 'blob' });
  const enlace = URL.createObjectURL(data);
  const a = document.createElement('a');
  a.href = enlace;
  a.download = nombre;
  a.click();
  setTimeout(() => URL.revokeObjectURL(enlace), 1000);
}
