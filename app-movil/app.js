/* Arranque de la app: rutas, permisos por rol, dibujo de pantallas y eventos. */
(function (root) {
  'use strict';
  const L = root.Logic, UI = root.UI, Screens = root.Screens;

  const ADM = ['Administrador'], EMP = ['Chofer', 'Ayudante de Carga'], CLI = ['Cliente'];
  // [ruta, pantalla, quién entra]: null = sin sesión, 'any' = cualquier usuario, 'clave' = cambio de clave pendiente
  const ROUTES = [
    ['splash', 'splash', null], ['login', 'login', null], ['registro', 'registro', null], ['recuperar', 'recuperar', null],
    ['cambiar-clave', 'cambiarClave', 'clave'], ['perfil', 'perfil', 'any'],
    ['cli/inicio', 'cliInicio', CLI], ['cli/pedir', 'cliPedir', CLI], ['cli/enviado/:id', 'cliEnviado', CLI],
    ['cli/pedidos', 'cliPedidos', CLI], ['cli/pedido/:id', 'cliPedido', CLI],
    ['adm/panel', 'admPanel', ADM], ['adm/pedidos', 'admPedidos', ADM], ['adm/pedido/:id', 'admPedido', ADM],
    ['adm/asignar/:id', 'admAsignar', ADM], ['adm/cobro/:id', 'admCobro', ADM],
    ['adm/vehiculos', 'admVehiculos', ADM], ['adm/vehiculo/:id', 'admVehiculo', ADM], ['adm/vehiculo-form/:id', 'admVehiculoForm', ADM],
    ['adm/usuarios', 'admUsuarios', ADM], ['adm/usuario/:id', 'admUsuario', ADM], ['adm/usuario-nuevo', 'admUsuarioNuevo', ADM],
    ['adm/servicios', 'admServicios', ADM], ['adm/servicio-form/:id', 'admServicioForm', ADM],
    ['emp/mudanzas', 'empMudanzas', EMP], ['emp/mudanza/:id', 'empMudanza', EMP],
  ];

  function match(path) {
    const seg = String(path || '').split('/');
    for (const [pat, screen, roles] of ROUTES) {
      const ps = pat.split('/');
      if (ps.length !== seg.length) continue;
      const params = {};
      let ok = true;
      for (let i = 0; i < ps.length; i++) {
        if (ps[i].charAt(0) === ':') params[ps[i].slice(1)] = decodeURIComponent(seg[i]);
        else if (ps[i] !== seg[i]) { ok = false; break; }
      }
      if (ok) return { path: String(path), screen, roles, params };
    }
    return null;
  }

  function homeOf(S) {
    const u = S.usuarioActual();
    if (!u) return S.session.pendiente ? 'cambiar-clave' : 'login';
    if (u.rol === 'Administrador') return 'adm/panel';
    if (u.rol === 'Cliente') return 'cli/inicio';
    return 'emp/mudanzas';
  }

  function resolve(S, path) {
    const u = S.usuarioActual();
    const m = match(path);
    if (!m) return match(homeOf(S));
    if (m.roles === null) return u ? match(homeOf(S)) : m;
    if (m.roles === 'clave') return u || S.session.pendiente ? m : match('login');
    if (!u) return match('login');
    if (m.roles === 'any' || m.roles.includes(u.rol)) return m;
    return match(homeOf(S));
  }

  function freshUi() {
    return { form: null, overlay: null, toast: null, q: {}, f: {}, draft: null, x: {} };
  }

  // Contexto que recibe cada pantalla. En la galería se arma con acciones inertes.
  function makeCtx(S, ui, route, api) {
    const noop = () => {};
    api = api || {};
    return {
      S, L, UI, ui, route, params: route.params, user: S.usuarioActual(), hoy: S.hoy(), live: !!api.live,
      val(id, def) {
        const f = ui.form;
        return f && f.values && Object.prototype.hasOwnProperty.call(f.values, id) ? f.values[id] : def;
      },
      err(id) { const f = ui.form; return (f && f.errores && f.errores[id]) || null; },
      go: api.go || noop, back: api.back || noop, refresh: api.refresh || noop, toast: api.toast || noop,
      overlay: api.overlay || noop, closeOverlay: api.closeOverlay || noop, entrar: api.entrar || noop,
      scrollTop: api.scrollTop || noop,
      // Maneja el resultado de una acción del store: si salió bien corre `ok`,
      // si no, deja los errores para que el formulario los muestre.
      result(r, name, values, ok) {
        if (r.ok) { ui.form = null; if (ok) ok(r); return true; }
        if (name) ui.form = { name, values: values || {}, errores: r.errores || null, error: r.error || null };
        else if (api.toast) api.toast(r.error || 'Revisá los datos.', 'error');
        if (api.refresh && name) api.refresh();
        return false;
      },
    };
  }

  function overlayHtml(ctx) {
    const o = ctx.ui.overlay;
    if (!o) return '';
    const scrim = '<div class="scrim" data-act="cerrar"></div>';
    if (o.kind === 'confirm') {
      return scrim + '<div class="dialog' + (o.danger ? ' danger' : '') + '" role="alertdialog" aria-modal="true" aria-labelledby="dlg-t">' +
        '<div class="ic">' + UI.icon(o.icon || (o.danger ? 'alert' : 'info'), 26) + '</div>' +
        '<h3 id="dlg-t">' + UI.esc(o.title) + '</h3><p>' + o.text + '</p>' +
        '<div class="row-2"><button class="btn ghost" data-act="cerrar">Cancelar</button>' +
        '<button class="btn ' + (o.danger ? 'danger' : 'primary') + '" data-act="' + o.act + '"' + UI.attrs(o.data) + '>' + UI.esc(o.confirm) + '</button></div></div>';
    }
    const scr = Screens[ctx.route.screen];
    const body = scr.sheets && scr.sheets[o.name] ? scr.sheets[o.name](ctx, o.data || {}) : '';
    return scrim + '<div class="sheet" role="dialog" aria-modal="true"><div class="handle"></div>' + body + '</div>';
  }

  function toneOf(scr, ctx) {
    return typeof scr.tone === 'function' ? scr.tone(ctx) : scr.tone || 'dark';
  }

  function renderInto(appEl, phoneEl, S, ui, route, api) {
    const scr = Screens[route.screen];
    const ctx = makeCtx(S, ui, route, api);
    appEl.innerHTML = UI.statusbar() + scr.render(ctx) + overlayHtml(ctx) + toastHtml(ui);
    phoneEl.classList.toggle('sb-light', toneOf(scr, ctx) === 'light');
    phoneEl.classList.toggle('no-tabs', !appEl.querySelector('.tabbar, .bottom-bar'));
    return { scr, ctx };
  }

  function toastHtml(ui) {
    const t = ui.toast;
    if (!t) return '';
    return '<div class="toast ' + t.kind + '" role="status">' + UI.icon(t.kind === 'error' ? 'alert' : 'check', 18) +
      '<span>' + UI.esc(t.text) + '</span></div>';
  }

  root.AppCore = { makeCtx, overlayHtml, renderInto, match, freshUi };

  // ---------------- app en vivo ----------------
  function boot() {
    let storage = null;
    try { storage = root.localStorage; } catch (e) { storage = null; }
    const S = root.createStore(storage);
    S.load();

    const appEl = document.getElementById('app');
    const phoneEl = document.getElementById('phone');
    const App = { route: null, stack: [], ui: freshUi(), lastPath: null, toastN: 0, keepScroll: true };

    const api = {
      live: true,
      go, back, refresh: render, toast, overlay: openOverlay, closeOverlay, entrar,
      scrollTop() { App.keepScroll = false; },
    };

    function render() {
      const cont = appEl.querySelector('.content');
      const scroll = cont && App.keepScroll && App.lastPath === App.route.path ? cont.scrollTop : 0;
      const act = document.activeElement;
      const focoId = act && appEl.contains(act) && act.id ? act.id : null;
      const caret = focoId && typeof act.selectionStart === 'number' ? act.selectionStart : null;
      const { scr, ctx } = renderInto(appEl, phoneEl, S, App.ui, App.route, api);
      const nuevo = appEl.querySelector('.content');
      if (nuevo) nuevo.scrollTop = scroll;
      if (focoId) {
        const el = document.getElementById(focoId);
        if (el) { el.focus({ preventScroll: true }); if (caret != null && el.setSelectionRange) { try { el.setSelectionRange(caret, caret); } catch (e) { /* tipo sin cursor */ } } }
      }
      App.lastPath = App.route.path;
      App.keepScroll = true;
      if (scr.after) scr.after(appEl, ctx);
      syncDemo();
    }

    function go(path, opts) {
      opts = opts || {};
      const m = resolve(S, path);
      if (opts.clear) App.stack = [];
      else if (App.route && !opts.replace && App.route.path !== m.path) App.stack.push(App.route.path);
      App.route = m;
      App.ui.form = null; App.ui.overlay = null; App.ui.x = {};
      App.keepScroll = false;
      render();
      const h = appEl.querySelector('h1, h2');
      if (h && opts.focus !== false) { h.setAttribute('tabindex', '-1'); h.focus({ preventScroll: true }); }
    }

    function back() {
      let prev = App.stack.pop();
      while (prev && resolve(S, prev).path !== prev) prev = App.stack.pop();
      if (!prev) { go(homeOf(S), { clear: true }); return; }
      App.route = resolve(S, prev);
      App.ui.form = null; App.ui.overlay = null; App.ui.x = {};
      App.keepScroll = false;
      render();
    }

    function toast(text, kind) {
      const id = ++App.toastN;
      App.ui.toast = { text, kind: kind || 'ok', id };
      const viejo = appEl.querySelector('.toast');
      if (viejo) viejo.remove();
      appEl.insertAdjacentHTML('beforeend', toastHtml(App.ui));
      setTimeout(() => {
        if (App.ui.toast && App.ui.toast.id === id) {
          App.ui.toast = null;
          const t = appEl.querySelector('.toast');
          if (t) t.remove();
        }
      }, 3200);
    }

    function openOverlay(o) { App.ui.overlay = o; App.ui.form = null; render(); }
    function closeOverlay() { App.ui.overlay = null; App.ui.form = null; render(); }

    function entrar(r, mensaje) {
      if (r.cambiarClave) { go('cambiar-clave', { clear: true }); return; }
      go(homeOf(S), { clear: true });
      const u = S.usuarioActual();
      toast(mensaje || ('Hola, ' + u.nombre + '. Entraste como ' + u.rol.toLowerCase() + '.'));
    }

    const GLOBAL = {
      cerrar() { closeOverlay(); },
      'ver-clave'(ctx, el) {
        const input = el.closest('.input').querySelector('input');
        const ver = input.type === 'password';
        input.type = ver ? 'text' : 'password';
        el.innerHTML = UI.icon(ver ? 'eyeOff' : 'eye', 18);
        el.setAttribute('aria-label', ver ? 'Ocultar contraseña' : 'Mostrar contraseña');
      },
      filtro(ctx, el) { App.ui.f[el.dataset.k] = el.dataset.v; App.keepScroll = false; render(); },
      logout() { S.logout(); App.ui = freshUi(); go('login', { clear: true }); toast('Cerraste sesión.'); },
      'entrar-como'(ctx, el) {
        const r = S.entrarComo(Number(el.dataset.dni));
        if (r.ok) entrar(r); else toast(r.error, 'error');
      },
      galeria() { mostrarGaleria(); },
      'reiniciar-ok'() { S.reset(); App.ui = freshUi(); go('splash', { clear: true }); toast('Volvimos a los datos de ejemplo.'); },
    };

    function ctxActual() { return makeCtx(S, App.ui, App.route, api); }

    appEl.addEventListener('click', (e) => {
      const t = e.target.closest('[data-go], [data-back], [data-act]');
      if (!t || !appEl.contains(t) || t.disabled) return;
      if (t.dataset.go) {
        e.preventDefault();
        go(t.dataset.go, { replace: 'replace' in t.dataset, clear: 'clear' in t.dataset });
      } else if ('back' in t.dataset) {
        e.preventDefault();
        back();
      } else if (t.dataset.act) {
        e.preventDefault();
        const name = t.dataset.act;
        const scr = Screens[App.route.screen];
        const fn = (scr.acts && scr.acts[name]) || GLOBAL[name];
        if (fn) fn(ctxActual(), t);
      }
    });

    appEl.addEventListener('submit', (e) => {
      const f = e.target.closest('form[data-form]');
      if (!f) return;
      e.preventDefault();
      const scr = Screens[App.route.screen];
      const fn = scr.forms && scr.forms[f.dataset.form];
      if (!fn) return;
      const fd = new FormData(f);
      const values = {};
      fd.forEach((v, k) => { values[k] = k in values ? [].concat(values[k], v) : v; });
      fn(ctxActual(), values, fd, f);
    });

    function onLive(e) {
      const t = e.target.closest('[data-live]');
      if (!t || !appEl.contains(t)) return;
      const name = t.dataset.live;
      if (name === 'buscar') {
        if (e.type !== 'input') return;
        App.ui.q[t.dataset.k] = t.value;
        render();
        return;
      }
      const scr = Screens[App.route.screen];
      const fn = scr.live && scr.live[name];
      if (fn) fn(ctxActual(), t, e);
    }
    appEl.addEventListener('input', onLive);
    appEl.addEventListener('change', onLive);

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && App.ui.overlay) closeOverlay();
    });

    // ---------- panel de la demo (escritorio) ----------
    const demo = document.getElementById('demo');
    function syncDemo() {
      if (!demo) return;
      const u = S.usuarioActual();
      const quien = demo.querySelector('[data-quien]');
      if (quien) quien.textContent = u ? u.nombre + ' ' + u.apellido + ' · ' + u.rol : 'Nadie inició sesión';
    }
    if (demo) {
      demo.addEventListener('click', (e) => {
        const b = e.target.closest('button');
        if (!b) return;
        if (b.dataset.dni) {
          S.logout();
          App.ui = freshUi();
          const r = S.entrarComo(Number(b.dataset.dni));
          if (r.ok) entrar(r);
        } else if (b.dataset.demo === 'galeria') {
          mostrarGaleria();
        } else if (b.dataset.demo === 'salir') {
          GLOBAL.logout();
        } else if (b.dataset.demo === 'reiniciar') {
          if (b.dataset.seguro) {
            GLOBAL['reiniciar-ok']();
            delete b.dataset.seguro;
            b.textContent = 'Reiniciar demo';
          } else {
            b.dataset.seguro = '1';
            b.textContent = '¿Seguro? Tocá de nuevo para reiniciar';
            setTimeout(() => { delete b.dataset.seguro; b.textContent = 'Reiniciar demo'; }, 4000);
          }
        }
      });
    }

    // ---------- escala del teléfono en pantallas bajas ----------
    function fit() {
      const w = root.innerWidth, h = root.innerHeight;
      const s = w <= 520 ? 1 : Math.max(0.6, Math.min(1, (h - 56) / 864));
      document.documentElement.style.setProperty('--scale', String(s));
    }
    root.addEventListener('resize', fit);
    fit();

    // ---------- galería ----------
    const stage = document.getElementById('stage');
    const galeria = document.getElementById('gallery');
    function mostrarGaleria() {
      try { if (location.hash !== '#pantallas') history.replaceState(null, '', '#pantallas'); } catch (e) { /* sin historial */ }
      root.Gallery.renderAll(galeria);
      stage.hidden = true;
      galeria.hidden = false;
      root.scrollTo(0, 0);
    }
    function mostrarApp() {
      try { history.replaceState(null, '', location.pathname + location.search); } catch (e) { /* sin historial */ }
      galeria.hidden = true;
      stage.hidden = false;
      render();
    }
    galeria.addEventListener('click', (e) => {
      if (e.target.closest('[data-demo="app"]')) mostrarApp();
    });

    // Los modos especiales se eligen con la dirección; al cambiarla se recarga.
    const especial = (h) => /^#(pantallas|figma(-\d)?|vista-.+)$/.test(h);
    root.addEventListener('hashchange', () => { if (especial(location.hash) || !location.hash) location.reload(); });

    const hash = location.hash.replace('#', '');
    const figma = hash.match(/^figma(?:-(\d))?$/);
    if (figma) {
      document.body.classList.add('bare-body');
      stage.hidden = true;
      galeria.hidden = false;
      root.Gallery.renderFigma(galeria, figma[1] ? Number(figma[1]) : 0);
      return;
    }
    if (hash.indexOf('vista-') === 0) {
      document.body.classList.add('bare-body');
      stage.hidden = true;
      galeria.hidden = false;
      root.Gallery.renderOne(galeria, hash.slice(6));
      return;
    }
    const inicio = S.usuarioActual() ? homeOf(S) : S.session.pendiente ? 'cambiar-clave' : 'splash';
    App.route = resolve(S, inicio);
    render();
    if (hash === 'pantallas') mostrarGaleria();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
})(window);
