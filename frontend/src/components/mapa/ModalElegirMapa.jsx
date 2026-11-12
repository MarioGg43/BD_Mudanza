import { useEffect, useRef, useState } from 'react';
import { Modal } from 'react-bootstrap';
import axios from 'axios';
import { mapaService } from '../../services/mapaService';
import { L, SALTA, capaOSM } from './leaflet';

const AYUDA = 'Si falta el número o algo no coincide, corregilo acá antes de usarla.';

/* «Elegir en el mapa»: la persona toca el lugar (o «Estoy acá») y Django le devuelve la dirección
   de ese punto. Se puede corregir antes de usarla. Devuelve el texto y el punto exacto. */
export function ModalElegirMapa({ titulo, desde, onUsar, onHide }) {
  const lienzo = useRef(null);
  const mapa = useRef(null);
  const marcador = useRef(null);
  const consulta = useRef(0);
  const [punto, setPunto] = useState(null);
  const [direccion, setDireccion] = useState('');
  const [estado, setEstado] = useState({ texto: AYUDA, error: false, buscando: false });

  const elegir = async (lat, lon) => {
    if (marcador.current) marcador.current.setLatLng([lat, lon]);
    else marcador.current = L.marker([lat, lon]).addTo(mapa.current);
    setPunto({ lat, lon });
    const esta = ++consulta.current;  // si toca otro punto antes de la respuesta, vale el último
    setEstado({ texto: 'Buscando la dirección…', error: false, buscando: true });
    try {
      const r = await mapaService.direccion(lat, lon);
      if (esta !== consulta.current) return;
      if (!r.ok) { setEstado({ texto: r.error, error: true, buscando: false }); return; }
      setDireccion(r.direccion);
      setEstado({ texto: AYUDA, error: false, buscando: false });
    } catch (err) {
      if (esta === consulta.current && !axios.isCancel(err)) setEstado({ texto: err.message, error: true, buscando: false });
    }
  };

  // el mapa se arma cuando la ventana ya se ve: si no, Leaflet calcula mal el tamaño
  const alMostrar = () => {
    mapa.current = L.map(lienzo.current).setView(desde ? [desde.lat, desde.lon] : SALTA, desde ? 17 : 13);
    capaOSM().addTo(mapa.current);
    mapa.current.on('click', (e) => elegir(e.latlng.lat, e.latlng.lng));
  };
  useEffect(() => () => mapa.current?.remove(), []);

  const estoyAca = () => {
    if (!navigator.geolocation) { setEstado({ texto: 'Este navegador no comparte la ubicación.', error: true }); return; }
    setEstado({ texto: 'Buscando dónde estás…', error: false });
    navigator.geolocation.getCurrentPosition(
      (pos) => { mapa.current.setView([pos.coords.latitude, pos.coords.longitude], 17); elegir(pos.coords.latitude, pos.coords.longitude); },
      () => setEstado({ texto: 'No se pudo obtener tu ubicación. Tocá el lugar en el mapa.', error: true }),
      { enableHighAccuracy: true, timeout: 10000 });
  };

  const listo = direccion.trim() && punto && !estado.buscando;
  return (
    <Modal show onHide={onHide} onEntered={alMostrar} size="lg" centered>
      <Modal.Header closeButton><Modal.Title as="h2" className="h5 fw-bold">Elegí «{titulo}» en el mapa</Modal.Title></Modal.Header>
      <Modal.Body>
        <div className="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-2">
          <p className="small text-muted mb-0">Tocá el mapa donde es la mudanza. Podés acercarte con la rueda del mouse o con los dedos.</p>
          <button type="button" className="btn btn-sm btn-outline-secondary" onClick={estoyAca}><i className="bi bi-crosshair me-1" />Estoy acá</button>
        </div>
        <div ref={lienzo} className="mapa-caja mapa-elegir" role="application" aria-label="Mapa para elegir la dirección" />
        <label htmlFor="direccionElegida" className="form-label fw-semibold mt-3 mb-1">Dirección</label>
        <input id="direccionElegida" className="form-control" maxLength={200} placeholder="Tocá un punto del mapa"
          value={direccion} disabled={!punto || estado.buscando} onChange={(e) => setDireccion(e.target.value)} />
        <div className={`form-text ${estado.error ? 'text-danger' : ''}`}>{estado.texto}</div>
      </Modal.Body>
      <Modal.Footer>
        <button type="button" className="btn btn-outline-secondary" onClick={onHide}>Cancelar</button>
        <button type="button" className="btn btn-primary fw-bold" disabled={!listo} onClick={() => onUsar(direccion.trim().slice(0, 200), punto)}>
          Usar esta dirección
        </button>
      </Modal.Footer>
    </Modal>
  );
}
