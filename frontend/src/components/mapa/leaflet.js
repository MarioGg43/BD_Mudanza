// Leaflet con OpenStreetMap, igual que las pantallas de Django.
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import icono from 'leaflet/dist/images/marker-icon.png';
import icono2x from 'leaflet/dist/images/marker-icon-2x.png';
import sombra from 'leaflet/dist/images/marker-shadow.png';

// con Vite, las imágenes del marcador hay que indicarlas a mano
L.Icon.Default.mergeOptions({ iconUrl: icono, iconRetinaUrl: icono2x, shadowUrl: sombra });

export const SALTA = [-24.7821, -65.4117];

export function capaOSM() {
  return L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    referrerPolicy: 'strict-origin-when-cross-origin', // sin esto OpenStreetMap bloquea los mapas
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> · openrouteservice.org',
  });
}

export { L };
