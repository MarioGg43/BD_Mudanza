/* Piezas de interfaz compartidas por todas las pantallas. Todas devuelven HTML. */
(function (root) {
  'use strict';

  const P = {
    home: '<path d="m4 11 8-6.5 8 6.5v8a1.5 1.5 0 0 1-1.5 1.5h-13A1.5 1.5 0 0 1 4 19z"/><path d="M10 20.5v-6h4v6"/>',
    grid: '<rect x="4" y="4" width="7" height="7" rx="2"/><rect x="13" y="4" width="7" height="7" rx="2"/><rect x="4" y="13" width="7" height="7" rx="2"/><rect x="13" y="13" width="7" height="7" rx="2"/>',
    clipboard: '<path d="M9 4h6v3H9z"/><path d="M8 5.5H6.5A1.5 1.5 0 0 0 5 7v12.5A1.5 1.5 0 0 0 6.5 21h11a1.5 1.5 0 0 0 1.5-1.5V7a1.5 1.5 0 0 0-1.5-1.5H16M8.5 12h7M8.5 16h4.5"/>',
    truck: '<path d="M2.5 6.5h11v9.5h-11zM13.5 10h4l3 3.2V16h-7z"/><circle cx="6.5" cy="18" r="1.9"/><circle cx="17" cy="18" r="1.9"/>',
    users: '<circle cx="9" cy="8.5" r="3.5"/><path d="M2.5 20a6.5 6.5 0 0 1 13 0M16 5.2a3.5 3.5 0 0 1 0 6.6M18 14.5a6.5 6.5 0 0 1 3.5 5.5"/>',
    user: '<circle cx="12" cy="8" r="4"/><path d="M4.5 20.5a7.5 7.5 0 0 1 15 0"/>',
    mail: '<rect x="3" y="5" width="18" height="14" rx="2.5"/><path d="m3.5 7 8.5 6 8.5-6"/>',
    lock: '<rect x="4.5" y="10" width="15" height="11" rx="2.5"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/>',
    eye: '<path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12Z"/><circle cx="12" cy="12" r="2.8"/>',
    eyeOff: '<path d="M4 4l16 16M9.9 5.8A9.8 9.8 0 0 1 12 5.5c6 0 9.5 6.5 9.5 6.5a17 17 0 0 1-3 3.7M6.5 7.6A16.6 16.6 0 0 0 2.5 12S6 18.5 12 18.5a9.4 9.4 0 0 0 4.2-1"/><path d="M10 10a2.8 2.8 0 0 0 4 4"/>',
    phone: '<path d="M5 3.5h3.5l1.8 4.6-2.3 1.4a11.5 11.5 0 0 0 6.5 6.5l1.4-2.3 4.6 1.8V19a1.8 1.8 0 0 1-1.8 1.8A15.8 15.8 0 0 1 3.2 5.3 1.8 1.8 0 0 1 5 3.5Z"/>',
    search: '<circle cx="11" cy="11" r="6.5"/><path d="m20 20-4.2-4.2"/>',
    back: '<path d="m14.5 5.5-6.5 6.5 6.5 6.5"/>',
    chev: '<path d="m9.5 5.5 6.5 6.5-6.5 6.5"/>',
    down: '<path d="m6 9.5 6 6 6-6"/>',
    plus: '<path d="M12 5v14M5 12h14"/>',
    edit: '<path d="M4 20h4L19.5 8.5a2.8 2.8 0 0 0-4-4L4 16z"/><path d="m14 6 4 4"/>',
    trash: '<path d="M4 7h16M9.5 7V4.5h5V7M6 7l1 13h10l1-13M10 11v5M14 11v5"/>',
    logout: '<path d="M14 4h4a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-4M10 16.5 5.5 12 10 7.5M5.5 12H16"/>',
    alert: '<circle cx="12" cy="12" r="9"/><path d="M12 7.5v5.5M12 16.5h.01"/>',
    check: '<path d="m5 12.5 4.5 4.5L19 7.5"/>',
    x: '<path d="M6 6l12 12M18 6 6 18"/>',
    calendar: '<rect x="3.5" y="5" width="17" height="15.5" rx="2.5"/><path d="M3.5 10h17M8 3v4M16 3v4"/>',
    pin: '<path d="M12 21s-7-6.2-7-11.5a7 7 0 0 1 14 0C19 14.8 12 21 12 21Z"/><circle cx="12" cy="9.5" r="2.5"/>',
    box: '<path d="M3.5 7.5 12 3l8.5 4.5v9L12 21l-8.5-4.5z"/><path d="M3.5 7.5 12 12l8.5-4.5M12 12v9"/>',
    money: '<rect x="2.5" y="6" width="19" height="12" rx="2.5"/><circle cx="12" cy="12" r="2.8"/><path d="M6 9.5v5M18 9.5v5"/>',
    key: '<circle cx="8" cy="15" r="4"/><path d="m10.8 12.2 8.7-8.7M16.5 6.5l2.5 2.5M14 9l2 2"/>',
    refresh: '<path d="M20 11a8 8 0 0 0-14.3-4.5L4 8.5M4 4v4.5h4.5M4 13a8 8 0 0 0 14.3 4.5L20 15.5M20 20v-4.5h-4.5"/>',
    shield: '<path d="M12 3 4.5 6v5.5c0 4.8 3.2 8.2 7.5 9.5 4.3-1.3 7.5-4.7 7.5-9.5V6z"/><path d="m8.5 12 2.5 2.5 4.5-5"/>',
    info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v5.5M12 7.5h.01"/>',
    glass: '<path d="M7.5 3h9L15.8 9a3.8 3.8 0 0 1-7.6 0z"/><path d="M12 12.8V20M8.5 21h7"/>',
    route: '<circle cx="6" cy="18" r="2.5"/><circle cx="18" cy="6" r="2.5"/><path d="M8.5 18h6a3.5 3.5 0 0 0 0-7h-5a3.5 3.5 0 0 1 0-7H15.5"/>',
    tag: '<path d="M3.5 12.5V4.5h8l9 9-8 8z"/><circle cx="8" cy="9" r="1.5"/>',
    wrench: '<path d="M14.7 6.3a4 4 0 0 0 5 5L13 18a2.8 2.8 0 0 1-4-4z"/><path d="M14.7 6.3 17.5 3.5a4 4 0 0 0-5 5"/>',
    play: '<path d="M7 4.5v15l12-7.5z"/>',
    flag: '<path d="M5 21V4M5 4.5h11l-2 4 2 4H5"/>',
    card: '<rect x="3" y="5" width="18" height="14" rx="2.5"/><path d="M3 9.5h18M7 15h4"/>',
    id: '<rect x="3" y="5" width="18" height="14" rx="2.5"/><circle cx="9" cy="11" r="2.2"/><path d="M5.8 16a3.3 3.3 0 0 1 6.4 0M14.5 10h3.5M14.5 13.5h3.5"/>',
    weight: '<path d="M6.5 8h11l2.5 12.5h-16z"/><circle cx="12" cy="5.5" r="2.2"/>',
    copy: '<rect x="8.5" y="8.5" width="11.5" height="11.5" rx="2.2"/><path d="M15.5 8.5V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v7.5a2 2 0 0 0 2 2h2.5"/>',
  };

  function icon(name, size) {
    const s = size || 20;
    return '<svg width="' + s + '" height="' + s + '" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" ' +
      'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + (P[name] || '') + '</svg>';
  }

  function esc(v) {
    return String(v == null ? '' : v).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  }

  const attrs = (o) => Object.keys(o || {}).map((k) => ' data-' + k + '="' + esc(o[k]) + '"').join('');
  const speed = '<div class="speed" aria-hidden="true"><i></i><i></i><i></i></div>';
  const nombreDe = (u) => (u ? u.nombre + ' ' + u.apellido : '');
  const corto = (dir) => String(dir || '').split(',')[0];
  const plural = (n, uno, varios) => n + ' ' + (n === 1 ? uno : varios);
  const claseRol = (rol) => (rol === 'Ayudante de Carga' ? 'Ayudante' : rol);

  function statusbar() {
    return '<div class="statusbar" aria-hidden="true"><span class="num">9:41</span><span class="sig">' +
      '<svg width="18" height="12" viewBox="0 0 18 12" fill="currentColor"><rect x="0" y="8" width="3" height="4" rx="1"/><rect x="5" y="5.5" width="3" height="6.5" rx="1"/><rect x="10" y="3" width="3" height="9" rx="1"/><rect x="15" y="0" width="3" height="12" rx="1"/></svg>' +
      '<svg width="16" height="12" viewBox="0 0 16 12" fill="currentColor"><path d="M8 2.3c2.3 0 4.4.9 6 2.4l1.3-1.4A10.4 10.4 0 0 0 8 .3C5.2.3 2.6 1.4.7 3.3L2 4.7a8.4 8.4 0 0 1 6-2.4Zm0 4c1.2 0 2.3.4 3.2 1.2l1.3-1.4A6.6 6.6 0 0 0 8 4.3c-1.7 0-3.3.6-4.5 1.8l1.3 1.4A4.6 4.6 0 0 1 8 6.3Zm0 4 2-2.1a3 3 0 0 0-4 0l2 2.1Z"/></svg>' +
      '<svg width="27" height="13" viewBox="0 0 27 13" fill="none"><rect x=".5" y=".5" width="23" height="12" rx="3.5" stroke="currentColor" opacity=".45"/><rect x="2" y="2" width="18" height="9" rx="2" fill="currentColor"/><path d="M25 4.5v4a2 2 0 0 0 0-4Z" fill="currentColor" opacity=".45"/></svg>' +
      '</span></div>';
  }

  // ---------- barras ----------
  function hero(o) {
    const back = o.back ? '<div class="hero-back"><button class="icon-btn" data-back aria-label="Volver">' + icon('back', 22) + '</button>' +
      (o.backLabel ? '<span class="small">' + esc(o.backLabel) + '</span>' : '') + '</div>' : '';
    return '<header class="hero">' + speed + back +
      '<div class="hero-row"><div style="min-width:0"><h1>' + esc(o.title) + '</h1>' +
      (o.sub ? '<p>' + o.sub + '</p>' : '') + '</div>' + (o.right || '') + '</div>' + (o.extra || '') + '</header>';
  }

  function appbar(o) {
    return '<header class="appbar">' +
      (o.back === false ? '<span style="width:6px"></span>' : '<button class="icon-btn" data-back aria-label="Volver">' + icon('back', 22) + '</button>') +
      '<div class="t"><h2>' + esc(o.title) + '</h2>' + (o.sub ? '<small>' + o.sub + '</small>' : '') + '</div>' +
      (o.right || '') + '</header>';
  }

  const TABS = {
    Cliente: [['cli/inicio', 'home', 'Inicio'], ['cli/pedidos', 'clipboard', 'Pedidos'], ['perfil', 'user', 'Perfil']],
    Administrador: [['adm/panel', 'grid', 'Panel'], ['adm/pedidos', 'clipboard', 'Pedidos'], ['adm/vehiculos', 'truck', 'Vehículos'],
      ['adm/usuarios', 'users', 'Usuarios'], ['perfil', 'user', 'Perfil']],
    Empleado: [['emp/mudanzas', 'truck', 'Mudanzas'], ['perfil', 'user', 'Perfil']],
  };

  function tabbar(rol, activa) {
    const grupo = rol === 'Chofer' || rol === 'Ayudante de Carga' ? 'Empleado' : rol;
    return '<nav class="tabbar" aria-label="Menú">' + (TABS[grupo] || []).map(([ruta, ic, label]) =>
      '<button class="tab' + (ruta === activa ? ' on' : '') + '" data-go="' + ruta + '"' + (ruta === activa ? ' aria-current="page"' : '') + '>' +
      icon(ic, 22) + label + '</button>').join('') + '</nav>';
  }

  // ---------- estados ----------
  const CLASE_PEDIDO = { Pendiente: 'pendiente', Confirmado: 'confirmado', Asignado: 'asignado', 'En curso': 'encurso', Finalizado: 'finalizado', Rechazado: 'rechazado' };
  const CLASE_VEHICULO = { Disponible: 'disponible', 'En Viaje': 'enviaje', 'En Mantenimiento': 'mant', 'Fuera de Servicio': 'fuera' };
  const badgePedido = (e) => '<span class="badge b-' + CLASE_PEDIDO[e] + '">' + esc(e) + '</span>';
  const badgeVehiculo = (e) => '<span class="badge b-' + CLASE_VEHICULO[e] + '">' + esc(e) + '</span>';
  const badgeUsuario = (u) => u.activo ? '<span class="badge b-activo">Activo</span>' : '<span class="badge b-baja">De baja</span>';

  // ---------- formularios ----------
  function field(ctx, o) {
    const val = o.value !== undefined ? o.value : ctx.val(o.id, o.def == null ? '' : o.def);
    const err = o.error || ctx.err(o.id);
    const tipo = o.type || 'text';
    let control;
    if (tipo === 'select') {
      control = '<select id="f-' + o.id + '" name="' + o.id + '"' + (o.live ? ' data-live="' + o.live + '"' : '') + '>' +
        (o.placeholder ? '<option value="">' + esc(o.placeholder) + '</option>' : '') +
        o.options.map((op) => {
          const [v, t] = Array.isArray(op) ? op : [op, op];
          return '<option value="' + esc(v) + '"' + (String(v) === String(val) ? ' selected' : '') + '>' + esc(t) + '</option>';
        }).join('') + '</select>' + icon('down', 18);
    } else if (tipo === 'textarea') {
      control = '<textarea id="f-' + o.id + '" name="' + o.id + '" rows="' + (o.rows || 3) + '" placeholder="' + esc(o.placeholder || '') + '"' +
        (o.live ? ' data-live="' + o.live + '"' : '') + '>' + esc(val) + '</textarea>';
    } else {
      control = '<input id="f-' + o.id + '" name="' + o.id + '" type="' + tipo + '" value="' + esc(val) + '"' +
        (o.placeholder ? ' placeholder="' + esc(o.placeholder) + '"' : '') +
        (o.auto ? ' autocomplete="' + o.auto + '"' : '') + (o.mode ? ' inputmode="' + o.mode + '"' : '') +
        (o.min ? ' min="' + o.min + '"' : '') + (o.disabled ? ' disabled' : '') +
        (o.live ? ' data-live="' + o.live + '"' : '') + '>' +
        (tipo === 'password' ? '<button type="button" class="eye" data-act="ver-clave" aria-label="Mostrar contraseña">' + icon('eye', 18) + '</button>' : '') +
        (o.suf ? '<span class="suf">' + esc(o.suf) + '</span>' : '');
    }
    return '<div class="field"><label for="f-' + o.id + '">' + esc(o.label) + '</label>' +
      '<div class="input' + (err ? ' bad' : '') + '">' + (o.icon ? icon(o.icon, 18) : '') + control + '</div>' +
      (err ? '<div class="ferr">' + esc(err) + '</div>' : (o.hint ? '<div class="hint">' + esc(o.hint) + '</div>' : '')) + '</div>';
  }

  function opt(o) {
    return '<label class="opt' + (o.check ? ' check' : '') + (o.disabled ? ' disabled' : '') + '">' +
      '<input type="' + (o.check ? 'checkbox' : 'radio') + '" name="' + o.name + '" value="' + esc(o.value) + '"' +
      (o.checked ? ' checked' : '') + (o.disabled ? ' disabled' : '') + (o.live ? ' data-live="' + o.live + '"' : '') + '>' +
      '<span class="mark">' + icon('check', 14) + '</span>' +
      '<span class="body"><b>' + o.title + '</b>' + (o.sub ? '<small>' + o.sub + '</small>' : '') + '</span>' +
      (o.right || '') + '</label>';
  }

  function formError(ctx) {
    const e = ctx.ui.form && ctx.ui.form.error;
    return e ? '<div class="banner error" role="alert">' + icon('alert', 18) + '<span>' + esc(e) + '</span></div>' : '';
  }

  function chips(items, activo, key) {
    return '<div class="chips" role="tablist">' + items.map(([v, t, n]) =>
      '<button class="chip' + (v === activo ? ' on' : '') + '" role="tab" aria-selected="' + (v === activo) + '" data-act="filtro" data-k="' + key + '" data-v="' + esc(v) + '">' +
      esc(t) + (n != null ? '<span class="n">' + n + '</span>' : '') + '</button>').join('') + '</div>';
  }

  function search(ctx, key, placeholder) {
    return '<label class="search">' + icon('search', 18) + '<span class="sr">Buscar</span>' +
      '<input type="search" id="q-' + key + '" value="' + esc(ctx.ui.q[key] || '') + '" placeholder="' + esc(placeholder) + '" data-live="buscar" data-k="' + key + '"></label>';
  }

  function empty(ic, titulo, texto, extra) {
    return '<div class="empty"><div class="ic">' + icon(ic, 26) + '</div><b>' + esc(titulo) + '</b>' +
      (texto ? '<p>' + esc(texto) + '</p>' : '') + (extra || '') + '</div>';
  }

  const kv = (k, v) => '<div class="kv"><span>' + esc(k) + '</span><b>' + v + '</b></div>';

  // ---------- pedidos ----------
  function nombresServicios(S, p) {
    return p.servicios.map((id) => (S.servicio(id) || {}).tipo).filter(Boolean).join(' + ');
  }

  function pesoTotal(p) {
    return p.inventario.reduce((a, i) => a + i.cant * i.peso, 0);
  }

  function pedidoCard(ctx, p, o) {
    const S = ctx.S, L = ctx.L;
    const cli = o && o.cliente ? S.usuario(p.clienteDni) : null;
    return '<button class="pcard" data-go="' + o.go + '">' +
      '<div class="row"><span class="pnum">Pedido #' + p.id + '</span>' + badgePedido(p.estado) + '</div>' +
      (cli ? '<div class="meta">' + icon('user', 15) + '<span>' + esc(nombreDe(cli)) + '</span></div>' : '') +
      '<div class="pserv">' + esc(nombresServicios(S, p)) + '</div>' +
      '<div class="meta">' + icon('calendar', 15) + '<span>' + esc(L.diaRelativo(p.fecha, ctx.hoy)) + '</span></div>' +
      '<div class="meta">' + icon('route', 15) + '<span>' + esc(corto(p.origen)) + ' → ' + esc(corto(p.destino)) + '</span></div>' +
      '<div class="pfoot"><span class="muted">' + plural(p.inventario.length, 'objeto', 'objetos') + '</span><b>' + L.money(S.total(p)) + '</b></div>' +
      '</button>';
  }

  const PASOS = [
    ['Pendiente', 'Pedido recibido', 'Esperando que la empresa lo confirme'],
    ['Confirmado', 'Confirmado', 'La empresa aprobó el pedido'],
    ['Asignado', 'Equipo asignado', 'Ya tiene chofer, ayudantes y vehículo'],
    ['En curso', 'En camino', 'La mudanza está en marcha'],
    ['Finalizado', 'Finalizado', 'Todo entregado en destino'],
  ];

  function timeline(ctx, p) {
    if (p.estado === 'Rechazado') {
      return '<div class="banner error" role="status">' + icon('alert', 18) + '<span><b>Pedido rechazado.</b> ' + esc(p.motivo || '') + '</span></div>';
    }
    const actual = PASOS.findIndex((x) => x[0] === p.estado);
    const fechaDe = (estado) => {
      const h = p.historial.filter((x) => x.estado === estado).pop();
      return h ? ctx.L.diaRelativo(h.fecha, ctx.hoy) : '';
    };
    return '<div class="card"><h4>Seguimiento</h4><div class="timeline">' + PASOS.map(([estado, titulo, desc], i) => {
      const cls = i < actual ? 'done' : i === actual ? (p.estado === 'Finalizado' ? 'done' : 'now') : 'todo';
      const cuando = i <= actual ? fechaDe(estado) : '';
      return '<div class="tl ' + cls + '"><span class="dot"></span><div><b>' + titulo + '</b><small>' +
        (i <= actual ? esc(cuando) + (cuando ? ' · ' : '') : '') + desc + '</small></div></div>';
    }).join('') + '</div></div>';
  }

  function ruta(p) {
    return '<div class="route"><div class="pt"><i></i><div><small>Desde</small><b>' + esc(p.origen) + '</b></div></div>' +
      '<div class="line"></div><div class="pt dest"><i></i><div><small>Hasta</small><b>' + esc(p.destino) + '</b></div></div></div>';
  }

  function inventario(p) {
    const total = pesoTotal(p);
    return '<div class="card"><h4>Qué se lleva · ' + plural(p.inventario.reduce((a, i) => a + i.cant, 0), 'bulto', 'bultos') +
      ', ' + total.toLocaleString('es-AR') + ' kg</h4><div class="items">' +
      p.inventario.map((i) => '<div class="item"><div class="d"><b>' + esc(i.desc) + '</b><small>' + i.cant + ' × ' +
        i.peso.toLocaleString('es-AR') + ' kg</small></div>' +
        (i.fragil ? '<span class="tag fragil">' + icon('glass', 13) + 'Frágil</span>' : '') + '</div>').join('') + '</div></div>';
  }

  function persona(u, detalle) {
    if (!u) return '';
    return '<div class="person"><span class="av ' + claseRol(u.rol) + '">' + ctxIniciales(u) + '</span><div><b>' + esc(nombreDe(u)) +
      '</b><small>' + esc(detalle || u.rol) + '</small></div></div>';
  }
  const ctxIniciales = (u) => (u.nombre.charAt(0) + u.apellido.charAt(0)).toUpperCase();

  function pedidoDetalle(ctx, p, o) {
    const S = ctx.S, L = ctx.L;
    o = o || {};
    const v = S.vehiculo(p.patente);
    const total = S.total(p), cobrado = S.cobrado(p), saldo = total - cobrado;
    const partes = [];
    if (o.timeline !== false) partes.push(timeline(ctx, p));
    partes.push('<div class="card"><h4>Cuándo y dónde</h4><div class="stack tight"><div class="meta">' + icon('calendar', 16) +
      '<span><b style="color:var(--tinta);font-weight:600">' + esc(L.fechaLarga(p.fecha)) + '</b></span></div>' + ruta(p) + '</div></div>');
    partes.push('<div class="card"><h4>Servicios</h4><div class="sum">' + p.servicios.map((id) => {
      const s = S.servicio(id);
      return s ? '<div class="l"><span>' + esc(s.tipo) + '</span><span>' + L.money(s.precio) + '</span></div>' : '';
    }).join('') + '<div class="l total"><span>Total</span><span>' + L.money(total) + '</span></div></div></div>');
    if (v) {
      partes.push('<div class="card"><h4>Vehículo</h4><div class="row"><div><b>' + esc(v.tipo) + '</b><div class="vmodel">' +
        esc(v.marcaModelo) + ' · ' + v.kg.toLocaleString('es-AR') + ' kg</div></div><span class="plate sm">' + esc(v.patente) + '</span></div></div>');
    }
    if (p.choferDni) {
      partes.push('<div class="card"><h4>Equipo</h4>' + persona(S.usuario(p.choferDni), 'Chofer') +
        p.ayudantes.map((d) => persona(S.usuario(d), 'Ayudante de carga')).join('') +
        (p.materiales.length ? '<div class="tags" style="margin-top:8px">' + p.materiales.map((m) => '<span class="tag">' + esc(m) + '</span>').join('') + '</div>' : '') +
        '</div>');
    }
    partes.push(inventario(p));
    if (o.pagos !== false && p.estado !== 'Rechazado') {
      const cobros = S.cobrosDe(p);
      partes.push('<div class="card"><h4>Pagos</h4><div class="sum">' +
        '<div class="l"><span>Total</span><span>' + L.money(total) + '</span></div>' +
        '<div class="l"><span>Pagado</span><span class="pagado">' + L.money(cobrado) + '</span></div>' +
        '<div class="l total"><span>Saldo</span><span class="' + (saldo > 0 ? 'saldo' : 'pagado') + '">' + L.money(saldo) + '</span></div>' +
        cobros.map((c) => '<div class="l small muted"><span>' + esc(L.diaRelativo(c.fecha, ctx.hoy)) + ' · ' + esc(c.metodo) + '</span><span>' +
          L.money(c.monto) + '</span></div>').join('') + '</div></div>');
    }
    return partes.join('');
  }

  root.UI = {
    icon, esc, attrs, statusbar, hero, appbar, tabbar, badgePedido, badgeVehiculo, badgeUsuario, field, opt,
    formError, chips, search, empty, kv, pedidoCard, pedidoDetalle, timeline, ruta, inventario, persona,
    nombreDe, corto, plural, claseRol, nombresServicios, pesoTotal, speed,
  };
})(window);
