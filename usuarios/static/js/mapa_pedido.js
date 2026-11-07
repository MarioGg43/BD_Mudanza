// Dibuja el recorrido de una mudanza (pedidos/_mapa.html) con Leaflet sobre OpenStreetMap.
// El recorrido lo arma Django con OpenRouteService y llega en GeoJSON, que Leaflet dibuja directo.
(function () {
  const COLOR = '#E10E0E'; // el rojo de la marca

  function duracion(minutos) {
    if (minutos < 60) return minutos + ' min';
    const h = Math.floor(minutos / 60), m = minutos % 60;
    return h + ' h' + (m ? ' ' + m + ' min' : '');
  }

  function marcador(punto, titulo) {
    // la etiqueta viene del servicio de mapas: va como texto, nunca como HTML
    const texto = document.createElement('div');
    const negrita = document.createElement('b');
    negrita.textContent = titulo;
    texto.append(negrita, document.createElement('br'), punto.etiqueta);
    return L.marker([punto.lat, punto.lon], { title: titulo }).bindPopup(texto);
  }

  async function dibujar(caja) {
    const info = caja.querySelector('[data-mapa-info]');
    const lienzo = caja.querySelector('[data-mapa-lienzo]');
    let datos;
    try {
      const r = await fetch(caja.dataset.mapaRecorrido, { headers: { Accept: 'application/json' } });
      datos = await r.json();
    } catch (e) {
      datos = { ok: false, error: 'No se pudo cargar el mapa.' };
    }
    if (!datos.ok) {
      // sin mapa: queda el aviso y el botón «Cómo llegar»
      info.textContent = datos.error || 'No se pudo cargar el mapa.';
      lienzo.remove();
      return;
    }
    info.textContent = 'Unos ' + datos.km.toLocaleString('es-AR') + ' km · ' + duracion(datos.minutos)
      + ' de viaje en camión (estimado).';
    const mapa = L.map(lienzo, { scrollWheelZoom: false });
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> · Ruta: openrouteservice.org',
    }).addTo(mapa);
    const ruta = L.geoJSON(datos.ruta, { style: { color: COLOR, weight: 5, opacity: 0.85 } }).addTo(mapa);
    marcador(datos.origen, 'Desde').addTo(mapa);
    marcador(datos.destino, 'Hasta').addTo(mapa);
    mapa.fitBounds(ruta.getBounds(), { padding: [30, 30] });
  }

  document.querySelectorAll('[data-mapa-recorrido]').forEach(dibujar);
})();
