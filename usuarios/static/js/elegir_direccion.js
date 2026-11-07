// «Elegir en el mapa» del formulario del pedido: la persona toca el lugar (o «Estoy acá») y Django
// le devuelve la dirección de ese punto (OpenRouteService). Se puede corregir antes de usarla.
(function () {
  const modalEl = document.getElementById('modalMapa');
  if (!modalEl) return;
  const SALTA = [-24.7821, -65.4117];
  const lienzo = modalEl.querySelector('[data-mapa-elegir]');
  const campoDireccion = document.getElementById('direccionElegida');
  const estado = modalEl.querySelector('[data-mapa-estado]');
  const botonUsar = modalEl.querySelector('[data-usar-direccion]');
  const AYUDA = estado.textContent;
  let mapa = null, marcador = null, destino = null, consulta = 0;

  function avisar(texto, esError) {
    estado.textContent = texto;
    estado.classList.toggle('text-danger', Boolean(esError));
  }

  function prepararMapa() {
    if (mapa) return;
    mapa = L.map(lienzo).setView(SALTA, 13);
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      referrerPolicy: 'strict-origin-when-cross-origin', // sin esto OpenStreetMap bloquea los mapas
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> · openrouteservice.org',
    }).addTo(mapa);
    mapa.on('click', (e) => elegir(e.latlng.lat, e.latlng.lng));
  }

  async function elegir(lat, lon) {
    if (marcador) marcador.setLatLng([lat, lon]);
    else marcador = L.marker([lat, lon]).addTo(mapa);
    const esta = ++consulta; // si toca otro punto antes de que llegue la respuesta, vale el último
    campoDireccion.disabled = true;
    botonUsar.disabled = true;
    avisar('Buscando la dirección…');
    let datos;
    try {
      const url = modalEl.dataset.urlDireccion + '?' + new URLSearchParams({ lat: lat.toFixed(6), lon: lon.toFixed(6) });
      datos = await (await fetch(url, { headers: { Accept: 'application/json' } })).json();
    } catch (e) {
      datos = { ok: false, error: 'No se pudo consultar la dirección.' };
    }
    if (esta !== consulta) return;
    if (!datos.ok) {
      avisar(datos.error, true);
      return;
    }
    campoDireccion.value = datos.direccion;
    campoDireccion.disabled = false;
    botonUsar.disabled = false;
    avisar(AYUDA);
  }

  // cada botón del mapa dice qué campo completa (Desde o Hasta)
  document.querySelectorAll('[data-elegir-en-mapa]').forEach((boton) => {
    boton.addEventListener('click', () => {
      destino = document.getElementById(boton.dataset.elegirEnMapa);
      modalEl.querySelector('.modal-title').textContent = 'Elegí «' + boton.dataset.titulo + '» en el mapa';
      campoDireccion.value = '';
      campoDireccion.disabled = true;
      botonUsar.disabled = true;
      avisar(AYUDA);
      if (marcador) { marcador.remove(); marcador = null; }
      bootstrap.Modal.getOrCreateInstance(modalEl).show();
    });
  });

  // el mapa se arma cuando la ventana ya se ve: si no, Leaflet calcula mal el tamaño
  modalEl.addEventListener('shown.bs.modal', () => {
    prepararMapa();
    mapa.invalidateSize();
  });

  modalEl.querySelector('[data-mi-ubicacion]').addEventListener('click', () => {
    if (!navigator.geolocation) {
      avisar('Este navegador no comparte la ubicación.', true);
      return;
    }
    avisar('Buscando dónde estás…');
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        mapa.setView([pos.coords.latitude, pos.coords.longitude], 17);
        elegir(pos.coords.latitude, pos.coords.longitude);
      },
      () => avisar('No se pudo obtener tu ubicación. Tocá el lugar en el mapa.', true),
      { enableHighAccuracy: true, timeout: 10000 });
  });

  botonUsar.addEventListener('click', () => {
    const texto = campoDireccion.value.trim();
    if (!texto || !destino) return;
    destino.value = texto.slice(0, 200);
    destino.dispatchEvent(new Event('input', { bubbles: true }));
    destino.dispatchEvent(new Event('change', { bubbles: true }));
    bootstrap.Modal.getInstance(modalEl).hide();
    destino.focus();
  });
})();
