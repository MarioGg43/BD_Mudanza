/* "Todas las pantallas": cada vista dibujada con datos de ejemplo frescos, lista para
   importar a Figma o sacar capturas. Con #vista-<id> se dibuja una sola, sin marco. */
(function (root) {
  'use strict';
  const L = root.Logic;

  const ADMIN = 35123456, CHOFER = 40987654, AYUDANTE = 38999888, CLIENTA = 29876543, CLIENTE_2 = 31555666;

  function draft(hoy, step, extra) {
    return Object.assign({
      step, fecha: L.sumarDias(hoy, 4), origen: 'Zuviría 50, Salta', destino: 'Güemes 900, Salta',
      servicios: [1, 4], patente: 'AG-234-NP',
      inventario: [
        { desc: 'Heladera', cant: 1, peso: 80, fragil: false },
        { desc: 'Televisor 50"', cant: 1, peso: 14, fragil: true },
        { desc: 'Cajas de cocina', cant: 8, peso: 6, fragil: true },
      ],
    }, extra || {});
  }

  const ENTRADAS = [
    { g: 'Sin sesión', id: 'inicio', t: 'Inicio', d: 'Consigna · logo, nombre y misión de la empresa.', r: 'splash' },
    { g: 'Sin sesión', id: 'login', t: 'Iniciar sesión', d: 'Consigna · correo y contraseña, olvidé mi contraseña y registrarse.', r: 'login' },
    { g: 'Sin sesión', id: 'registro', t: 'Registrarse', d: 'Consigna · nombre, correo y contraseña con confirmación.', r: 'registro' },
    { g: 'Sin sesión', id: 'recuperar', t: 'Recuperar contraseña', d: 'Proceso Recuperar Clave.', r: 'recuperar' },
    { g: 'Sin sesión', id: 'recuperar-ok', t: 'Contraseña temporal enviada', d: 'Respuesta de Recuperar Clave.', r: 'recuperar',
      setup: (c) => { c.ui.x.recuperado = { correo: 'maria.gomez@ejemplo.com', temporal: 'Mz7#kP2qTa' }; } },
    { g: 'Sin sesión', id: 'cambiar-clave', t: 'Cambio obligatorio de clave', d: 'Primer ingreso con clave temporal (Hito 2).', r: 'cambiar-clave', pendiente: AYUDANTE },

    { g: 'Cliente', id: 'cli-inicio', t: 'Inicio del cliente', d: 'Pedir mudanza y pedidos en curso.', r: 'cli/inicio', dni: CLIENTA },
    { g: 'Cliente', id: 'pedir-1', t: 'Pedir mudanza · paso 1', d: 'Fecha y direcciones.', r: 'cli/pedir', dni: CLIENTA, setup: (c) => { c.ui.draft = draft(c.S.hoy(), 1); } },
    { g: 'Cliente', id: 'pedir-2', t: 'Pedir mudanza · paso 2', d: 'Servicios con precio base.', r: 'cli/pedir', dni: CLIENTA, setup: (c) => { c.ui.draft = draft(c.S.hoy(), 2); } },
    { g: 'Cliente', id: 'pedir-3', t: 'Pedir mudanza · paso 3', d: 'Vehículos libres ese día.', r: 'cli/pedir', dni: CLIENTA, setup: (c) => { c.ui.draft = draft(c.S.hoy(), 3); } },
    { g: 'Cliente', id: 'pedir-4', t: 'Pedir mudanza · paso 4', d: 'Inventario: qué se lleva (Registrar Inventario).', r: 'cli/pedir', dni: CLIENTA, setup: (c) => { c.ui.draft = draft(c.S.hoy(), 4); } },
    { g: 'Cliente', id: 'pedir-5', t: 'Pedir mudanza · paso 5', d: 'Resumen antes de confirmar.', r: 'cli/pedir', dni: CLIENTA, setup: (c) => { c.ui.draft = draft(c.S.hoy(), 5); } },
    { g: 'Cliente', id: 'enviado', t: 'Pedido enviado', d: 'El pedido queda pendiente.', r: 'cli/enviado/1025', dni: CLIENTA },
    { g: 'Cliente', id: 'cli-pedidos', t: 'Mis pedidos', d: 'Proceso Consultar Pedidos.', r: 'cli/pedidos', dni: CLIENTA,
      setup: (c) => { c.ui.f.cliPed = 'todos'; } },
    { g: 'Cliente', id: 'cli-pedido', t: 'Detalle del pedido', d: 'Seguimiento, equipo, inventario y pagos.', r: 'cli/pedido/1023', dni: CLIENTE_2 },

    { g: 'Administrador', id: 'adm-panel', t: 'Panel', d: 'Resumen del día.', r: 'adm/panel', dni: ADMIN },
    { g: 'Administrador', id: 'adm-pedidos', t: 'Pedidos', d: 'Buscador y filtros por estado.', r: 'adm/pedidos', dni: ADMIN },
    { g: 'Administrador', id: 'adm-pedido', t: 'Detalle del pedido', d: 'Confirmar o rechazar (Confirmar Pedido).', r: 'adm/pedido/1025', dni: ADMIN },
    { g: 'Administrador', id: 'adm-rechazo', t: 'Rechazar pedido', d: 'El motivo le llega al cliente.', r: 'adm/pedido/1025', dni: ADMIN,
      setup: (c) => { c.ui.overlay = { kind: 'sheet', name: 'rechazo' }; c.ui.form = { name: 'rechazo', values: { motivo: 'No tenemos vehículos libres ese día. ¿Te sirve el lunes?' } }; } },
    { g: 'Administrador', id: 'adm-asignar', t: 'Asignar equipo', d: 'Chofer, ayudantes, vehículo y materiales.', r: 'adm/asignar/1024', dni: ADMIN },
    { g: 'Administrador', id: 'adm-cobro', t: 'Registrar cobro', d: 'Proceso Registrar Cobranza.', r: 'adm/cobro/1020', dni: ADMIN },
    { g: 'Administrador', id: 'adm-vehiculos', t: 'Vehículos', d: 'Consigna (CRUD) · buscador, listado con ver, editar y baja.', r: 'adm/vehiculos', dni: ADMIN },
    { g: 'Administrador', id: 'adm-vehiculo', t: 'Detalle del vehículo', d: 'Consigna (CRUD) · ver.', r: 'adm/vehiculo/AE-123-CD', dni: ADMIN },
    { g: 'Administrador', id: 'adm-vehiculo-nuevo', t: 'Agregar vehículo', d: 'Consigna (CRUD) · crear.', r: 'adm/vehiculo-form/nuevo', dni: ADMIN },
    { g: 'Administrador', id: 'adm-vehiculo-editar', t: 'Editar vehículo', d: 'Consigna (CRUD) · editar.', r: 'adm/vehiculo-form/AD-321-JK', dni: ADMIN },
    { g: 'Administrador', id: 'adm-vehiculo-baja', t: 'Confirmar baja', d: 'Consigna (CRUD) · eliminar con confirmación.', r: 'adm/vehiculos', dni: ADMIN,
      setup: (c) => { root.Screens.admVehiculos.acts.baja(c.ctx(), { dataset: { p: 'AD-321-JK' } }); } },
    { g: 'Administrador', id: 'adm-usuarios', t: 'Usuarios', d: 'Hito 2 · listado con filtros por rol.', r: 'adm/usuarios', dni: ADMIN },
    { g: 'Administrador', id: 'adm-usuario-nuevo', t: 'Nuevo usuario', d: 'Hito 2 · usuario automático (apellido + inicial).', r: 'adm/usuario-nuevo', dni: ADMIN,
      setup: (c) => { c.ui.form = { name: 'alta', values: { nombre: 'Pablo', apellido: 'Romero', dni: '42123123', telefono: '3875000000', correo: 'pablo.romero@mudanzassalta.com.ar', rol: 'Chofer' } }; } },
    { g: 'Administrador', id: 'adm-usuario', t: 'Detalle del usuario', d: 'Hito 2 · correo, rol, clave, baja y reactivación.', r: 'adm/usuario/38999888', dni: ADMIN },
    { g: 'Administrador', id: 'adm-usuario-rol', t: 'Cambiar rol', d: 'Proceso Asignar Rol.', r: 'adm/usuario/40987654', dni: ADMIN,
      setup: (c) => { c.ui.overlay = { kind: 'sheet', name: 'rol' }; } },
    { g: 'Administrador', id: 'adm-servicios', t: 'Servicios', d: 'Catálogo y precios base.', r: 'adm/servicios', dni: ADMIN },

    { g: 'Empleado', id: 'emp-mudanzas', t: 'Mis mudanzas', d: 'Proceso Consultar Mudanzas Asignadas.', r: 'emp/mudanzas', dni: CHOFER },
    { g: 'Empleado', id: 'emp-mudanza', t: 'Detalle de la mudanza', d: 'Cliente, recorrido, objetos frágiles y equipo.', r: 'emp/mudanza/1023', dni: CHOFER },
    { g: 'Empleado', id: 'emp-iniciar', t: 'Iniciar mudanza', d: 'Proceso Actualizar Estado del Pedido.', r: 'emp/mudanza/1023', dni: CHOFER,
      setup: (c) => { root.Screens.empMudanza.acts.iniciar(c.ctx()); } },

    { g: 'Todos', id: 'perfil', t: 'Perfil', d: 'Consigna · datos editables, guardar cambios y cerrar sesión.', r: 'perfil', dni: ADMIN },
  ];

  function dibujar(e, bare) {
    const Core = root.AppCore;
    const S = root.createStore(null);
    S.load();
    if (e.dni) S.session = { dni: e.dni, pendiente: null };
    if (e.pendiente) S.session = { dni: null, pendiente: e.pendiente };
    const ui = Core.freshUi();
    const route = Core.match(e.r);
    const api = { overlay(o) { ui.overlay = o; } };
    if (e.setup) e.setup({ S, ui, route, ctx: () => Core.makeCtx(S, ui, route, api) });

    const device = document.createElement('div');
    device.className = 'device';
    device.innerHTML = '<div class="phone' + (bare ? ' bare' : '') + '">' + (bare ? '' : '<div class="notch" aria-hidden="true"></div>') +
      '<div class="app"></div><div class="home-ind" aria-hidden="true"></div></div>';
    const phone = device.querySelector('.phone');
    Core.renderInto(phone.querySelector('.app'), phone, S, ui, route, {});
    phone.querySelectorAll('input, select, textarea, button, a').forEach((el) => { el.tabIndex = -1; });
    return device;
  }

  function renderAll(container) {
    container.innerHTML = '<div class="gal-head"><div><h1>Todas las pantallas</h1><p>' + ENTRADAS.length +
      ' vistas de la app, agrupadas por rol y con datos de ejemplo. Las marcadas "Consigna" son las cinco que pide Desarrollo Móvil. ' +
      'Para importarlas a Figma usá "Pantallas para Figma": las muestra sin marco, una por una.</p>' +
      '<p class="gal-links">Pantallas para Figma: <a href="#figma">las 35 juntas</a>' +
      TANDAS.map((t, i) => ' · <a href="#figma-' + (i + 1) + '">tanda ' + (i + 1) + ' (' + t[0] + ' a ' + t[1] + ')</a>').join('') + '</p></div>' +
      '<button class="btn primary sm" data-demo="app">Volver a la app</button></div>';
    let n = 0;
    const grupos = [...new Set(ENTRADAS.map((e) => e.g))];
    grupos.forEach((g) => {
      const sec = document.createElement('section');
      sec.className = 'gal-group';
      sec.innerHTML = '<h2>' + g + '</h2><div class="gal-grid"></div>';
      const grid = sec.querySelector('.gal-grid');
      ENTRADAS.filter((e) => e.g === g).forEach((e) => {
        n++;
        const fig = document.createElement('figure');
        fig.className = 'gal';
        fig.id = 'pantalla-' + e.id;
        fig.appendChild(dibujar(e, false));
        const cap = document.createElement('figcaption');
        cap.innerHTML = '<b><span>' + n + '</span>' + e.t + '</b><small>' + e.d + '</small>';
        fig.appendChild(cap);
        grid.appendChild(fig);
      });
      container.appendChild(sec);
    });
  }

  function renderOne(container, id) {
    const e = ENTRADAS.find((x) => x.id === id) || ENTRADAS[0];
    container.className = '';
    container.innerHTML = '';
    container.appendChild(dibujar(e, true));
  }

  // Tandas de hasta 10 pantallas, las mismas que las carpetas de capturas.
  const TANDAS = [[1, 6], [7, 15], [16, 23], [24, 31], [32, 35]];

  // "Pantallas para Figma": cada pantalla es un hijo directo de la hoja, sin marco
  // ni textos alrededor, para que al importarla con html.to.design quede como un
  // marco suelto que se puede conectar en el prototipo.
  function renderFigma(container, tanda) {
    const [desde, hasta] = tanda ? TANDAS[tanda - 1] : [1, ENTRADAS.length];
    container.className = 'figma-sheet';
    container.innerHTML = '';
    ENTRADAS.forEach((e, i) => {
      const n = i + 1;
      if (n < desde || n > hasta) return;
      const phone = dibujar(e, true).firstElementChild;
      phone.id = String(n).padStart(2, '0') + '-' + e.id;
      phone.setAttribute('aria-label', n + '. ' + e.t);
      container.appendChild(phone);
    });
  }

  root.Gallery = { ENTRADAS, TANDAS, renderAll, renderOne, renderFigma };
})(window);
