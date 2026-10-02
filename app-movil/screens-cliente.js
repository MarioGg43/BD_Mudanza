/* Pantallas del cliente: inicio, pedir mudanza (5 pasos), mis pedidos y detalle. */
(function (root) {
  'use strict';
  const Screens = root.Screens = root.Screens || {};
  const UI = root.UI;
  const { icon, esc } = UI;

  const PASOS = ['¿Cuándo y dónde?', '¿Qué servicio necesitás?', 'Elegí el vehículo', '¿Qué vas a mudar?', 'Revisá y confirmá'];

  function nuevoDraft(ctx) {
    return { step: 1, fecha: ctx.L.sumarDias(ctx.hoy, 3), origen: '', destino: '', servicios: [], patente: null, inventario: [] };
  }
  root.nuevoDraft = nuevoDraft;

  function avatarBtn(ctx) {
    return '<button class="avatar" data-go="perfil" aria-label="Mi perfil">' + ctx.L.iniciales(ctx.user.nombre, ctx.user.apellido) + '</button>';
  }

  function noEncontrado(titulo) {
    return '<div class="scr">' + UI.appbar({ title: titulo }) + '<div class="content">' +
      UI.empty('info', 'No encontramos ese pedido', 'Puede que se haya borrado al reiniciar la demo.') + '</div></div>';
  }

  // ---------- inicio ----------
  Screens.cliInicio = {
    tone: 'light',
    render(ctx) {
      const S = ctx.S, u = ctx.user;
      const activos = S.pedidosDeCliente(u.dni).filter(S.activo);
      return '<div class="scr">' + UI.hero({ title: 'Hola, ' + u.nombre, sub: '¿Qué mudamos esta vez?', right: avatarBtn(ctx) }) +
        '<div class="content"><div class="stack">' +
        '<button class="cta" data-act="nuevo-pedido"><img class="truck" src="img/icono.png" alt="">' +
        '<b>Pedir una mudanza</b><small>Elegí la fecha, el servicio y el vehículo en cinco pasos.</small>' +
        '<span class="go">' + icon('chev', 22) + '</span></button>' +
        '<div class="section-title"><h3>En curso</h3><button class="link" data-go="cli/pedidos">Ver todos</button></div>' +
        (activos.length
          ? activos.map((p) => UI.pedidoCard(ctx, p, { go: 'cli/pedido/' + p.id })).join('')
          : UI.empty('box', 'No tenés mudanzas en curso', 'Cuando pidas una, vas a ver acá en qué estado está.')) +
        '<div class="section-title"><h3>Nuestros servicios</h3></div>' +
        '<div class="hscroll">' + S.state.servicios.map((s) =>
          '<div class="mini"><b>' + esc(s.tipo) + '</b><span>' + ctx.L.money(s.precio) + '</span><small>' + esc(s.detalle || '') + '</small></div>').join('') + '</div>' +
        '</div></div>' + UI.tabbar(u.rol, 'cli/inicio') + '</div>';
    },
    acts: {
      'nuevo-pedido'(ctx) { ctx.ui.draft = nuevoDraft(ctx); ctx.go('cli/pedir'); },
    },
  };

  // ---------- pedir mudanza ----------
  function totalDraft(ctx, d) {
    return d.servicios.reduce((a, id) => a + ((ctx.S.servicio(id) || {}).precio || 0), 0);
  }
  function pesoDraft(d) {
    return d.inventario.reduce((a, i) => a + i.cant * i.peso, 0);
  }

  function paso1(ctx, d) {
    return '<div class="stack">' +
      UI.field(ctx, { id: 'fecha', label: 'Fecha de la mudanza', type: 'date', icon: 'calendar', value: d.fecha, min: ctx.hoy, live: 'draft' }) +
      UI.field(ctx, { id: 'origen', label: 'Desde', icon: 'pin', value: d.origen, live: 'draft', placeholder: 'Calle, número y ciudad',
        hint: 'Por ejemplo: Av. Belgrano 1250, Salta' }) +
      UI.field(ctx, { id: 'destino', label: 'Hasta', icon: 'flag', value: d.destino, live: 'draft', placeholder: 'Calle, número y ciudad' }) +
      '</div>';
  }

  function paso2(ctx, d) {
    const L = ctx.L;
    return '<div class="stack"><p class="muted" style="margin:0">Podés elegir más de uno. El precio final lo confirma la empresa.</p>' +
      (ctx.err('servicios') ? '<div class="ferr">' + esc(ctx.err('servicios')) + '</div>' : '') +
      '<div class="opts">' + ctx.S.state.servicios.map((s) => UI.opt({
        check: true, name: 'servicios', value: s.id, checked: d.servicios.includes(s.id), live: 'servicio',
        title: esc(s.tipo), sub: esc(s.detalle || '') + '<br>Incluye: ' + esc(s.materiales.join(', ').toLowerCase()),
        right: '<span class="price">' + L.money(s.precio) + '</span>',
      })).join('') + '</div>' +
      '<div class="card"><div class="sum"><div class="l total" style="border:none;padding:0"><span>Total estimado</span><span>' +
      L.money(totalDraft(ctx, d)) + '</span></div></div></div></div>';
  }

  function paso3(ctx, d) {
    const libres = ctx.S.vehiculosLibres(d.fecha);
    if (!libres.length) {
      return UI.empty('truck', 'No hay vehículos libres ese día', 'Volvé al paso 1 y probá con otra fecha.');
    }
    return '<div class="stack"><p class="muted" style="margin:0">Estos vehículos están libres el ' + esc(ctx.L.fechaLarga(d.fecha)) + '.</p>' +
      (ctx.err('patente') ? '<div class="ferr">' + esc(ctx.err('patente')) + '</div>' : '') +
      '<div class="opts">' + libres.map((v) => UI.opt({
        name: 'patente', value: v.patente, checked: d.patente === v.patente, live: 'vehiculo',
        title: esc(v.tipo), sub: esc(v.marcaModelo) + '<br>Carga ' + v.kg.toLocaleString('es-AR') + ' kg · ' + v.m3 + ' m³',
        right: '<span class="plate sm">' + esc(v.patente) + '</span>',
      })).join('') + '</div></div>';
  }

  function paso4(ctx, d) {
    const v = ctx.S.vehiculo(d.patente);
    const peso = pesoDraft(d);
    const cap = v ? v.kg : 0;
    const pct = cap ? Math.min(100, Math.round((peso / cap) * 100)) : 0;
    return '<div class="stack">' +
      (d.inventario.length
        ? '<div class="card"><h4>Tu lista</h4><div class="items">' + d.inventario.map((i, n) =>
          '<div class="item"><div class="d"><b>' + esc(i.desc) + '</b><small>' + i.cant + ' × ' + i.peso.toLocaleString('es-AR') + ' kg' +
          (i.fragil ? ' · <span class="tag fragil">' + icon('glass', 12) + 'Frágil</span>' : '') + '</small></div>' +
          '<button type="button" class="x-btn" data-act="quitar-item" data-i="' + n + '" aria-label="Quitar ' + esc(i.desc) + '">' + icon('x', 16) + '</button></div>').join('') +
          '</div></div>'
        : UI.empty('box', 'Todavía no agregaste nada', 'Contanos qué hay que llevar: así elegimos bien el vehículo y el embalaje.')) +
      (ctx.err('inventario') ? '<div class="ferr">' + esc(ctx.err('inventario')) + '</div>' : '') +
      '<div class="card"><h4>Agregar un objeto</h4><div class="stack tight">' +
      UI.field(ctx, { id: 'desc', label: 'Qué es', placeholder: 'Heladera, cajas de libros, sillas…', value: ctx.val('desc', '') }) +
      '<div class="row-2">' +
      UI.field(ctx, { id: 'cant', label: 'Cantidad', type: 'number', mode: 'numeric', value: ctx.val('cant', '1') }) +
      UI.field(ctx, { id: 'peso', label: 'Peso de cada uno', type: 'number', mode: 'decimal', suf: 'kg', value: ctx.val('peso', '') }) +
      '</div>' +
      '<label class="switch"><span>' + icon('glass', 16) + ' Es frágil</span><input type="checkbox" name="fragil"' +
      (ctx.val('fragil', '') ? ' checked' : '') + '><span class="track"></span></label>' +
      '<button type="button" class="btn ghost" data-act="agregar-item">' + icon('plus', 18) + 'Agregar a la lista</button>' +
      '</div></div>' +
      (v ? '<div class="card"><div class="row small"><span>' + icon('weight', 15) + ' ' + peso.toLocaleString('es-AR') + ' kg de ' +
        cap.toLocaleString('es-AR') + ' kg</span><span class="muted">' + esc(v.tipo) + '</span></div>' +
        '<div class="bar' + (peso > cap ? ' over' : '') + '" style="margin-top:8px"><i style="width:' + pct + '%"></i></div></div>' : '') +
      '</div>';
  }

  function paso5(ctx, d) {
    const S = ctx.S, L = ctx.L;
    const v = S.vehiculo(d.patente);
    const p = { origen: d.origen, destino: d.destino };
    return '<div class="stack">' + UI.formError(ctx) +
      '<div class="card"><h4>Cuándo y dónde</h4><div class="stack tight"><div class="meta">' + icon('calendar', 16) +
      '<span style="color:var(--tinta);font-weight:600">' + esc(L.fechaLarga(d.fecha)) + '</span></div>' + UI.ruta(p) + '</div></div>' +
      '<div class="card"><h4>Servicios</h4><div class="sum">' + d.servicios.map((id) => {
        const s = S.servicio(id);
        return '<div class="l"><span>' + esc(s.tipo) + '</span><span>' + L.money(s.precio) + '</span></div>';
      }).join('') + '<div class="l total"><span>Total estimado</span><span>' + L.money(totalDraft(ctx, d)) + '</span></div></div></div>' +
      (v ? '<div class="card"><h4>Vehículo</h4><div class="row"><div><b>' + esc(v.tipo) + '</b><div class="vmodel">' + esc(v.marcaModelo) +
        '</div></div><span class="plate sm">' + esc(v.patente) + '</span></div></div>' : '') +
      '<div class="card"><h4>Qué se lleva</h4><div class="row"><span>' + UI.plural(d.inventario.reduce((a, i) => a + i.cant, 0), 'bulto', 'bultos') +
      ' · ' + pesoDraft(d).toLocaleString('es-AR') + ' kg</span><span class="muted">' +
      UI.plural(d.inventario.filter((i) => i.fragil).length, 'frágil', 'frágiles') + '</span></div></div>' +
      '<div class="banner info">' + icon('info', 18) + '<span>El pedido queda <b>pendiente</b> hasta que la empresa lo confirme. Lo vas a poder seguir en Mis pedidos.</span></div>' +
      '</div>';
  }

  function validarPaso(ctx, d) {
    const e = {};
    if (d.step === 1) {
      if (!d.fecha || d.fecha < ctx.hoy) e.fecha = 'Elegí una fecha de hoy en adelante.';
      if (!d.origen.trim()) e.origen = 'Escribí la dirección de origen.';
      if (!d.destino.trim()) e.destino = 'Escribí la dirección de destino.';
    } else if (d.step === 2) {
      if (!d.servicios.length) e.servicios = 'Elegí al menos un servicio.';
    } else if (d.step === 3) {
      if (!d.patente || !ctx.S.vehiculosLibres(d.fecha).some((v) => v.patente === d.patente)) e.patente = 'Elegí uno de los vehículos libres.';
    } else if (d.step === 4) {
      const v = ctx.S.vehiculo(d.patente);
      if (!d.inventario.length) e.inventario = 'Agregá al menos un objeto a la lista.';
      else if (v && pesoDraft(d) > v.kg) e.inventario = 'Pesa más de lo que carga el vehículo. Volvé al paso 3 y elegí uno más grande.';
    }
    return e;
  }

  function agregarItem(ctx, form) {
    const desc = form.elements.desc.value.trim();
    const cant = Number(form.elements.cant.value);
    const peso = Number(String(form.elements.peso.value).replace(',', '.'));
    const fragil = form.elements.fragil.checked;
    const errores = {};
    if (!desc) errores.desc = 'Escribí qué es.';
    if (!(cant >= 1) || Math.round(cant) !== cant) errores.cant = 'Un número entero, 1 o más.';
    if (!(peso > 0)) errores.peso = 'Escribí cuánto pesa, aunque sea aproximado.';
    if (Object.keys(errores).length) {
      ctx.ui.form = { name: 'paso', values: { desc, cant: form.elements.cant.value, peso: form.elements.peso.value, fragil: fragil ? 'on' : '' }, errores };
    } else {
      ctx.ui.draft.inventario.push({ desc, cant, peso, fragil });
      ctx.ui.form = null;
    }
    ctx.refresh();
    const campo = document.getElementById('f-desc');
    if (campo && !Object.keys(errores).length) campo.focus();
  }

  Screens.cliPedir = {
    tone: 'light',
    render(ctx) {
      const d = ctx.ui.draft || (ctx.ui.draft = nuevoDraft(ctx));
      const cuerpo = [paso1, paso2, paso3, paso4, paso5][d.step - 1](ctx, d);
      return '<div class="scr"><header class="hero">' + UI.speed +
        '<div class="hero-back"><button class="icon-btn" data-act="paso-atras" aria-label="Volver">' + icon('back', 22) + '</button>' +
        '<span class="small">Pedir mudanza · paso ' + d.step + ' de 5</span></div>' +
        '<div class="hero-row"><div><h1>' + PASOS[d.step - 1] + '</h1></div></div>' +
        '<div class="steps" aria-hidden="true">' + [1, 2, 3, 4, 5].map((i) => '<i class="' + (i <= d.step ? 'on' : '') + '"></i>').join('') + '</div></header>' +
        '<div class="content"><form id="form-paso" data-form="paso" novalidate>' + cuerpo + '</form></div>' +
        '<div class="bottom-bar"><button class="btn primary" type="submit" form="form-paso">' +
        (d.step < 5 ? 'Siguiente' + icon('chev', 18) : 'Confirmar pedido') + '</button></div></div>';
    },
    live: {
      draft(ctx, el) { ctx.ui.draft[el.name] = el.value; },
      servicio(ctx, el) {
        const d = ctx.ui.draft, id = Number(el.value);
        d.servicios = el.checked ? d.servicios.concat(id) : d.servicios.filter((x) => x !== id);
        ctx.ui.form = null;
        ctx.refresh();
      },
      vehiculo(ctx, el) { ctx.ui.draft.patente = el.value; ctx.ui.form = null; },
    },
    acts: {
      'paso-atras'(ctx) {
        const d = ctx.ui.draft;
        ctx.ui.form = null;
        if (d && d.step > 1) { d.step--; ctx.scrollTop(); ctx.refresh(); } else ctx.back();
      },
      'agregar-item'(ctx, el) { agregarItem(ctx, el.form); },
      'quitar-item'(ctx, el) { ctx.ui.draft.inventario.splice(Number(el.dataset.i), 1); ctx.refresh(); },
    },
    forms: {
      paso(ctx, v, fd, form) {
        const d = ctx.ui.draft;
        if (d.step === 4 && form.elements.desc && form.elements.desc.value.trim()) { agregarItem(ctx, form); return; }
        if (d.step === 1) { d.fecha = v.fecha || ''; d.origen = v.origen || ''; d.destino = v.destino || ''; }
        const errores = validarPaso(ctx, d);
        if (Object.keys(errores).length) {
          ctx.ui.form = { name: 'paso', values: {}, errores };
          ctx.refresh();
          return;
        }
        ctx.ui.form = null;
        if (d.step < 5) { d.step++; ctx.scrollTop(); ctx.refresh(); return; }
        const r = ctx.S.crearPedido(d);
        if (r.ok) {
          ctx.ui.draft = null;
          ctx.go('cli/enviado/' + r.pedido.id, { replace: true });
        } else {
          const primero = r.error || Object.values(r.errores || {})[0];
          ctx.ui.form = { name: 'paso', values: {}, error: primero };
          ctx.refresh();
        }
      },
    },
  };

  Screens.cliEnviado = {
    render(ctx) {
      const p = ctx.S.pedido(ctx.params.id);
      if (!p) return noEncontrado('Pedido enviado');
      return '<div class="scr"><div class="content" style="padding-top:calc(var(--sb) + 40px)"><div class="stack center">' +
        '<div class="ok-big">' + icon('check', 42) + '</div>' +
        '<h1 class="h-title">¡Pedido enviado!</h1>' +
        '<p class="h-sub">Tu pedido #' + p.id + ' quedó pendiente. Cuando la empresa lo confirme lo vas a ver en Mis pedidos.</p>' +
        '<div class="card" style="text-align:left"><div class="kv"><span>Fecha</span><b>' + esc(ctx.L.fechaLarga(p.fecha)) + '</b></div>' +
        '<div class="kv"><span>Servicios</span><b>' + esc(UI.nombresServicios(ctx.S, p)) + '</b></div>' +
        '<div class="kv"><span>Total estimado</span><b>' + ctx.L.money(ctx.S.total(p)) + '</b></div></div>' +
        '<button class="btn primary" data-go="cli/pedido/' + p.id + '" data-replace>Ver el pedido</button>' +
        '<button class="btn ghost" data-go="cli/inicio" data-clear>Volver al inicio</button>' +
        '</div></div></div>';
    },
  };

  // ---------- mis pedidos ----------
  const TERMINADOS = ['Finalizado', 'Rechazado'];

  Screens.cliPedidos = {
    tone: 'light',
    render(ctx) {
      const S = ctx.S, u = ctx.user;
      const todos = S.pedidosDeCliente(u.dni);
      const f = ctx.ui.f.cliPed || 'activos';
      const activos = todos.filter(S.activo);
      const terminados = todos.filter((p) => TERMINADOS.includes(p.estado));
      const lista = f === 'activos' ? activos : f === 'terminados' ? terminados : todos;
      return '<div class="scr">' + UI.hero({ title: 'Mis pedidos', sub: UI.plural(todos.length, 'pedido', 'pedidos') + ' en total', right: avatarBtn(ctx) }) +
        '<div class="content"><div class="stack">' +
        UI.chips([['activos', 'En curso', activos.length], ['terminados', 'Terminados', terminados.length], ['todos', 'Todos', todos.length]], f, 'cliPed') +
        (lista.length
          ? lista.map((p) => UI.pedidoCard(ctx, p, { go: 'cli/pedido/' + p.id })).join('')
          : UI.empty('clipboard', f === 'activos' ? 'No tenés pedidos en curso' : 'Todavía no hay pedidos acá',
            'Tocá el botón + para pedir una mudanza.')) +
        '</div></div>' +
        '<button class="fab" data-act="nuevo-pedido" aria-label="Pedir una mudanza">' + icon('plus', 26) + '</button>' +
        UI.tabbar(u.rol, 'cli/pedidos') + '</div>';
    },
    acts: {
      'nuevo-pedido'(ctx) { ctx.ui.draft = nuevoDraft(ctx); ctx.go('cli/pedir'); },
    },
  };

  Screens.cliPedido = {
    render(ctx) {
      const p = ctx.S.pedido(ctx.params.id);
      if (!p || p.clienteDni !== ctx.user.dni) return noEncontrado('Pedido');
      return '<div class="scr">' + UI.appbar({ title: 'Pedido #' + p.id, sub: esc(UI.nombresServicios(ctx.S, p)), right: UI.badgePedido(p.estado) }) +
        '<div class="content"><div class="stack">' + UI.pedidoDetalle(ctx, p) + '</div></div></div>';
    },
  };
})(window);
