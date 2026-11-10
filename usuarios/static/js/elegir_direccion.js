// Las direcciones del pedido y su punto exacto en el mapa.
//
// 1. «Elegir en el mapa»: la persona toca el lugar (o «Estoy acá») y Django le devuelve la dirección
//    de ese punto (OpenRouteService). Se puede corregir antes de usarla. Se guarda la dirección y
//    también el punto (latitud y longitud, en campos ocultos del formulario).
// 2. Si la escribe a mano, al salir del campo se busca dónde cae y se muestra en un mapa chico:
//    «¿Es acá?». Con «Sí» se guarda ese punto; con «No» se abre el mapa para marcarlo.
// Si después vuelve a escribir la dirección, el punto se borra: ya no corresponde.
(function () {
  const modalEl = document.getElementById('modalMapa');
  if (!modalEl) return;
  const SALTA = [-24.7821, -65.4117];
  const lienzo = modalEl.querySelector('[data-mapa-elegir]');
  const campoDireccion = document.getElementById('direccionElegida');
  const estado = modalEl.querySelector('[data-mapa-estado]');
  const botonUsar = modalEl.querySelector('[data-usar-direccion]');
  const AYUDA = estado.textContent;
  const CAPA = {
    maxZoom: 19,
    referrerPolicy: 'strict-origin-when-cross-origin', // sin esto OpenStreetMap bloquea los mapas
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> · openrouteservice.org',
  };
  let mapa = null, marcador = null, destino = null, consulta = 0, puntoElegido = null;

  // ---------------------------------------------------------------- el punto de cada dirección
  function ocultos(campo) {
    const lado = campo.name; // origen o destino
    return { lat: document.getElementById('id_lat_' + lado), lon: document.getElementById('id_lon_' + lado) };
  }
  function guardarPunto(campo, punto) {
    const o = ocultos(campo);
    o.lat.value = punto ? punto.lat.toFixed(6) : '';
    o.lon.value = punto ? punto.lon.toFixed(6) : '';
  }
  function puntoGuardado(campo) {
    const o = ocultos(campo);
    return o.lat.value && o.lon.value ? { lat: Number(o.lat.value), lon: Number(o.lon.value) } : null;
  }

  // ---------------------------------------------------------------- la vista previa debajo del campo
  const previas = {};
  function previaDe(campo) {
    if (previas[campo.id]) return previas[campo.id];
    const caja = document.querySelector('[data-previa-de="' + campo.id + '"]');
    if (!caja) return null;
    previas[campo.id] = {
      caja, mapa: null, marcador: null, propuesto: null, pedido: 0,
      mensaje: caja.querySelector('[data-previa-mensaje]'), botones: caja.querySelector('[data-previa-botones]'),
      lienzo: caja.querySelector('[data-mapa-mini]'),
    };
    caja.querySelector('[data-es-aca]').addEventListener('click', () => {
      const p = previas[campo.id];
      guardarPunto(campo, p.propuesto);
      mostrarMarcado(campo, p.propuesto, 'Ubicación confirmada.');
    });
    caja.querySelector('[data-no-es-aca]').addEventListener('click', () => {
      abrirMapa(campo, previas[campo.id].propuesto);
    });
    return previas[campo.id];
  }

  function dibujarMini(p, punto) {
    p.caja.hidden = false;
    if (typeof L === 'undefined') return;
    if (!p.mapa) {
      p.mapa = L.map(p.lienzo, { zoomControl: false, attributionControl: false, dragging: false,
                                 scrollWheelZoom: false, doubleClickZoom: false, boxZoom: false,
                                 keyboard: false, touchZoom: false });
      L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', CAPA).addTo(p.mapa);
    }
    p.mapa.invalidateSize();
    p.mapa.setView([punto.lat, punto.lon], 16);
    if (p.marcador) p.marcador.setLatLng([punto.lat, punto.lon]);
    else p.marcador = L.marker([punto.lat, punto.lon]).addTo(p.mapa);
  }

  function mostrarMarcado(campo, punto, texto) {
    const p = previaDe(campo);
    if (!p || !punto) return;
    p.mensaje.innerHTML = '';
    const icono = document.createElement('i');
    icono.className = 'bi bi-geo-alt-fill text-success me-1';
    p.mensaje.append(icono, texto || 'Ubicación marcada en el mapa.');
    p.botones.hidden = true;
    dibujarMini(p, punto);
  }

  function ocultarPrevia(campo) {
    const p = previaDe(campo);
    if (p) { p.caja.hidden = true; p.pedido++; }
  }

  async function proponer(campo) {
    const p = previaDe(campo);
    const texto = campo.value.trim();
    if (!p || puntoGuardado(campo) || texto.length < 5) return;
    const esta = ++p.pedido;
    p.caja.hidden = false;
    p.botones.hidden = true;
    p.mensaje.textContent = 'Buscando dónde queda…';
    let datos;
    try {
      const url = modalEl.dataset.urlUbicar + '?' + new URLSearchParams({ direccion: texto });
      datos = await (await fetch(url, { headers: { Accept: 'application/json' } })).json();
    } catch (e) {
      datos = { ok: false, error: 'No se pudo buscar la dirección.' };
    }
    if (esta !== p.pedido) return; // escribió otra cosa mientras tanto
    if (!datos.ok) {
      p.mensaje.textContent = (datos.error || 'No encontramos la dirección.') + ' Podés marcarla en el mapa.';
      p.botones.hidden = false;
      p.caja.querySelector('[data-es-aca]').hidden = true;
      p.propuesto = null;
      if (p.mapa) p.lienzo.hidden = true;
      return;
    }
    p.propuesto = { lat: datos.lat, lon: datos.lon };
    p.lienzo.hidden = false;
    p.caja.querySelector('[data-es-aca]').hidden = false;
    p.mensaje.innerHTML = '';
    const b = document.createElement('b');
    b.textContent = '¿Es acá? ';
    p.mensaje.append(b, 'Lo ubicamos en ' + datos.etiqueta + '.'); // texto del servicio: nunca como HTML
    p.botones.hidden = false;
    dibujarMini(p, p.propuesto);
  }

  // ---------------------------------------------------------------- la ventana con el mapa grande
  function avisar(texto, esError) {
    estado.textContent = texto;
    estado.classList.toggle('text-danger', Boolean(esError));
  }

  function prepararMapa() {
    if (mapa) return;
    mapa = L.map(lienzo).setView(SALTA, 13);
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', CAPA).addTo(mapa);
    mapa.on('click', (e) => elegir(e.latlng.lat, e.latlng.lng));
  }

  async function elegir(lat, lon) {
    if (marcador) marcador.setLatLng([lat, lon]);
    else marcador = L.marker([lat, lon]).addTo(mapa);
    puntoElegido = { lat, lon };
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

  // abre el mapa para un campo; si ya hay un punto (guardado o propuesto), arranca ahí
  let centrar = null;
  function abrirMapa(campo, desde) {
    destino = campo;
    const boton = document.querySelector('[data-elegir-en-mapa="' + campo.id + '"]');
    modalEl.querySelector('.modal-title').textContent = 'Elegí «' + (boton ? boton.dataset.titulo : '') + '» en el mapa';
    campoDireccion.value = '';
    campoDireccion.disabled = true;
    botonUsar.disabled = true;
    puntoElegido = null;
    avisar(AYUDA);
    if (marcador) { marcador.remove(); marcador = null; }
    centrar = desde || puntoGuardado(campo);
    bootstrap.Modal.getOrCreateInstance(modalEl).show();
  }

  document.querySelectorAll('[data-elegir-en-mapa]').forEach((boton) => {
    boton.addEventListener('click', () => abrirMapa(document.getElementById(boton.dataset.elegirEnMapa)));
  });

  // el mapa se arma cuando la ventana ya se ve: si no, Leaflet calcula mal el tamaño
  modalEl.addEventListener('shown.bs.modal', () => {
    prepararMapa();
    mapa.invalidateSize();
    if (centrar) mapa.setView([centrar.lat, centrar.lon], 17);
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
    destino.dispatchEvent(new Event('input', { bubbles: true }));  // esto borra el punto viejo…
    destino.dispatchEvent(new Event('change', { bubbles: true }));
    guardarPunto(destino, puntoElegido);                            // …y acá se guarda el nuevo
    mostrarMarcado(destino, puntoElegido, 'Ubicación marcada en el mapa.');
    bootstrap.Modal.getInstance(modalEl).hide();
    destino.focus();
  });

  // ---------------------------------------------------------------- los campos de dirección
  document.querySelectorAll('[data-previa-de]').forEach((caja) => {
    const campo = document.getElementById(caja.dataset.previaDe);
    if (!campo) return;
    campo.addEventListener('input', (e) => {
      if (!e.isTrusted) return; // lo escribió el mapa, no la persona
      guardarPunto(campo, null);
      ocultarPrevia(campo);
    });
    campo.addEventListener('change', (e) => { if (e.isTrusted) proponer(campo); });
    // al modificar un pedido (o si el formulario volvió con errores), el punto que ya tenía
    window.addEventListener('load', () => {
      const punto = puntoGuardado(campo);
      if (punto) mostrarMarcado(campo, punto, 'Ubicación marcada en el mapa.');
    });
  });
})();
