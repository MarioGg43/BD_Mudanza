import { api } from './api';

const get = async (url, signal, params) => (await api.get(url, { signal, params })).data;

// El mapa (OpenRouteService a través de Django: la clave queda en el servidor)
export const mapaService = {
  recorrido: (idPedido, signal) => get(`/pedidos/${idPedido}/recorrido`, signal),
  // la dirección del punto que se tocó en el mapa
  direccion: (lat, lon, signal) => get('/mapa/direccion', signal, { lat: lat.toFixed(6), lon: lon.toFixed(6) }),
  // dónde cae una dirección escrita a mano («¿Es acá?»)
  ubicar: (direccion, signal) => get('/mapa/ubicar', signal, { direccion }),
};
