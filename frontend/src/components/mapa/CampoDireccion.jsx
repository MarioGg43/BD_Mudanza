import { useEffect, useRef, useState } from 'react';
import axios from 'axios';
import { mapaService } from '../../services/mapaService';
import { L, capaOSM } from './leaflet';
import { ModalElegirMapa } from './ModalElegirMapa';

// Un mapa chico, quieto, con el punto marcado (la vista previa de la dirección)
function MapaChico({ punto }) {
  const lienzo = useRef(null);
  useEffect(() => {
    const mapa = L.map(lienzo.current, { zoomControl: false, attributionControl: false, dragging: false, scrollWheelZoom: false,
      doubleClickZoom: false, boxZoom: false, keyboard: false, touchZoom: false }).setView([punto.lat, punto.lon], 16);
    capaOSM().addTo(mapa);
    L.marker([punto.lat, punto.lon]).addTo(mapa);
    return () => mapa.remove();
  }, [punto.lat, punto.lon]);
  return <div ref={lienzo} className="mapa-mini" aria-hidden="true" />;
}

/* Una dirección del pedido con su punto exacto. Si la persona la marca en el mapa, se guarda ese
   punto. Si la escribe a mano, al salir del campo se busca dónde cae: «¿Es acá?». Con «Sí» se
   guarda ese punto; con «No» se abre el mapa ahí para corregirlo. Si vuelve a escribir, el punto
   se borra porque ya no corresponde. Mismo comportamiento que la pantalla de Django. */
export function CampoDireccion({ name, label, valor, punto, error, mapaActivo, onCambio }) {
  const [propuesto, setPropuesto] = useState(null);   // { lat, lon, etiqueta } o { error }
  const [buscando, setBuscando] = useState(false);
  const [abrirMapa, setAbrirMapa] = useState(null);   // null = cerrado; si no, desde dónde arranca
  const [confirmado, setConfirmado] = useState(false);
  const consulta = useRef(null);

  // Si la persona vuelve a escribir la dirección, el punto marcado antes ya no sirve: lo borramos.
  const escribir = (e) => {
    onCambio(e.target.value, null);   // a mano: el punto viejo ya no corresponde
    setPropuesto(null);
    setConfirmado(false);
    consulta.current?.abort();
  };
  // Al salir del campo le preguntamos a Django dónde queda lo que escribió y mostramos «¿Es acá?».
  const proponer = async () => {
    const texto = valor.trim();
    if (!mapaActivo || punto || texto.length < 5) return;
    consulta.current?.abort();
    const controller = new AbortController();
    consulta.current = controller;
    setBuscando(true);
    try {
      const r = await mapaService.ubicar(texto, controller.signal);
      setPropuesto(r.ok ? { lat: r.lat, lon: r.lon, etiqueta: r.etiqueta } : { error: r.error });
    } catch (err) {
      if (!axios.isCancel(err)) setPropuesto({ error: err.message });
    } finally {
      if (!controller.signal.aborted) setBuscando(false);
    }
  };

  return (
    <div className="col-sm-6">
      <label htmlFor={name} className="form-label">{label}</label>
      <div className="input-group">
        <input id={name} name={name} className={`form-control ${error ? 'is-invalid' : ''}`} maxLength={200}
          placeholder="Calle, número y ciudad" value={valor} onChange={escribir} onBlur={proponer} />
        {mapaActivo && (
          <button type="button" className="btn btn-outline-secondary" title={`Elegir «${label}» en el mapa`}
            aria-label={`Elegir «${label}» en el mapa`} onClick={() => setAbrirMapa(punto || propuesto?.lat ? (punto || propuesto) : false)}>
            <i className="bi bi-geo-alt-fill text-marca" />
          </button>
        )}
      </div>
      {error && <div className="invalid-feedback d-block">{error}</div>}

      {/* dónde quedó: el punto marcado o, si se escribió a mano, «¿Es acá?» */}
      {mapaActivo && (punto || buscando || propuesto) && (
        <div className="ubicacion-previa">
          {punto ? (
            <>
              <MapaChico punto={punto} />
              <p className="small mb-0"><i className="bi bi-geo-alt-fill text-success me-1" />{confirmado ? 'Ubicación confirmada.' : 'Ubicación marcada en el mapa.'}</p>
            </>
          ) : buscando ? (
            <p className="small mb-0">Buscando dónde queda…</p>
          ) : propuesto.error ? (
            <div className="small">
              <p className="mb-1">{propuesto.error} Podés marcarla en el mapa.</p>
              <button type="button" className="btn btn-sm btn-outline-secondary" onClick={() => setAbrirMapa(false)}><i className="bi bi-geo-alt me-1" />Marcarla en el mapa</button>
            </div>
          ) : (
            <>
              <MapaChico punto={propuesto} />
              <div className="small">
                <p className="mb-1"><b>¿Es acá?</b> Lo ubicamos en {propuesto.etiqueta}.</p>
                <div className="d-flex flex-wrap gap-2">
                  <button type="button" className="btn btn-sm btn-success" onClick={() => { onCambio(valor, { lat: propuesto.lat, lon: propuesto.lon }); setConfirmado(true); }}>
                    <i className="bi bi-check-lg me-1" />Sí, es acá
                  </button>
                  <button type="button" className="btn btn-sm btn-outline-secondary" onClick={() => setAbrirMapa(propuesto)}>
                    <i className="bi bi-geo-alt me-1" />No, lo marco en el mapa
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      )}

      {abrirMapa !== null && (
        <ModalElegirMapa titulo={label} desde={abrirMapa || null} onHide={() => setAbrirMapa(null)}
          onUsar={(texto, p) => { onCambio(texto, p); setPropuesto(null); setConfirmado(false); setAbrirMapa(null); }} />
      )}
    </div>
  );
}
