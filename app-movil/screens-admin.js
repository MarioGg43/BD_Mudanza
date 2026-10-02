/* Pantallas del administrador. */
(function (root) {
  'use strict';
  const Screens = root.Screens = root.Screens || {};
  const UI = root.UI;
  const { icon, esc } = UI;

  const avatarBtn = (ctx) => '<button class="avatar" data-go="perfil" aria-label="Mi perfil">' +
    ctx.L.iniciales(ctx.user.nombre, ctx.user.apellido) + '</button>';
  const capital = (s) => s.charAt(0).toUpperCase() + s.slice(1);
  const noExiste = (titulo, texto) => '<div class="scr">' + UI.appbar({ title: titulo }) + '<div class="content">' +
    UI.empty('info', texto, 'Puede que se haya borrado al reiniciar la demo.') + '</div></div>';
  const telefono = (t) => String(t).replace(/^(\d{3})(\d{3})(\d{4})$/, '$1 $2-$3');
  const conSaldo = (S, p) => !['Pendiente', 'Rechazado'].includes(p.estado) && S.saldo(p) > 0;

  function kpi(ic, n, label, act, v, alerta, money) {
    return '<button class="kpi' + (alerta ? ' alert' : '') + '" data-act="' + act + '" data-v="' + esc(v) + '">' +
      '<span class="ic">' + icon(ic, 18) + '</span><span class="n' + (money ? ' money' : '') + '">' + n + '</span>' +
      '<span class="l">' + esc(label) + '</span></button>';
  }

  // ---------- panel ----------
  Screens.admPanel = {
    tone: 'light',
    render(ctx) {
      const S = ctx.S, L = ctx.L, u = ctx.user, hoy = ctx.hoy;
      const ped = S.state.pedidos;
      const pendientes = ped.filter((p) => p.estado === 'Pendiente').length;
      const sinAsignar = ped.filter((p) => p.estado === 'Confirmado').length;
      const deHoy = ped.filter((p) => p.fecha === hoy && S.activo(p));
      const libres = S.state.vehiculos.filter((v) => v.estado === 'Disponible').length;
      const porCobrar = ped.filter((p) => conSaldo(S, p)).reduce((a, p) => a + S.saldo(p), 0);
      return '<div class="scr">' + UI.hero({ title: 'Hola, ' + u.nombre, sub: capital(L.fechaLarga(hoy)), right: avatarBtn(ctx) }) +
        '<div class="content"><div class="stack">' +
        '<div class="kpis">' +
        kpi('clipboard', pendientes, 'Pedidos por confirmar', 'ir-pedidos', 'Pendiente', pendientes > 0) +
        kpi('users', sinAsignar, 'Confirmados sin equipo', 'ir-pedidos', 'Confirmado', sinAsignar > 0) +
        kpi('truck', libres + '<small style="font-size:14px;color:var(--tinta-3);font-weight:600"> / ' + S.state.vehiculos.length + '</small>',
          'Vehículos disponibles', 'ir-vehiculos', 'Disponible') +
        kpi('money', L.money(porCobrar), 'Saldo por cobrar', 'ir-pedidos', 'saldo', false, true) +
        '</div>' +
        '<div class="section-title"><h3>Mudanzas de hoy</h3><span class="small muted">' + UI.plural(deHoy.length, 'mudanza', 'mudanzas') + '</span></div>' +
        (deHoy.length ? deHoy.map((p) => UI.pedidoCard(ctx, p, { go: 'adm/pedido/' + p.id, cliente: true })).join('')
          : UI.empty('truck', 'Hoy no hay mudanzas', 'Las mudanzas confirmadas para hoy aparecen acá.')) +
        '<div class="section-title"><h3>Administración</h3></div>' +
        '<div class="card pad-0"><div class="actions-list">' +
        '<button class="action-row" data-go="adm/servicios"><span class="ic">' + icon('tag', 18) + '</span><span>Servicios y precios</span>' + icon('chev', 18) + '</button>' +
        '<button class="action-row" data-go="adm/usuario-nuevo"><span class="ic">' + icon('user', 18) + '</span><span>Dar de alta un usuario</span>' + icon('chev', 18) + '</button>' +
        '<button class="action-row" data-go="adm/vehiculo-form/nuevo"><span class="ic">' + icon('truck', 18) + '</span><span>Agregar un vehículo</span>' + icon('chev', 18) + '</button>' +
        '</div></div></div></div>' + UI.tabbar(u.rol, 'adm/panel') + '</div>';
    },
    acts: {
      'ir-pedidos'(ctx, el) { ctx.ui.f.admPed = el.dataset.v; ctx.ui.q.admPed = ''; ctx.go('adm/pedidos'); },
      'ir-vehiculos'(ctx, el) { ctx.ui.f.admVeh = el.dataset.v; ctx.ui.q.admVeh = ''; ctx.go('adm/vehiculos'); },
    },
  };

  // ---------- pedidos ----------
  const FILTROS_PED = [['todos', 'Todos'], ['Pendiente', 'Por confirmar'], ['Confirmado', 'Sin equipo'], ['Asignado', 'Asignados'],
    ['En curso', 'En curso'], ['saldo', 'Con saldo'], ['Finalizado', 'Finalizados'], ['Rechazado', 'Rechazados']];

  Screens.admPedidos = {
    tone: 'light',
    render(ctx) {
      const S = ctx.S, u = ctx.user;
      const f = ctx.ui.f.admPed || 'todos';
      const q = (ctx.ui.q.admPed || '').trim().toLowerCase();
      const pasa = (p, filtro) => filtro === 'todos' || (filtro === 'saldo' ? conSaldo(S, p) : p.estado === filtro);
      const busca = (p) => {
        if (!q) return true;
        const c = S.usuario(p.clienteDni);
        return ('#' + p.id + ' ' + UI.nombreDe(c) + ' ' + p.origen + ' ' + p.destino).toLowerCase().includes(q);
      };
      const base = S.state.pedidos.filter(busca).sort((a, b) => b.id - a.id);
      const lista = base.filter((p) => pasa(p, f));
      return '<div class="scr">' + UI.hero({ title: 'Pedidos', sub: UI.plural(S.state.pedidos.length, 'pedido', 'pedidos') + ' en total',
        extra: UI.search(ctx, 'admPed', 'Buscar por cliente, número o calle') }) +
        '<div class="content"><div class="stack">' +
        UI.chips(FILTROS_PED.map(([v, t]) => [v, t, base.filter((p) => pasa(p, v)).length]), f, 'admPed') +
        (lista.length ? lista.map((p) => UI.pedidoCard(ctx, p, { go: 'adm/pedido/' + p.id, cliente: true })).join('')
          : UI.empty('search', 'No hay pedidos con ese filtro', q ? 'Probá con otra búsqueda.' : 'Elegí otro filtro arriba.')) +
        '</div></div>' + UI.tabbar(u.rol, 'adm/pedidos') + '</div>';
    },
  };

  Screens.admPedido = {
    render(ctx) {
      const S = ctx.S, L = ctx.L;
      const p = S.pedido(ctx.params.id);
      if (!p) return noExiste('Pedido', 'No encontramos ese pedido');
      const c = S.usuario(p.clienteDni);
      const saldo = S.saldo(p);
      let barra = '';
      if (p.estado === 'Pendiente') {
        barra = '<button class="btn danger-o" data-act="rechazar">Rechazar</button><button class="btn primary" data-act="confirmar">Confirmar</button>';
      } else if (p.estado === 'Confirmado') {
        barra = '<button class="btn danger-o" data-act="rechazar">Rechazar</button><button class="btn primary" data-go="adm/asignar/' + p.id + '">Asignar equipo</button>';
      } else if (p.estado === 'Asignado') {
        barra = '<button class="btn ghost" data-go="adm/asignar/' + p.id + '">Cambiar equipo</button>' +
          (saldo > 0 ? '<button class="btn primary" data-go="adm/cobro/' + p.id + '">Registrar cobro</button>' : '');
      } else if (conSaldo(S, p)) {
        barra = '<button class="btn primary" data-go="adm/cobro/' + p.id + '">Registrar cobro · ' + L.money(saldo) + '</button>';
      }
      return '<div class="scr">' + UI.appbar({ title: 'Pedido #' + p.id, sub: 'Cliente: ' + esc(UI.nombreDe(c)), right: UI.badgePedido(p.estado) }) +
        '<div class="content"><div class="stack">' +
        '<div class="card"><h4>Cliente</h4>' + UI.persona(c, 'Cliente · ' + (c ? c.usuario : '')) +
        '<div class="meta" style="margin-top:4px">' + icon('phone', 15) + '<span style="user-select:all">' + esc(telefono(c ? c.telefono : '')) + '</span></div>' +
        '<div class="meta" style="margin-top:6px">' + icon('mail', 15) + '<span style="user-select:all">' + esc(c ? c.correo : '') + '</span></div></div>' +
        UI.pedidoDetalle(ctx, p) + '</div></div>' +
        (barra ? '<div class="bottom-bar">' + barra + '</div>' : '') + '</div>';
    },
    acts: {
      confirmar(ctx) {
        const id = ctx.params.id;
        ctx.overlay({ kind: 'confirm', title: '¿Confirmar el pedido #' + id + '?', icon: 'check', confirm: 'Confirmar', act: 'confirmar-ok',
          text: 'El cliente lo va a ver como confirmado. Después le asignás el chofer, los ayudantes y el vehículo.' });
      },
      'confirmar-ok'(ctx) {
        const r = ctx.S.confirmarPedido(ctx.params.id);
        ctx.closeOverlay();
        if (r.ok) ctx.toast('Confirmaste el pedido #' + r.pedido.id + '. Ahora asignale el equipo.');
        else ctx.toast(r.error, 'error');
      },
      rechazar(ctx) { ctx.overlay({ kind: 'sheet', name: 'rechazo' }); },
    },
    sheets: {
      rechazo(ctx) {
        return '<h3>Rechazar el pedido #' + ctx.params.id + '</h3>' +
          '<p class="muted small" style="margin:4px 0 0">El cliente va a ver este motivo en su pedido.</p>' +
          '<form class="stack" data-form="rechazo" style="margin-top:14px" novalidate>' +
          UI.field(ctx, { id: 'motivo', label: 'Motivo', type: 'textarea', placeholder: 'Por ejemplo: no tenemos vehículos libres ese día.' }) +
          '<div class="row-2"><button type="button" class="btn ghost" data-act="cerrar">Cancelar</button>' +
          '<button class="btn danger" type="submit">Rechazar</button></div></form>';
      },
    },
    forms: {
      rechazo(ctx, v) {
        const r = ctx.S.rechazarPedido(ctx.params.id, v.motivo);
        ctx.result(r, 'rechazo', v, () => { ctx.closeOverlay(); ctx.toast('Rechazaste el pedido. El cliente ve el motivo.'); });
      },
    },
  };

  Screens.admAsignar = {
    render(ctx) {
      const S = ctx.S, L = ctx.L;
      const p = S.pedido(ctx.params.id);
      if (!p) return noExiste('Asignar equipo', 'No encontramos ese pedido');
      if (!['Confirmado', 'Asignado'].includes(p.estado)) {
        return '<div class="scr">' + UI.appbar({ title: 'Asignar equipo', sub: 'Pedido #' + p.id }) + '<div class="content">' +
          UI.empty('info', 'Este pedido no se puede asignar', 'Solo se asigna equipo a pedidos confirmados que todavía no empezaron.') + '</div></div>';
      }
      const choferes = S.empleadosLibres('Chofer', p.fecha, p.id);
      const ayudantes = S.empleadosLibres('Ayudante de Carga', p.fecha, p.id);
      const vehiculos = S.vehiculosLibres(p.fecha, p.id);
      const materiales = [...new Set(p.servicios.flatMap((id) => (S.servicio(id) || { materiales: [] }).materiales))];
      const peso = UI.pesoTotal(p);
      const f = ctx.ui.form && ctx.ui.form.name === 'asignar' ? ctx.ui.form.values : null;
      const lista = (x) => [].concat(x || []).map(String);
      const selChofer = String(f ? f.chofer || '' : p.choferDni || '');
      const selAyud = f ? lista(f.ayudantes) : p.ayudantes.map(String);
      const selPat = f ? f.patente || '' : p.patente;
      const selMat = f ? lista(f.materiales) : (p.materiales.length ? p.materiales : materiales);
      const err = (k) => (ctx.err(k) ? '<div class="ferr">' + esc(ctx.err(k)) + '</div>' : '');
      return '<div class="scr">' + UI.appbar({ title: 'Asignar equipo', sub: 'Pedido #' + p.id + ' · ' + esc(L.diaRelativo(p.fecha, ctx.hoy)) }) +
        '<div class="content"><form id="form-asignar" class="stack" data-form="asignar" novalidate>' +
        '<div class="card"><div class="row"><div><b>' + esc(UI.nombresServicios(S, p)) + '</b><div class="vmodel">' +
        esc(UI.corto(p.origen)) + ' → ' + esc(UI.corto(p.destino)) + '</div></div><span class="tag">' + icon('weight', 13) +
        peso.toLocaleString('es-AR') + ' kg</span></div></div>' +
        '<div class="section-title"><h3>Chofer</h3><span class="small muted">Libres ese día</span></div>' + err('chofer') +
        (choferes.length ? '<div class="opts">' + choferes.map((u) => UI.opt({
          name: 'chofer', value: u.dni, checked: selChofer === String(u.dni), title: esc(UI.nombreDe(u)),
          sub: 'Chofer' + (S.state.vehiculos.some((v) => v.chofer === u.dni) ? ' · maneja el ' + esc(S.state.vehiculos.find((v) => v.chofer === u.dni).patente) : ''),
        })).join('') + '</div>' : UI.empty('user', 'No hay choferes libres ese día', '')) +
        '<div class="section-title"><h3>Ayudantes de carga</h3><span class="small muted">Podés elegir varios</span></div>' + err('ayudantes') +
        (ayudantes.length ? '<div class="opts">' + ayudantes.map((u) => UI.opt({
          check: true, name: 'ayudantes', value: u.dni, checked: selAyud.includes(String(u.dni)), title: esc(UI.nombreDe(u)), sub: 'Ayudante de carga',
        })).join('') + '</div>' : '<p class="muted small" style="margin:0">No hay ayudantes libres ese día.</p>') +
        '<div class="section-title"><h3>Vehículo</h3></div>' + err('patente') +
        '<div class="opts">' + vehiculos.map((v) => UI.opt({
          name: 'patente', value: v.patente, checked: selPat === v.patente, title: esc(v.tipo),
          sub: esc(v.marcaModelo) + ' · ' + v.kg.toLocaleString('es-AR') + ' kg' + (v.kg < peso ? ' · <b style="display:inline;color:var(--rojo-osc)">no alcanza</b>' : ''),
          right: '<span class="plate sm">' + esc(v.patente) + '</span>',
        })).join('') + '</div>' +
        '<div class="section-title"><h3>Materiales</h3></div>' +
        '<div class="seg">' + materiales.map((m) => UI.opt({ check: true, name: 'materiales', value: m, checked: selMat.includes(m), title: esc(m) })).join('') + '</div>' +
        '</form></div>' +
        '<div class="bottom-bar"><button class="btn primary" type="submit" form="form-asignar">Guardar asignación</button></div></div>';
    },
    forms: {
      asignar(ctx, v, fd) {
        const datos = { choferDni: fd.get('chofer'), ayudantes: fd.getAll('ayudantes'), patente: fd.get('patente'), materiales: fd.getAll('materiales') };
        const r = ctx.S.asignarRecursos(ctx.params.id, datos);
        const valores = { chofer: datos.choferDni || '', ayudantes: datos.ayudantes, patente: datos.patente || '', materiales: datos.materiales };
        ctx.result(r, 'asignar', valores, () => { ctx.back(); ctx.toast('Guardamos el equipo del pedido #' + r.pedido.id + '.'); });
      },
    },
  };

  Screens.admCobro = {
    render(ctx) {
      const S = ctx.S, L = ctx.L;
      const p = S.pedido(ctx.params.id);
      if (!p) return noExiste('Registrar cobro', 'No encontramos ese pedido');
      const c = S.usuario(p.clienteDni);
      const total = S.total(p), cobrado = S.cobrado(p), saldo = total - cobrado;
      const cobros = S.cobrosDe(p);
      const metodo = ctx.val('metodo', 'Efectivo');
      return '<div class="scr">' + UI.appbar({ title: 'Registrar cobro', sub: 'Pedido #' + p.id + ' · ' + esc(UI.nombreDe(c)) }) +
        '<div class="content"><div class="stack">' +
        '<div class="card"><div class="sum"><div class="l"><span>Total del pedido</span><span>' + L.money(total) + '</span></div>' +
        '<div class="l"><span>Ya cobrado</span><span class="pagado">' + L.money(cobrado) + '</span></div>' +
        '<div class="l total"><span>Saldo</span><span class="' + (saldo > 0 ? 'saldo' : 'pagado') + '">' + L.money(saldo) + '</span></div></div></div>' +
        (saldo <= 0 ? '<div class="banner ok">' + icon('check', 18) + '<span>Este pedido ya está pagado.</span></div>'
          : '<form class="stack" data-form="cobro" id="form-cobro" novalidate>' + UI.formError(ctx) +
          UI.field(ctx, { id: 'monto', label: 'Monto que pagó', type: 'number', mode: 'numeric', icon: 'money', def: String(saldo), hint: 'Puede ser un pago parcial.' }) +
          '<div class="field"><span class="lbl">Cómo pagó</span><div class="seg">' + S.state.metodosPago.map((m) =>
            UI.opt({ name: 'metodo', value: m, checked: metodo === m, title: esc(m) })).join('') + '</div></div>' +
          '<button class="btn primary" type="submit">Registrar cobro</button></form>') +
        (cobros.length ? '<div class="card"><h4>Cobros anteriores</h4><div class="sum">' + cobros.map((x) =>
          '<div class="l"><span>' + esc(L.diaRelativo(x.fecha, ctx.hoy)) + ' · ' + esc(x.metodo) + '</span><span>' + L.money(x.monto) + '</span></div>').join('') +
          '</div></div>' : '') +
        '</div></div></div>';
    },
    forms: {
      cobro(ctx, v) {
        const r = ctx.S.registrarCobro(ctx.params.id, v.monto, v.metodo);
        ctx.result(r, 'cobro', v, () => {
          ctx.back();
          ctx.toast('Registraste ' + ctx.L.money(r.cobranza.monto) + ' (' + r.cobranza.metodo.toLowerCase() + ').');
        });
      },
    },
  };

  // ---------- vehículos: el CRUD de la consigna ----------
  const FILTROS_VEH = [['todos', 'Todos'], ['Disponible', 'Disponibles'], ['En Viaje', 'En viaje'], ['En Mantenimiento', 'En mantenimiento'], ['Fuera de Servicio', 'Fuera de servicio']];

  const accionesVehiculo = {
    baja(ctx, el) {
      const v = ctx.S.vehiculo(el.dataset.p);
      ctx.overlay({ kind: 'confirm', danger: true, icon: 'trash', title: '¿Dar de baja el ' + v.patente + '?', confirm: 'Dar de baja',
        act: 'baja-ok', data: { p: v.patente },
        text: 'El ' + esc(v.marcaModelo) + ' queda <b>fuera de servicio</b> y no se ofrece para nuevos pedidos. Lo podés volver a habilitar editando su estado.' });
    },
    'baja-ok'(ctx, el) {
      const r = ctx.S.bajaVehiculo(el.dataset.p);
      ctx.closeOverlay();
      if (r.ok) ctx.toast('El ' + r.vehiculo.patente + ' quedó fuera de servicio.');
      else ctx.toast(r.error, 'error');
    },
  };

  function especificaciones(v) {
    return '<div class="specs"><span><b>' + v.kg.toLocaleString('es-AR') + '</b> kg</span><span><b>' + v.m3 + '</b> m³</span><span>' + esc(v.tipo) + '</span></div>';
  }

  Screens.admVehiculos = {
    tone: 'light',
    render(ctx) {
      const S = ctx.S, u = ctx.user;
      const f = ctx.ui.f.admVeh || 'todos';
      const q = (ctx.ui.q.admVeh || '').trim().toLowerCase();
      const base = S.state.vehiculos.filter((v) => !q || (v.patente + ' ' + v.patente.replace(/-/g, '') + ' ' + v.marcaModelo + ' ' + v.tipo).toLowerCase().includes(q));
      const lista = base.filter((v) => f === 'todos' || v.estado === f);
      const disp = S.state.vehiculos.filter((v) => v.estado === 'Disponible').length;
      return '<div class="scr">' + UI.hero({ title: 'Vehículos', sub: UI.plural(S.state.vehiculos.length, 'unidad', 'unidades') + ' · ' + disp + ' disponibles',
        extra: UI.search(ctx, 'admVeh', 'Buscar por patente o modelo') }) +
        '<div class="content" style="padding-bottom:90px"><div class="stack">' +
        UI.chips(FILTROS_VEH.map(([v, t]) => [v, t, base.filter((x) => v === 'todos' || x.estado === v).length]), f, 'admVeh') +
        (lista.length ? lista.map((v) => '<div class="vcard"><div class="row top"><div><span class="plate">' + esc(v.patente) + '</span>' +
          '<div class="vmodel">' + esc(v.marcaModelo) + '</div></div>' + UI.badgeVehiculo(v.estado) + '</div>' + especificaciones(v) +
          '<div class="acts"><button class="act" data-go="adm/vehiculo/' + v.patente + '">' + icon('eye', 15) + 'Ver</button>' +
          '<button class="act" data-go="adm/vehiculo-form/' + v.patente + '">' + icon('edit', 15) + 'Editar</button>' +
          '<button class="act del" data-act="baja" data-p="' + v.patente + '"' + (v.estado === 'Fuera de Servicio' ? ' disabled style="opacity:.45"' : '') + '>' +
          icon('trash', 15) + 'Baja</button></div></div>').join('')
          : UI.empty('truck', 'No hay vehículos con ese filtro', q ? 'Probá con otra patente o modelo.' : 'Elegí otro filtro arriba.')) +
        '</div></div>' +
        '<button class="fab" data-go="adm/vehiculo-form/nuevo" aria-label="Agregar vehículo">' + icon('plus', 26) + '</button>' +
        UI.tabbar(u.rol, 'adm/vehiculos') + '</div>';
    },
    acts: accionesVehiculo,
  };

  Screens.admVehiculo = {
    tone: 'light',
    render(ctx) {
      const S = ctx.S, L = ctx.L;
      const v = S.vehiculo(ctx.params.id);
      if (!v) return noExiste('Vehículo', 'No encontramos ese vehículo');
      const chofer = v.chofer ? S.usuario(v.chofer) : null;
      const proximos = S.state.pedidos.filter((p) => p.patente === v.patente && S.activo(p)).sort((a, b) => (a.fecha < b.fecha ? -1 : 1));
      return '<div class="scr"><header class="hero">' + UI.speed +
        '<div class="hero-back"><button class="icon-btn" data-back aria-label="Volver">' + icon('back', 22) + '</button><span class="small">Vehículos</span></div>' +
        '<h1 class="sr">Vehículo ' + esc(v.patente) + '</h1>' +
        '<div class="hero-row" style="align-items:flex-end"><div><span class="plate lg">' + esc(v.patente) + '</span>' +
        '<p style="font-size:15px;margin-top:10px">' + esc(v.marcaModelo) + '</p></div>' +
        UI.badgeVehiculo(v.estado).replace('class="badge', 'class="badge on-grad') + '</div></header>' +
        '<div class="content"><div class="stack">' +
        '<div class="card"><h4>Datos de la unidad</h4>' +
        UI.kv('Tipo', esc(v.tipo)) + UI.kv('Capacidad de carga', v.kg.toLocaleString('es-AR') + ' kg') + UI.kv('Volumen', v.m3 + ' m³') +
        UI.kv('Kilometraje', v.km.toLocaleString('es-AR') + ' km') + UI.kv('Año', String(v.anio)) +
        UI.kv('Chofer habitual', chofer ? esc(UI.nombreDe(chofer)) : 'Sin chofer fijo') +
        (v.obs ? UI.kv('Observaciones', esc(v.obs)) : '') + '</div>' +
        '<div class="section-title"><h3>Próximos pedidos</h3></div>' +
        (proximos.length ? proximos.map((p) => UI.pedidoCard(ctx, p, { go: 'adm/pedido/' + p.id, cliente: true })).join('')
          : '<p class="muted small" style="margin:0">No tiene pedidos pendientes.</p>') +
        '</div></div>' +
        '<div class="bottom-bar">' + (v.estado !== 'Fuera de Servicio'
          ? '<button class="btn danger-o" data-act="baja" data-p="' + v.patente + '">' + icon('trash', 18) + 'Dar de baja</button>' : '') +
        '<button class="btn primary" data-go="adm/vehiculo-form/' + v.patente + '">' + icon('edit', 18) + 'Editar</button></div></div>';
    },
    acts: accionesVehiculo,
  };

  Screens.admVehiculoForm = {
    render(ctx) {
      const S = ctx.S;
      const nuevo = ctx.params.id === 'nuevo';
      const v = nuevo ? null : S.vehiculo(ctx.params.id);
      if (!nuevo && !v) return noExiste('Editar vehículo', 'No encontramos ese vehículo');
      const d = v || { patente: '', marcaModelo: '', tipo: '', kg: '', m3: '', estado: 'Disponible', km: '0', anio: '', chofer: '', obs: '' };
      const choferes = S.state.usuarios.filter((u) => u.rol === 'Chofer' && u.activo);
      return '<div class="scr">' + UI.appbar({ title: nuevo ? 'Agregar vehículo' : 'Editar vehículo', sub: nuevo ? 'Todos los campos son obligatorios salvo el chofer y las observaciones' : esc(v.patente) }) +
        '<div class="content"><form id="form-veh" class="stack" data-form="vehiculo" novalidate>' + UI.formError(ctx) +
        UI.field(ctx, { id: 'patente', label: 'Patente', def: d.patente, disabled: !nuevo, placeholder: 'AB 123 CD', hint: nuevo ? 'Formato Mercosur (AB 123 CD) o viejo (ABC 123).' : 'La patente no se puede cambiar.' }) +
        UI.field(ctx, { id: 'marcaModelo', label: 'Marca y modelo', def: d.marcaModelo, placeholder: 'Ej.: Renault Master Furgón' }) +
        UI.field(ctx, { id: 'tipo', label: 'Tipo de vehículo', type: 'select', def: d.tipo, placeholder: 'Elegí el tipo', options: S.state.tiposVehiculo }) +
        '<div class="row-2">' + UI.field(ctx, { id: 'kg', label: 'Capacidad', type: 'number', mode: 'numeric', def: String(d.kg), suf: 'kg' }) +
        UI.field(ctx, { id: 'm3', label: 'Volumen', type: 'number', mode: 'decimal', def: String(d.m3), suf: 'm³' }) + '</div>' +
        '<div class="row-2">' + UI.field(ctx, { id: 'km', label: 'Kilometraje', type: 'number', mode: 'numeric', def: String(d.km), suf: 'km' }) +
        UI.field(ctx, { id: 'anio', label: 'Año', type: 'number', mode: 'numeric', def: String(d.anio), placeholder: '2024' }) + '</div>' +
        UI.field(ctx, { id: 'estado', label: 'Estado', type: 'select', def: d.estado, options: S.state.estadosVehiculo }) +
        UI.field(ctx, { id: 'chofer', label: 'Chofer habitual', type: 'select', def: String(d.chofer || ''),
          options: [['', 'Sin chofer fijo']].concat(choferes.map((u) => [String(u.dni), UI.nombreDe(u)])) }) +
        UI.field(ctx, { id: 'obs', label: 'Observaciones', type: 'textarea', def: d.obs, rows: 2, placeholder: 'Opcional' }) +
        '</form></div>' +
        '<div class="bottom-bar"><button class="btn ghost" data-back>Cancelar</button><button class="btn primary" type="submit" form="form-veh">Guardar</button></div></div>';
    },
    forms: {
      vehiculo(ctx, v) {
        const nuevo = ctx.params.id === 'nuevo';
        const r = ctx.S.guardarVehiculo(v, nuevo ? null : ctx.params.id);
        ctx.result(r, 'vehiculo', v, () => {
          if (nuevo) ctx.go('adm/vehiculo/' + r.vehiculo.patente, { replace: true });
          else ctx.back();
          ctx.toast(nuevo ? 'Agregaste el ' + r.vehiculo.patente + '.' : 'Guardaste los cambios del ' + r.vehiculo.patente + '.');
        });
      },
    },
  };

  // ---------- usuarios (Hito 2) ----------
  const FILTROS_USU = [['todos', 'Todos'], ['Administrador', 'Administradores'], ['Chofer', 'Choferes'], ['Ayudante de Carga', 'Ayudantes'],
    ['Cliente', 'Clientes'], ['baja', 'De baja']];

  const avatarUsuario = (ctx, u, extra) => '<span class="av ' + UI.claseRol(u.rol) + (u.activo ? '' : ' baja') + (extra || '') + '">' +
    ctx.L.iniciales(u.nombre, u.apellido) + '</span>';

  Screens.admUsuarios = {
    tone: 'light',
    render(ctx) {
      const S = ctx.S, me = ctx.user;
      const f = ctx.ui.f.admUsu || 'todos';
      const q = (ctx.ui.q.admUsu || '').trim().toLowerCase();
      const pasa = (u, filtro) => filtro === 'todos' || (filtro === 'baja' ? !u.activo : u.rol === filtro && u.activo);
      const base = S.state.usuarios.filter((u) => !q || (UI.nombreDe(u) + ' ' + u.usuario + ' ' + u.dni + ' ' + u.correo).toLowerCase().includes(q))
        .sort((a, b) => a.apellido.localeCompare(b.apellido, 'es'));
      const lista = base.filter((u) => pasa(u, f));
      const activos = S.state.usuarios.filter((u) => u.activo).length;
      return '<div class="scr">' + UI.hero({ title: 'Usuarios', sub: activos + ' activos · ' + (S.state.usuarios.length - activos) + ' de baja',
        extra: UI.search(ctx, 'admUsu', 'Buscar por nombre, usuario o DNI') }) +
        '<div class="content" style="padding-bottom:90px"><div class="stack tight">' +
        UI.chips(FILTROS_USU.map(([v, t]) => [v, t, base.filter((u) => pasa(u, v)).length]), f, 'admUsu') +
        (lista.length ? lista.map((u) => '<button class="ucard" data-go="adm/usuario/' + u.dni + '">' + avatarUsuario(ctx, u) +
          '<span style="min-width:0"><b>' + esc(UI.nombreDe(u)) + (u.dni === me.dni ? ' <span class="small muted">(vos)</span>' : '') + '</b><small>' +
          esc(u.usuario) + ' · ' + esc(u.rol) + '</small></span>' +
          (!u.activo ? UI.badgeUsuario(u) : u.debeCambiar ? '<span class="badge b-clave">Clave temporal</span>' : icon('chev', 18)) +
          '</button>').join('')
          : UI.empty('users', 'No hay usuarios con ese filtro', q ? 'Probá con otra búsqueda.' : '')) +
        '</div></div>' +
        '<button class="fab" data-go="adm/usuario-nuevo" aria-label="Nuevo usuario">' + icon('plus', 26) + '</button>' +
        UI.tabbar(me.rol, 'adm/usuarios') + '</div>';
    },
  };

  Screens.admUsuarioNuevo = {
    render(ctx) {
      const S = ctx.S, L = ctx.L;
      const nom = ctx.val('nombre', ''), ape = ctx.val('apellido', '');
      const previa = nom || ape ? L.username(ape, nom, S.state.usuarios.map((u) => u.usuario)) : '—';
      return '<div class="scr">' + UI.appbar({ title: 'Nuevo usuario', sub: 'Empleado o cliente' }) +
        '<div class="content"><form id="form-alta" class="stack" data-form="alta" novalidate>' + UI.formError(ctx) +
        '<div class="row-2">' + UI.field(ctx, { id: 'nombre', label: 'Nombre', live: 'previa' }) +
        UI.field(ctx, { id: 'apellido', label: 'Apellido', live: 'previa' }) + '</div>' +
        '<div class="row-2">' + UI.field(ctx, { id: 'dni', label: 'DNI', mode: 'numeric', placeholder: 'Sin puntos' }) +
        UI.field(ctx, { id: 'telefono', label: 'Teléfono', type: 'tel', placeholder: '387 5550000' }) + '</div>' +
        UI.field(ctx, { id: 'correo', label: 'Correo electrónico', type: 'email', icon: 'mail' }) +
        UI.field(ctx, { id: 'rol', label: 'Rol', type: 'select', placeholder: 'Elegí el rol', options: S.state.roles }) +
        '<div class="card row"><div><small class="muted">Usuario que se va a crear</small>' +
        '<div style="font-size:19px;font-weight:700" id="prev-user" aria-live="polite">' + esc(previa) + '</div></div>' +
        '<span class="av">' + icon('user', 20) + '</span></div>' +
        '<div class="banner info">' + icon('key', 18) + '<span>Se crea con una contraseña temporal que tiene que cambiar la primera vez que entre.</span></div>' +
        '</form></div>' +
        '<div class="bottom-bar"><button class="btn primary" type="submit" form="form-alta">Crear usuario</button></div></div>';
    },
    live: {
      previa(ctx, el) {
        const f = el.form;
        const nom = f.elements.nombre.value, ape = f.elements.apellido.value;
        const out = document.getElementById('prev-user');
        if (out) out.textContent = nom || ape ? ctx.L.username(ape, nom, ctx.S.state.usuarios.map((u) => u.usuario)) : '—';
      },
    },
    forms: {
      alta(ctx, v) {
        const r = ctx.S.altaUsuario(v);
        ctx.result(r, 'alta', v, () => {
          ctx.go('adm/usuario/' + r.usuario.dni, { replace: true });
          ctx.overlay({ kind: 'sheet', name: 'clave', data: { nuevo: '1', temporal: r.temporal } });
        });
      },
    },
  };

  function fechaDato(ctx, iso) {
    return iso ? esc(ctx.L.diaRelativo(iso, ctx.hoy)) : '—';
  }

  Screens.admUsuario = {
    tone: 'light',
    render(ctx) {
      const S = ctx.S, L = ctx.L;
      const u = S.usuario(ctx.params.id);
      if (!u) return noExiste('Usuario', 'No encontramos ese usuario');
      const yo = u.dni === ctx.user.dni;
      return '<div class="scr"><header class="hero" style="text-align:center;padding-bottom:22px">' + UI.speed +
        '<div class="hero-back" style="text-align:left"><button class="icon-btn" data-back aria-label="Volver">' + icon('back', 22) + '</button><span class="small">Usuarios</span></div>' +
        '<div style="position:relative;z-index:1"><div class="avatar lg">' + L.iniciales(u.nombre, u.apellido) + '</div>' +
        '<h1 style="font-size:20px">' + esc(UI.nombreDe(u)) + '</h1><p>' + esc(u.usuario) + ' · ' + esc(u.rol) + '</p>' +
        '<div class="tags" style="justify-content:center;margin-top:10px">' + UI.badgeUsuario(u).replace('class="badge', 'class="badge on-grad') +
        (u.debeCambiar && u.activo ? '<span class="badge b-clave on-grad">Clave temporal</span>' : '') + '</div></div></header>' +
        '<div class="content"><div class="stack">' +
        (yo ? '<div class="banner info">' + icon('shield', 18) + '<span>Es tu usuario: no podés darte de baja ni cambiar tu propio rol.</span></div>' : '') +
        '<div class="card"><h4>Datos</h4>' + UI.kv('DNI', u.dni.toLocaleString('es-AR')) + UI.kv('Correo', esc(u.correo)) +
        UI.kv('Teléfono', esc(telefono(u.telefono))) + UI.kv('Fecha de alta', fechaDato(ctx, u.alta)) +
        UI.kv('Última modificación', fechaDato(ctx, u.modificado)) + UI.kv('Último acceso', fechaDato(ctx, u.ultimoAcceso)) +
        (u.baja ? UI.kv('Fecha de baja', fechaDato(ctx, u.baja)) : '') + '</div>' +
        '<div class="card pad-0"><div class="actions-list">' +
        '<button class="action-row" data-act="sheet" data-v="correo"><span class="ic">' + icon('mail', 18) + '</span><span>Modificar correo</span>' + icon('chev', 18) + '</button>' +
        '<button class="action-row" data-act="sheet" data-v="rol"><span class="ic">' + icon('users', 18) + '</span><span>Cambiar rol</span>' + icon('chev', 18) + '</button>' +
        '<button class="action-row" data-act="restablecer"><span class="ic">' + icon('key', 18) + '</span><span>Restablecer contraseña</span>' + icon('chev', 18) + '</button>' +
        (u.activo
          ? '<button class="action-row danger" data-act="baja-u"><span class="ic">' + icon('trash', 18) + '</span><span>Dar de baja</span></button>'
          : '<button class="action-row ok" data-act="reactivar"><span class="ic">' + icon('refresh', 18) + '</span><span>Reactivar usuario</span></button>') +
        '</div></div></div></div></div>';
    },
    acts: {
      sheet(ctx, el) { ctx.overlay({ kind: 'sheet', name: el.dataset.v }); },
      restablecer(ctx) {
        const u = ctx.S.usuario(ctx.params.id);
        ctx.overlay({ kind: 'confirm', icon: 'key', title: '¿Restablecer la contraseña?', confirm: 'Restablecer', act: 'restablecer-ok',
          text: 'Le generamos a ' + esc(UI.nombreDe(u)) + ' una contraseña temporal. La va a tener que cambiar cuando entre.' });
      },
      'restablecer-ok'(ctx) {
        const r = ctx.S.restablecerClave(ctx.params.id);
        if (r.ok) ctx.overlay({ kind: 'sheet', name: 'clave', data: { temporal: r.temporal } });
        else { ctx.closeOverlay(); ctx.toast(r.error, 'error'); }
      },
      'baja-u'(ctx) {
        const S = ctx.S, u = S.usuario(ctx.params.id);
        const e = ctx.L.errorBaja(ctx.user.dni, u, S.state.usuarios);
        if (e) { ctx.toast(e, 'error'); return; }
        ctx.overlay({ kind: 'confirm', danger: true, icon: 'trash', title: '¿Dar de baja a ' + UI.nombreDe(u) + '?', confirm: 'Dar de baja', act: 'baja-u-ok',
          text: 'No va a poder iniciar sesión. Sus datos y su historial se conservan, y lo podés reactivar cuando quieras.' });
      },
      'baja-u-ok'(ctx) {
        const r = ctx.S.bajaUsuario(ctx.params.id);
        ctx.closeOverlay();
        if (r.ok) ctx.toast('Diste de baja a ' + UI.nombreDe(r.usuario) + '.');
        else ctx.toast(r.error, 'error');
      },
      reactivar(ctx) {
        const r = ctx.S.reactivarUsuario(ctx.params.id);
        if (r.ok) { ctx.refresh(); ctx.toast('Reactivaste a ' + UI.nombreDe(r.usuario) + '.'); } else ctx.toast(r.error, 'error');
      },
    },
    sheets: {
      correo(ctx) {
        const u = ctx.S.usuario(ctx.params.id);
        return '<h3>Modificar correo</h3><p class="muted small" style="margin:4px 0 0">Según el Hito 2, de un usuario solo se modifica el correo.</p>' +
          '<form class="stack" data-form="correo" style="margin-top:14px" novalidate>' +
          UI.field(ctx, { id: 'correo', label: 'Correo nuevo', type: 'email', icon: 'mail', def: u.correo }) +
          '<div class="row-2"><button type="button" class="btn ghost" data-act="cerrar">Cancelar</button><button class="btn primary" type="submit">Guardar</button></div></form>';
      },
      rol(ctx) {
        const S = ctx.S, u = S.usuario(ctx.params.id);
        const sel = ctx.val('rol', u.rol);
        return '<h3>Cambiar rol</h3><p class="muted small" style="margin:4px 0 0">' + esc(UI.nombreDe(u)) + ' es ' + esc(u.rol).toLowerCase() + '.</p>' +
          '<form class="stack" data-form="rol" style="margin-top:14px" novalidate>' + UI.formError(ctx) +
          '<div class="opts">' + S.state.roles.map((r) => UI.opt({ name: 'rol', value: r, checked: sel === r, title: esc(r) })).join('') + '</div>' +
          '<div class="row-2"><button type="button" class="btn ghost" data-act="cerrar">Cancelar</button><button class="btn primary" type="submit">Guardar rol</button></div></form>';
      },
      clave(ctx, data) {
        const u = ctx.S.usuario(ctx.params.id);
        return '<div class="stack center"><div class="ok-big">' + icon('key', 34) + '</div>' +
          '<h3>' + (data.nuevo ? 'Usuario creado' : 'Contraseña restablecida') + '</h3>' +
          '<p class="muted" style="margin:0">Pasale estos datos a ' + esc(UI.nombreDe(u)) + '. Cuando entre le vamos a pedir que cambie la contraseña.</p>' +
          '<div class="card" style="text-align:left">' + UI.kv('Usuario', esc(u.usuario)) + UI.kv('Contraseña temporal', '<span class="num" style="user-select:all">' + esc(data.temporal) + '</span>') + '</div>' +
          '<button class="btn primary" data-act="cerrar">Listo</button></div>';
      },
    },
    forms: {
      correo(ctx, v) {
        const r = ctx.S.modificarCorreo(ctx.params.id, v.correo);
        if (!r.ok) { ctx.ui.form = { name: 'correo', values: v, errores: { correo: r.error } }; ctx.refresh(); return; }
        ctx.closeOverlay();
        ctx.toast('Actualizaste el correo de ' + UI.nombreDe(r.usuario) + '.');
      },
      rol(ctx, v) {
        const r = ctx.S.cambiarRol(ctx.params.id, v.rol);
        ctx.result(r, 'rol', v, () => { ctx.closeOverlay(); ctx.toast(UI.nombreDe(r.usuario) + ' ahora es ' + r.usuario.rol.toLowerCase() + '.'); });
      },
    },
  };

  // ---------- servicios ----------
  Screens.admServicios = {
    render(ctx) {
      const S = ctx.S, L = ctx.L;
      return '<div class="scr">' + UI.appbar({ title: 'Servicios', sub: 'Catálogo y precios base' }) +
        '<div class="content" style="padding-bottom:90px"><div class="stack">' +
        '<div class="banner info">' + icon('info', 18) + '<span>El total de cada pedido es la suma de los precios base de sus servicios.</span></div>' +
        S.state.servicios.map((s) => '<button class="scard" data-go="adm/servicio-form/' + s.id + '"><div class="row"><b>' + esc(s.tipo) +
          '</b><b class="num">' + L.money(s.precio) + '</b></div>' + (s.detalle ? '<span class="small muted">' + esc(s.detalle) + '</span>' : '') +
          '<div class="tags">' + s.materiales.map((m) => '<span class="tag">' + esc(m) + '</span>').join('') + '</div></button>').join('') +
        '</div></div>' +
        '<button class="fab" style="bottom:calc(24px + var(--hb))" data-go="adm/servicio-form/nuevo" aria-label="Agregar servicio">' + icon('plus', 26) + '</button></div>';
    },
  };

  Screens.admServicioForm = {
    render(ctx) {
      const nuevo = ctx.params.id === 'nuevo';
      const s = nuevo ? null : ctx.S.servicio(ctx.params.id);
      if (!nuevo && !s) return noExiste('Servicio', 'No encontramos ese servicio');
      const d = s || { tipo: '', precio: '', detalle: '', materiales: [] };
      return '<div class="scr">' + UI.appbar({ title: nuevo ? 'Nuevo servicio' : 'Editar servicio', sub: nuevo ? '' : esc(s.tipo) }) +
        '<div class="content"><form id="form-serv" class="stack" data-form="servicio" novalidate>' + UI.formError(ctx) +
        UI.field(ctx, { id: 'tipo', label: 'Nombre del servicio', def: d.tipo, placeholder: 'Ej.: Guardamuebles' }) +
        UI.field(ctx, { id: 'precio', label: 'Precio base', type: 'number', mode: 'numeric', icon: 'money', def: String(d.precio) }) +
        UI.field(ctx, { id: 'detalle', label: 'Descripción corta', def: d.detalle, placeholder: 'Qué incluye, en una línea' }) +
        UI.field(ctx, { id: 'materiales', label: 'Materiales', type: 'textarea', rows: 2, def: d.materiales.join(', '), hint: 'Separados por comas: Mantas, Film, Cintas' }) +
        '</form></div>' +
        '<div class="bottom-bar"><button class="btn ghost" data-back>Cancelar</button><button class="btn primary" type="submit" form="form-serv">Guardar</button></div></div>';
    },
    forms: {
      servicio(ctx, v) {
        const nuevo = ctx.params.id === 'nuevo';
        const r = ctx.S.guardarServicio(Object.assign({}, v, { id: nuevo ? null : ctx.params.id }));
        ctx.result(r, 'servicio', v, () => { ctx.back(); ctx.toast(nuevo ? 'Agregaste ' + r.servicio.tipo + '.' : 'Guardaste ' + r.servicio.tipo + '.'); });
      },
    },
  };
})(window);
