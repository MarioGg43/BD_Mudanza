import { useEffect, useRef } from 'react';
import { useCarga } from '../../hooks/useCarga';
import { mapaService } from '../../services/mapaService';
import { L, capaOSM } from './leaflet';

/* El recorrido de la mudanza en el mapa: la ruta para camión que arma OpenRouteService (en
   GeoJSON), los dos puntos y los km y minutos. Si el servicio no responde, queda «Cómo llegar». */
export function MapaRecorrido({ idPedido, comoLlegar }) {
  const lienzo = useRef(null);
  const { datos, loading } = useCarga((signal) => mapaService.recorrido(idPedido, signal), [idPedido]);

  useEffect(() => {
    if (!datos?.ok || !lienzo.current) return undefined;
    const mapa = L.map(lienzo.current, { scrollWheelZoom: false });
    capaOSM().addTo(mapa);
    const ruta = L.geoJSON(datos.ruta, { style: { color: '#e8590c', weight: 5, opacity: 0.85 } }).addTo(mapa);
    // las etiquetas vienen del servicio de mapas: van como texto, nunca como HTML
    const marcador = (p, titulo) => {
      const texto = document.createElement('div');
      const negrita = document.createElement('b');
      negrita.textContent = titulo;
      texto.append(negrita, document.createElement('br'), p.etiqueta);
      return L.marker([p.lat, p.lon], { title: titulo }).bindPopup(texto).addTo(mapa);
    };
    marcador(datos.origen, 'Desde');
    marcador(datos.destino, 'Hasta');
    mapa.fitBounds(ruta.getBounds(), { padding: [30, 30] });
    return () => mapa.remove();
  }, [datos]);

  const enlace = datos?.como_llegar || comoLlegar;
  return (
    <section className="card-panel p-3 mb-3">
      <div className="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-2">
        <h2 className="h6 fw-bold text-uppercase text-muted mb-0"><i className="bi bi-map me-1" />Recorrido</h2>
        {datos?.ok && <span className="small fw-semibold">{datos.km.toLocaleString('es-AR')} km · unos {datos.minutos} min en camión</span>}
        {enlace && (
          <a href={enlace} target="_blank" rel="noopener noreferrer" className="btn btn-sm btn-outline-secondary">
            <i className="bi bi-sign-turn-right me-1" />Cómo llegar
          </a>
        )}
      </div>
      {loading && <p className="small text-muted mb-0">Buscando el recorrido…</p>}
      {datos && !datos.ok && <p className="small text-muted mb-0"><i className="bi bi-info-circle me-1" />{datos.error}</p>}
      {datos?.ok && <div ref={lienzo} className="mapa-caja" role="img" aria-label="Mapa con el recorrido de la mudanza" />}
    </section>
  );
}
