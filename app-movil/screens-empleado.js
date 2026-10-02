/* Pantallas del empleado (chofer o ayudante de carga). */
(function (root) {
  'use strict';
  const Screens = root.Screens = root.Screens || {};
  const UI = root.UI;
  const { icon, esc } = UI;

  const telefono = (t) => String(t).replace(/^(\d{3})(\d{3})(\d{4})$/, '$1 $2-$3');

  function grupos(ctx) {
    const S = ctx.S, hoy = ctx.hoy;
    const todas = S.pedidosDeEmpleado(ctx.user.dni).filter((p) => p.estado !== 'Rechazado');
    return {
      hoy: todas.filter((p) => (S.activo(p) && p.fecha <= hoy) || (p.fecha === hoy && p.estado === 'Finalizado')),
      proximas: todas.filter((p) => S.activo(p) && p.fecha > hoy),
      hechas: todas.filter((p) => p.estado === 'Finalizado').reverse(),
    };
  }

  function tarjeta(ctx, p) {
    const S = ctx.S;
    const c = S.usuario(p.clienteDni);
    const fragiles = p.inventario.filter((i) => i.fragil).length;
    return '<button class="pcard" data-go="emp/mudanza/' + p.id + '">' +
      '<div class="row"><span class="pnum">Mudanza #' + p.id + '</span>' + UI.badgePedido(p.estado) + '</div>' +
      '<div class="meta">' + icon('calendar', 15) + '<span>' + esc(ctx.L.diaRelativo(p.fecha, ctx.hoy)) + ' · ' + esc(UI.nombresServicios(S, p)) + '</span></div>' +
      '<div class="meta">' + icon('user', 15) + '<span>' + esc(UI.nombreDe(c)) + '</span></div>' +
      '<div class="meta">' + icon('route', 15) + '<span>' + esc(UI.corto(p.origen)) + ' → ' + esc(UI.corto(p.destino)) + '</span></div>' +
      '<div class="pfoot"><span class="plate sm">' + esc(p.patente) + '</span><span class="muted">' +
      (fragiles ? icon('glass', 13) + ' ' + UI.plural(fragiles, 'objeto frágil', 'objetos frágiles') : UI.plural(p.inventario.length, 'objeto', 'objetos')) +
      '</span></div></button>';
  }

  Screens.empMudanzas = {
    tone: 'light',
    render(ctx) {
      const u = ctx.user;
      const g = grupos(ctx);
      const f = ctx.ui.f.emp || 'hoy';
      const activasHoy = g.hoy.filter(ctx.S.activo).length;
      const lista = g[f];
      const vacio = {
        hoy: ['Hoy no tenés mudanzas', 'Cuando el administrador te asigne una para hoy, aparece acá.'],
        proximas: ['No tenés mudanzas próximas', 'Las que te asignen para los próximos días aparecen acá.'],
        hechas: ['Todavía no terminaste ninguna', 'Las mudanzas finalizadas quedan guardadas acá.'],
      }[f];
      return '<div class="scr">' + UI.hero({ title: 'Hola, ' + u.nombre,
        sub: esc(u.rol) + ' · ' + (activasHoy ? UI.plural(activasHoy, 'mudanza hoy', 'mudanzas hoy') : 'sin mudanzas hoy'),
        right: '<button class="avatar" data-go="perfil" aria-label="Mi perfil">' + ctx.L.iniciales(u.nombre, u.apellido) + '</button>' }) +
        '<div class="content"><div class="stack">' +
        UI.chips([['hoy', 'Hoy', g.hoy.length], ['proximas', 'Próximas', g.proximas.length], ['hechas', 'Realizadas', g.hechas.length]], f, 'emp') +
        (lista.length ? lista.map((p) => tarjeta(ctx, p)).join('') : UI.empty('truck', vacio[0], vacio[1])) +
        '</div></div>' + UI.tabbar(u.rol, 'emp/mudanzas') + '</div>';
    },
  };

  Screens.empMudanza = {
    render(ctx) {
      const S = ctx.S, L = ctx.L, me = ctx.user;
      const p = S.pedido(ctx.params.id);
      if (!p || (p.choferDni !== me.dni && !p.ayudantes.includes(me.dni))) {
        return '<div class="scr">' + UI.appbar({ title: 'Mudanza' }) + '<div class="content">' +
          UI.empty('info', 'Esta mudanza no está asignada a vos', 'Volvé a Mis mudanzas.') + '</div></div>';
      }
      const c = S.usuario(p.clienteDni);
      const v = S.vehiculo(p.patente);
      let barra = '';
      if (p.estado === 'Asignado') barra = '<button class="btn primary" data-act="iniciar">' + icon('play', 18) + 'Iniciar mudanza</button>';
      if (p.estado === 'En curso') barra = '<button class="btn primary" data-act="finalizar">' + icon('flag', 18) + 'Finalizar mudanza</button>';
      return '<div class="scr">' + UI.appbar({ title: 'Mudanza #' + p.id, sub: esc(L.diaRelativo(p.fecha, ctx.hoy)) + ' · ' + esc(UI.nombresServicios(S, p)),
        right: UI.badgePedido(p.estado) }) +
        '<div class="content"><div class="stack">' +
        (p.estado === 'Finalizado' ? '<div class="banner ok">' + icon('check', 18) + '<span>Mudanza finalizada. ¡Buen trabajo!</span></div>' : '') +
        '<div class="card"><h4>Cliente</h4>' + UI.persona(c, 'Cliente') +
        '<div class="row" style="margin-top:6px"><span class="num" style="font-weight:600;user-select:all">' + esc(telefono(c.telefono)) + '</span>' +
        '<a class="btn sm ghost" href="tel:' + esc(c.telefono) + '">' + icon('phone', 16) + 'Llamar</a></div></div>' +
        '<div class="card"><h4>Recorrido</h4>' + UI.ruta(p) + '</div>' +
        UI.inventario(p) +
        '<div class="card"><h4>Vehículo y equipo</h4>' +
        (v ? '<div class="row" style="padding-bottom:6px"><div><b>' + esc(v.tipo) + '</b><div class="vmodel">' + esc(v.marcaModelo) + '</div></div>' +
          '<span class="plate sm">' + esc(v.patente) + '</span></div>' : '') +
        UI.persona(S.usuario(p.choferDni), p.choferDni === me.dni ? 'Chofer · vos' : 'Chofer') +
        p.ayudantes.map((d) => UI.persona(S.usuario(d), d === me.dni ? 'Ayudante · vos' : 'Ayudante de carga')).join('') +
        (p.materiales.length ? '<div class="tags" style="margin-top:8px">' + p.materiales.map((m) => '<span class="tag">' + esc(m) + '</span>').join('') + '</div>' : '') +
        '</div></div></div>' +
        (barra ? '<div class="bottom-bar">' + barra + '</div>' : '') + '</div>';
    },
    acts: {
      iniciar(ctx) {
        ctx.overlay({ kind: 'confirm', icon: 'play', title: '¿Arrancan la mudanza?', confirm: 'Iniciar', act: 'iniciar-ok',
          text: 'El cliente la va a ver <b>en camino</b> y el vehículo pasa a estar en viaje.' });
      },
      'iniciar-ok'(ctx) {
        const r = ctx.S.iniciarMudanza(ctx.params.id);
        ctx.closeOverlay();
        if (r.ok) ctx.toast('Mudanza en curso. ¡Buen viaje!'); else ctx.toast(r.error, 'error');
      },
      finalizar(ctx) {
        ctx.overlay({ kind: 'confirm', icon: 'flag', title: '¿Terminaron la mudanza?', confirm: 'Finalizar', act: 'finalizar-ok',
          text: 'Confirmá solo cuando todo esté descargado en destino.' });
      },
      'finalizar-ok'(ctx) {
        const r = ctx.S.finalizarMudanza(ctx.params.id);
        ctx.closeOverlay();
        if (r.ok) ctx.toast('Mudanza finalizada. El cliente ya lo ve.'); else ctx.toast(r.error, 'error');
      },
    },
  };
})(window);
