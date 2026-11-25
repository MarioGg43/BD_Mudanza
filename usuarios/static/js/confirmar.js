// Dos cosas para todos los formularios del sistema:
// 1. Las preguntas antes de una acción fuerte («¿Finalizar la mudanza?», «¿Dar de baja…?») con un
//    cartel propio, con los colores de la marca, en lugar de la ventanita gris del navegador.
//    En el HTML: <form data-confirmar="¿Finalizar la mudanza N° 12?" data-confirmar-detalle="…"
//    data-confirmar-boton="Finalizar" data-peligro>. Desde JavaScript: await confirmar({...}).
// 2. Que un formulario no se mande dos veces: al enviarlo, el botón se desactiva y dice
//    «Guardando…». Así un doble clic no registra dos pedidos iguales.
(function () {
  const estilo = document.createElement('style');
  estilo.textContent = `
    .cf-fondo{position:fixed;inset:0;z-index:2000;background:rgba(32,22,14,.45);display:flex;align-items:center;
      justify-content:center;padding:1rem;animation:cf-aparece .15s ease-out}
    .cf-caja{background:#fff;border-radius:16px;box-shadow:0 20px 50px rgba(0,0,0,.25);width:100%;max-width:460px;
      max-height:calc(100vh - 2rem);display:flex;flex-direction:column;overflow:hidden;font-family:inherit;color:#2b211a}
    .cf-caja.cf-ancha{max-width:600px}
    .cf-cabeza{display:flex;gap:.75rem;align-items:flex-start;padding:1.25rem 1.25rem .5rem}
    .cf-icono{flex:none;width:2.5rem;height:2.5rem;border-radius:50%;display:grid;place-items:center;font-size:1.15rem;
      background:#FFF0E2;color:#C04F00}
    .cf-peligro .cf-icono{background:#FDECEC;color:#C4170F}
    .cf-titulo{font-size:1.1rem;font-weight:700;margin:.35rem 0 0;line-height:1.3}
    .cf-cuerpo{padding:.25rem 1.25rem 1rem 4.5rem;font-size:.95rem;color:#5b4d42;overflow:auto}
    .cf-cuerpo.cf-sin-icono{padding-left:1.25rem}
    .cf-pie{display:flex;justify-content:flex-end;gap:.6rem;padding:.9rem 1.25rem;background:#FBF7F3;border-top:1px solid #efe6dd;flex-wrap:wrap}
    .cf-boton{border:0;border-radius:10px;padding:.6rem 1.1rem;font-weight:600;font-size:.95rem;cursor:pointer;font-family:inherit}
    .cf-boton:focus-visible{outline:3px solid #FF7A00;outline-offset:2px}
    .cf-no{background:#fff;color:#3b322b;border:1px solid #d6cbc0}
    .cf-no:hover{background:#f6efe8}
    .cf-si{color:#fff;background:linear-gradient(128deg,#D24600,#C73A06 55%,#B80B0B)}
    .cf-peligro .cf-si{background:#C4170F}
    .cf-si:hover{filter:brightness(1.05)}
    @keyframes cf-aparece{from{opacity:0}to{opacity:1}}
    .btn-guardando{opacity:.75;cursor:wait!important}
    .gira{display:inline-block;width:1em;height:1em;border:2px solid currentColor;border-right-color:transparent;
      border-radius:50%;animation:gira .7s linear infinite;vertical-align:-.15em;margin-right:.4em}
    @keyframes gira{to{transform:rotate(360deg)}}`;
  document.head.appendChild(estilo);

  /**
   * Muestra el cartel y devuelve una promesa: true si se eligió la acción, false si se canceló.
   * opciones: titulo, mensaje (texto), contenido (un nodo, para el resumen del pedido), boton,
   * cancelar, peligro (botón rojo), soloAceptar (un aviso con un solo botón), ancho.
   */
  function confirmar(opciones) {
    const o = typeof opciones === 'string' ? { titulo: opciones } : opciones;
    return new Promise((resolver) => {
      const antes = document.activeElement;
      const fondo = document.createElement('div');
      fondo.className = 'cf-fondo';
      const caja = document.createElement('div');
      caja.className = 'cf-caja' + (o.peligro ? ' cf-peligro' : '') + (o.ancho ? ' cf-ancha' : '');
      caja.setAttribute('role', o.soloAceptar ? 'alertdialog' : 'dialog');
      caja.setAttribute('aria-modal', 'true');
      const id = 'cf-' + Math.random().toString(36).slice(2);
      caja.setAttribute('aria-labelledby', id + '-t');

      const cabeza = document.createElement('div');
      cabeza.className = 'cf-cabeza';
      const icono = document.createElement('div');
      icono.className = 'cf-icono';
      icono.setAttribute('aria-hidden', 'true');
      icono.textContent = o.icono || (o.peligro ? '!' : o.soloAceptar ? 'i' : '?');
      const titulo = document.createElement('h2');
      titulo.className = 'cf-titulo';
      titulo.id = id + '-t';
      titulo.textContent = o.titulo || '¿Seguro?';
      cabeza.append(icono, titulo);

      const cuerpo = document.createElement('div');
      cuerpo.className = 'cf-cuerpo' + (o.contenido ? ' cf-sin-icono' : '');
      if (o.mensaje) {
        const p = document.createElement('p');
        p.style.margin = '0';
        p.style.whiteSpace = 'pre-line';
        p.textContent = o.mensaje;
        cuerpo.append(p);
      }
      if (o.contenido) cuerpo.append(o.contenido);

      const pie = document.createElement('div');
      pie.className = 'cf-pie';
      const no = document.createElement('button');
      no.type = 'button';
      no.className = 'cf-boton cf-no';
      no.textContent = o.cancelar || 'Cancelar';
      const si = document.createElement('button');
      si.type = 'button';
      si.className = 'cf-boton cf-si';
      si.textContent = o.soloAceptar ? (o.boton || 'Entendido') : (o.boton || 'Sí, continuar');
      if (!o.soloAceptar) pie.append(no);
      pie.append(si);
      caja.append(cabeza, cuerpo, pie);
      fondo.append(caja);
      document.body.append(fondo);
      document.body.style.overflow = 'hidden';

      function cerrar(resultado) {
        fondo.remove();
        document.body.style.overflow = '';
        document.removeEventListener('keydown', teclas, true);
        if (antes && antes.focus) antes.focus();
        resolver(resultado);
      }
      function teclas(e) {
        if (e.key === 'Escape') { e.preventDefault(); cerrar(false); }
        if (e.key === 'Tab') {  // el foco no se va del cartel
          const enfocables = [...caja.querySelectorAll('button, textarea, input, select, a[href]')].filter((x) => !x.disabled);
          const i = enfocables.indexOf(document.activeElement);
          e.preventDefault();
          enfocables[(i + (e.shiftKey ? -1 : 1) + enfocables.length) % enfocables.length].focus();
        }
      }
      no.addEventListener('click', () => cerrar(false));
      // el aviso de error se va apenas la persona escribe o elige algo
      cuerpo.addEventListener('input', () => { const x = cuerpo.querySelector('.cf-error'); if (x) x.remove(); });
      si.addEventListener('click', () => {
        // o.validar(): si devuelve un mensaje, el cartel no se cierra (por ejemplo, falta el motivo)
        const problema = o.validar ? o.validar() : '';
        if (problema) {
          let error = cuerpo.querySelector('.cf-error');
          if (!error) {
            error = document.createElement('p');
            error.className = 'cf-error';
            error.setAttribute('role', 'alert');
            error.style.cssText = 'margin:.6rem 0 0;color:#B42318;font-weight:600;font-size:.9rem';
            cuerpo.append(error);
          }
          error.textContent = problema;
          if (o.foco) o.foco.focus();
          return;
        }
        cerrar(true);
      });
      fondo.addEventListener('click', (e) => { if (e.target === fondo) cerrar(false); });
      document.addEventListener('keydown', teclas, true);
      // en las acciones peligrosas el foco arranca en «Cancelar», por si alguien aprieta Enter sin leer
      (o.foco || (o.peligro && !o.soloAceptar ? no : si)).focus();
    });
  }
  window.confirmar = confirmar;
  window.avisar = (titulo, mensaje) => confirmar({ titulo, mensaje, soloAceptar: true });

  /**
   * Arma el resumen de «revisá antes de guardar»: filas = [[título, línea principal, líneas chicas…]],
   * o {titulo, lineas, iguales: true} para una lista donde todas las líneas pesan lo mismo.
   * Una línea puede ser {texto, destacado: true} para resaltarla (por ejemplo, lo que cambia).
   */
  function resumen(filas, nota) {
    const caja = document.createElement('div');
    filas.forEach((fila, n) => {
      const [titulo, ...lineas] = Array.isArray(fila) ? fila : [fila.titulo, ...fila.lineas];
      const iguales = !Array.isArray(fila) && fila.iguales;
      const f = document.createElement('div');
      f.style.cssText = 'display:grid;grid-template-columns:7.5rem 1fr;gap:.75rem;padding:.55rem 0'
        + (n < filas.length - 1 ? ';border-bottom:1px solid #f0e8e0' : '');
      const t = document.createElement('div');
      t.style.cssText = 'font-weight:600;color:#7a6a5d';
      t.textContent = titulo;
      const v = document.createElement('div');
      lineas.filter(Boolean).forEach((l, i) => {
        const d = document.createElement('div');
        const texto = typeof l === 'string' ? l : l.texto;
        d.textContent = texto;
        if (i && !iguales) d.style.cssText = 'font-size:.85rem;color:#7a6a5d';
        if (l.destacado) d.style.cssText = 'font-weight:700;color:#C04F00';
        v.append(d);
      });
      f.append(t, v);
      caja.append(f);
    });
    if (nota) {
      const p = document.createElement('p');
      p.style.cssText = 'margin:.75rem 0 0;font-size:.85rem;color:#7a6a5d';
      p.textContent = nota;
      caja.append(p);
    }
    return caja;
  }
  window.resumenParaRevisar = resumen;

  // ---- anular o cancelar en un cartel, con motivos rápidos que completan el texto ----
  // <a href="/pedidos/12/anular/" data-motivo-url="…" data-motivo-titulo="…" data-motivo-detalle="…"
  //    data-motivos='["Duplicado", …]' data-motivo-boton="Sí, anular">. Sin JavaScript sigue abriendo la pantalla.
  function token(link) {
    if (link && link.dataset.token) return link.dataset.token;
    const m = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
    const campo = document.querySelector('[name="csrfmiddlewaretoken"]');
    return m ? decodeURIComponent(m[1]) : campo ? campo.value : '';
  }
  document.addEventListener('click', async (e) => {
    const link = e.target.closest && e.target.closest('a[data-motivo-url]');
    if (!link || e.ctrlKey || e.metaKey || e.shiftKey || e.button !== 0) return;
    e.preventDefault();
    const caja = document.createElement('div');
    const etiqueta = document.createElement('label');
    etiqueta.textContent = link.dataset.motivoPregunta || 'Motivo';
    etiqueta.style.cssText = 'display:block;font-weight:600;margin:.75rem 0 .4rem;color:#2b211a';
    const chips = document.createElement('div');
    chips.style.cssText = 'display:flex;flex-wrap:wrap;gap:.4rem;margin-bottom:.6rem';
    const texto = document.createElement('textarea');
    texto.rows = 3;
    texto.maxLength = 200;
    texto.minLength = 5;
    texto.dataset.validar = 'texto';
    texto.placeholder = 'Tocá un motivo de arriba o escribí el tuyo';
    texto.id = 'motivo-' + Date.now();
    etiqueta.htmlFor = texto.id;
    texto.style.cssText = 'width:100%;border:1px solid #d6cbc0;border-radius:10px;padding:.6rem .7rem;font:inherit;resize:vertical';
    const contador = document.createElement('div');
    contador.style.cssText = 'text-align:right;font-size:.78rem;color:#8a7a6d;margin-top:.2rem';
    const contar = () => { contador.textContent = `${texto.value.length} de 200`; };
    texto.addEventListener('input', contar);
    contar();
    JSON.parse(link.dataset.motivos || '[]').forEach((m) => {
      const b = document.createElement('button');
      b.type = 'button';
      b.textContent = m;
      b.style.cssText = 'border:1px solid #F3C9A5;background:#FFF6EE;color:#8a3d00;border-radius:999px;padding:.3rem .75rem;font:inherit;font-size:.85rem;cursor:pointer';
      b.addEventListener('click', () => {
        texto.value = m;
        texto.dispatchEvent(new Event('input', { bubbles: true }));
        texto.focus();
      });
      chips.append(b);
    });
    if (link.dataset.motivoDetalle) {
      const p = document.createElement('p');
      p.style.margin = '0';
      p.textContent = link.dataset.motivoDetalle;
      caja.append(p);
    }
    caja.append(etiqueta, chips, texto, contador);
    const letras = (t) => (t.match(/[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]/g) || []).length;
    const ok = await confirmar({
      titulo: link.dataset.motivoTitulo, contenido: caja, peligro: true, foco: texto,
      boton: link.dataset.motivoBoton || 'Sí, anular', cancelar: 'Volver',
      validar: () => {
        const v = texto.value.trim();
        if (v.length < 5) return 'Contá el motivo (5 caracteres o más).';
        if (letras(v) < 3 || /([A-Za-zÁÉÍÓÚÜÑáéíóúüñ])\1{3,}/i.test(v)) return 'Escribí el motivo con palabras.';
        return '';
      },
    });
    if (!ok) return;
    const form = document.createElement('form');
    form.method = 'post';
    form.action = link.dataset.motivoUrl;
    form.hidden = true;
    for (const [nombre, valor] of [['csrfmiddlewaretoken', token(link)], ['motivo', texto.value.trim()]]) {
      const i = document.createElement('input');
      i.type = 'hidden';
      i.name = nombre;
      i.value = valor;
      form.append(i);
    }
    document.body.append(form);
    form.submit();
  });

  // ---- 1. formularios con data-confirmar: primero se pregunta, después se envía ----
  document.addEventListener('submit', (e) => {
    const form = e.target;
    if (!(form instanceof HTMLFormElement)) return;
    if (form.dataset.enviando) {  // ya se está enviando: el segundo clic no hace nada
      e.preventDefault();
      e.stopImmediatePropagation();
      return;
    }
    const revisar = form.dataset.revisar !== undefined && typeof form.armarResumen === 'function';
    if ((form.dataset.confirmar === undefined && !revisar) || form.dataset.confirmado) return;
    e.preventDefault();
    e.stopImmediatePropagation();
    const quien = e.submitter;
    // <form data-revisar>: la pantalla arma el resumen con form.armarResumen() → {titulo, filas, nota, boton}
    const r = revisar ? form.armarResumen() : null;
    confirmar(r ? {
      titulo: r.titulo, contenido: resumen(r.filas, r.nota), boton: r.boton, cancelar: 'Corregir', ancho: true, icono: '✓',
    } : {
      titulo: form.dataset.confirmar,
      mensaje: form.dataset.confirmarDetalle || '',
      boton: form.dataset.confirmarBoton,
      peligro: form.dataset.peligro !== undefined,
    }).then((ok) => {
      if (!ok) return;
      form.dataset.confirmado = '1';
      form.requestSubmit(quien && quien.form === form ? quien : undefined);
      delete form.dataset.confirmado;
    });
  }, true);

  // ---- 2. al enviar de verdad: el botón queda desactivado y dice qué está pasando ----
  const TEXTOS = [
    [/iniciar sesión|entrar/i, 'Ingresando…'], [/crear (mi )?cuenta/i, 'Creando la cuenta…'],
    [/confirmar/i, 'Confirmando…'], [/finalizar/i, 'Finalizando…'], [/empezamos|terminamos/i, 'Guardando…'],
    [/dar de baja|eliminar|anular|cancelar/i, 'Un momento…'], [/registrar|guardar/i, 'Guardando…'],
  ];
  document.addEventListener('submit', (e) => {
    const form = e.target;
    if (!(form instanceof HTMLFormElement) || e.defaultPrevented) return;
    if ((form.method || 'get').toLowerCase() !== 'post') return;  // los filtros (GET) no hacen falta
    form.dataset.enviando = '1';
    // se desactiva un instante después: si se desactivara ya, el botón no viajaría con el formulario
    setTimeout(() => {
      form.querySelectorAll('button[type="submit"], button:not([type]), input[type="submit"]').forEach((b) => {
        if (b.disabled) return;
        b.dataset.textoOriginal = b.innerHTML;
        b.disabled = true;
        b.classList.add('btn-guardando');
        const texto = (TEXTOS.find(([re]) => re.test(b.textContent)) || [null, 'Un momento…'])[1];
        b.innerHTML = '<span class="gira" aria-hidden="true"></span>';
        b.append(texto);
      });
    }, 0);
    // si la página no cambia (por ejemplo, una descarga), a los 10 segundos se puede volver a usar
    setTimeout(() => liberar(form), 10000);
  });

  function liberar(form) {
    delete form.dataset.enviando;
    form.querySelectorAll('.btn-guardando').forEach((b) => {
      b.disabled = false;
      b.classList.remove('btn-guardando');
      if (b.dataset.textoOriginal !== undefined) b.innerHTML = b.dataset.textoOriginal;
    });
  }
  // al volver con «Atrás» del navegador la página puede quedar como estaba: se liberan los botones
  window.addEventListener('pageshow', (e) => { if (e.persisted) document.querySelectorAll('form').forEach(liberar); });

  // ---- 3. cambios sin guardar: si alguien está a mitad de un formulario y se va, se le pregunta ----
  // Cuenta en los formularios que guardan algo (POST); no en los filtros ni en los que dicen data-sin-aviso.
  const cambiados = new Set();
  function cuenta(form) {
    return form && (form.method || '').toLowerCase() === 'post' && form.dataset.sinAviso === undefined;
  }
  ['input', 'change'].forEach((tipo) => document.addEventListener(tipo, (e) => {
    const c = e.target;
    if (!c.form || c.type === 'hidden' || !e.isTrusted) return;
    if (cuenta(c.form)) cambiados.add(c.form);
  }, true));
  document.addEventListener('submit', (e) => { if (!e.defaultPrevented) cambiados.delete(e.target); });
  const hayCambios = () => [...cambiados].some((f) => document.contains(f) && !f.dataset.enviando && !f.closest('.hidden, [hidden]'));

  // un enlace del sistema (el menú, «Volver»…): el cartel propio
  document.addEventListener('click', async (e) => {
    const a = e.target.closest && e.target.closest('a[href]');
    if (!a || !hayCambios() || e.defaultPrevented || e.ctrlKey || e.metaKey || e.shiftKey || e.button !== 0) return;
    if (a.target === '_blank' || a.hasAttribute('download') || a.dataset.motivoUrl !== undefined || a.dataset.campanita !== undefined) return;
    const destino = new URL(a.href, location.href);
    if (destino.origin !== location.origin || (destino.pathname === location.pathname && destino.hash)) return;
    e.preventDefault();
    const salir = await confirmar({
      titulo: '¿Salir sin guardar?', mensaje: 'Tenés cambios sin guardar en esta pantalla. Si salís ahora, se pierden.',
      boton: 'Salir sin guardar', cancelar: 'Seguir editando', peligro: true,
    });
    if (salir) { cambiados.clear(); location.href = a.href; }
  });
  // cerrar la pestaña, recargar o «Atrás»: el navegador solo deja mostrar su propio aviso
  window.addEventListener('beforeunload', (e) => {
    if (!hayCambios()) return;
    e.preventDefault();
    e.returnValue = '';
  });
})();
