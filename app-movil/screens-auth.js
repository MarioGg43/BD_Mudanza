/* Pantallas sin sesión (inicio, login, registro, recuperar y cambiar clave) y el perfil. */
(function (root) {
  'use strict';
  const Screens = root.Screens = root.Screens || {};
  const UI = root.UI;
  const { icon, esc } = UI;

  // Accesos rápidos de la demo: un usuario de cada rol.
  const DEMO = [
    [35123456, 'Administrador', 'Carlos Sarmiento'],
    [40987654, 'Chofer', 'Luciana Fernández'],
    [38999888, 'Ayudante', 'Lucas Romero'],
    [29876543, 'Cliente', 'María Gómez'],
  ];
  root.DEMO_USERS = DEMO;

  const MISION = 'Trasladamos tu casa o tu oficina, en Salta y a todo el país, con la seguridad de que cada cosa llega como salió.';

  function enmascarar(correo) {
    const [u, d] = String(correo).split('@');
    return u.slice(0, 2) + '•••@' + d;
  }

  Screens.splash = {
    tone: 'light',
    render() {
      return '<div class="splash">' +
        '<div class="mid"><img class="logo" src="img/logo-blanco.png" alt="Logo de Mudanzas Salta">' +
        '<h1 class="sr">Mudanzas y Fletes Salta</h1><p class="mision">' + MISION + '</p></div>' +
        '<div class="foot"><button class="btn white" data-go="login">Comenzar</button>' +
        '<span><b style="color:#fff">Mudanzas y Fletes Salta</b> · Salta, Argentina</span></div></div>';
    },
  };

  Screens.login = {
    render(ctx) {
      return '<div class="scr"><div class="content" style="padding-top:calc(var(--sb) + 26px)"><div class="stack">' +
        '<img class="auth-logo" src="img/logo-color.png" alt="Logo de Mudanzas Salta">' +
        '<div class="center"><h1 class="h-title">Iniciar sesión</h1><p class="h-sub">Entrá con tu correo, tu usuario o tu DNI.</p></div>' +
        '<form class="stack" data-form="login" novalidate>' + UI.formError(ctx) +
        UI.field(ctx, { id: 'ident', label: 'Correo electrónico o usuario', icon: 'mail', auto: 'username', placeholder: 'nombre@correo.com' }) +
        UI.field(ctx, { id: 'clave', label: 'Contraseña', type: 'password', icon: 'lock', auto: 'current-password', placeholder: 'Tu contraseña', value: '' }) +
        '<div style="text-align:right;margin-top:-6px"><button type="button" class="link small" data-go="recuperar">¿Olvidaste tu contraseña?</button></div>' +
        '<button class="btn primary" type="submit">Iniciar sesión</button></form>' +
        '<p class="center muted" style="margin:0">¿No tenés cuenta? <button class="link" data-go="registro">Registrate</button></p>' +
        '<div class="divider">Entrar rápido (demo)</div>' +
        '<div class="quick">' + DEMO.map(([dni, rol, nombre]) =>
          '<button data-act="entrar-como" data-dni="' + dni + '"><b>' + rol + '</b>' + esc(nombre) + '</button>').join('') + '</div>' +
        '<p class="center small" style="margin:0"><button class="link" data-act="galeria">Ver todas las pantallas</button></p>' +
        '</div></div></div>';
    },
    forms: {
      login(ctx, v) {
        const r = ctx.S.login(v.ident, v.clave);
        if (!r.ok) {
          ctx.ui.form = { name: 'login', values: { ident: v.ident }, error: r.error };
          ctx.refresh();
          return;
        }
        ctx.entrar(r);
      },
    },
  };

  Screens.registro = {
    render(ctx) {
      return '<div class="scr">' + UI.appbar({ title: 'Crear cuenta', sub: 'Registrate para pedir tu mudanza' }) +
        '<div class="content"><form class="stack" data-form="registro" novalidate>' + UI.formError(ctx) +
        '<div class="row-2">' + UI.field(ctx, { id: 'nombre', label: 'Nombre', auto: 'given-name', placeholder: 'María' }) +
        UI.field(ctx, { id: 'apellido', label: 'Apellido', auto: 'family-name', placeholder: 'Gómez' }) + '</div>' +
        '<div class="row-2">' + UI.field(ctx, { id: 'dni', label: 'DNI', mode: 'numeric', placeholder: 'Sin puntos' }) +
        UI.field(ctx, { id: 'telefono', label: 'Teléfono', type: 'tel', auto: 'tel', placeholder: '387 4112233' }) + '</div>' +
        UI.field(ctx, { id: 'correo', label: 'Correo electrónico', type: 'email', icon: 'mail', auto: 'email', placeholder: 'nombre@correo.com' }) +
        UI.field(ctx, { id: 'clave', label: 'Contraseña', type: 'password', icon: 'lock', auto: 'new-password',
          hint: 'Mínimo 8 caracteres, con mayúscula, minúscula, número y símbolo.' }) +
        UI.field(ctx, { id: 'clave2', label: 'Repetir contraseña', type: 'password', icon: 'lock', auto: 'new-password' }) +
        '<button class="btn primary" type="submit">Registrarme</button>' +
        '<p class="center muted" style="margin:0">¿Ya tenés cuenta? <button type="button" class="link" data-go="login" data-replace>Iniciá sesión</button></p>' +
        '</form></div></div>';
    },
    forms: {
      registro(ctx, v) {
        const r = ctx.S.registrarCliente(v);
        ctx.result(r, 'registro', v, () => {
          ctx.go('cli/inicio', { clear: true });
          ctx.toast('Creamos tu cuenta. Tu usuario es ' + r.usuario.usuario + '.');
        });
      },
    },
  };

  Screens.recuperar = {
    render(ctx) {
      const hecho = ctx.ui.x.recuperado;
      if (hecho) {
        return '<div class="scr">' + UI.appbar({ title: 'Recuperar contraseña' }) +
          '<div class="content"><div class="stack center" style="padding-top:18px">' +
          '<div class="ok-big">' + icon('mail', 38) + '</div><h1 class="h-title">Revisá tu correo</h1>' +
          '<p class="h-sub">Te mandamos una contraseña temporal a <b>' + esc(enmascarar(hecho.correo)) +
          '</b>. Cuando entres te vamos a pedir que la cambies.</p>' +
          '<div class="banner info" style="text-align:left">' + icon('info', 18) +
          '<span>En la demo no se mandan correos. Tu contraseña temporal es:</span></div>' +
          '<div class="secret"><span>' + esc(hecho.temporal) + '</span>' + icon('key', 20) + '</div>' +
          '<button class="btn primary" data-go="login" data-replace>Ir a iniciar sesión</button></div></div></div>';
      }
      return '<div class="scr">' + UI.appbar({ title: 'Recuperar contraseña' }) +
        '<div class="content"><form class="stack" data-form="recuperar" novalidate>' +
        '<div class="empty" style="padding:8px 0 0"><div class="ic">' + icon('key', 26) + '</div>' +
        '<p>Escribí el correo de tu cuenta y te mandamos una contraseña temporal.</p></div>' +
        UI.field(ctx, { id: 'correo', label: 'Correo electrónico', type: 'email', icon: 'mail', auto: 'email', placeholder: 'nombre@correo.com' }) +
        '<button class="btn primary" type="submit">Enviar contraseña temporal</button>' +
        '<p class="center muted" style="margin:0"><button type="button" class="link" data-back>Volver a iniciar sesión</button></p>' +
        '</form></div></div>';
    },
    forms: {
      recuperar(ctx, v) {
        const r = ctx.S.recuperarClave(v.correo);
        if (!r.ok) {
          ctx.ui.form = { name: 'recuperar', values: v, errores: { correo: r.error } };
          ctx.refresh();
          return;
        }
        ctx.ui.form = null;
        ctx.ui.x.recuperado = { correo: r.usuario.correo, temporal: r.temporal };
        ctx.refresh();
      },
    },
  };

  Screens.cambiarClave = {
    render(ctx) {
      const S = ctx.S;
      const forzado = !!S.session.pendiente;
      const u = S.usuarioPendiente() || ctx.user;
      const top = forzado
        ? '<div class="empty" style="padding:4px 0 0"><div class="ic">' + icon('shield', 26) + '</div><b>Hola, ' + esc(u ? u.nombre : '') +
          '</b><p>Estás usando una contraseña temporal. Elegí una nueva para seguir.</p></div>'
        : '';
      return '<div class="scr">' + UI.appbar({ title: 'Cambiar contraseña', back: !forzado, sub: forzado ? 'Obligatorio en el primer ingreso' : '' }) +
        '<div class="content"><form class="stack" data-form="clave" novalidate>' + top + UI.formError(ctx) +
        UI.field(ctx, { id: 'actual', label: forzado ? 'Contraseña temporal' : 'Contraseña actual', type: 'password', icon: 'lock', auto: 'current-password' }) +
        UI.field(ctx, { id: 'nueva', label: 'Contraseña nueva', type: 'password', icon: 'lock', auto: 'new-password',
          hint: 'Mínimo 8 caracteres, con mayúscula, minúscula, número y símbolo.' }) +
        UI.field(ctx, { id: 'nueva2', label: 'Repetir contraseña nueva', type: 'password', icon: 'lock', auto: 'new-password' }) +
        '<button class="btn primary" type="submit">' + (forzado ? 'Guardar y entrar' : 'Guardar contraseña') + '</button>' +
        (forzado ? '<p class="center muted" style="margin:0"><button type="button" class="link" data-act="logout">Salir</button></p>' : '') +
        '</form></div></div>';
    },
    forms: {
      clave(ctx, v) {
        const forzado = !!ctx.S.session.pendiente;
        const r = ctx.S.cambiarClave(v.actual, v.nueva, v.nueva2);
        ctx.result(r, 'clave', v, () => {
          if (forzado) ctx.entrar(r, 'Listo, ' + r.usuario.nombre + '. Ya podés usar tu contraseña nueva.');
          else { ctx.back(); ctx.toast('Cambiamos tu contraseña.'); }
        });
      },
    },
  };

  Screens.perfil = {
    tone: 'light',
    render(ctx) {
      const u = ctx.user, L = ctx.L;
      return '<div class="scr"><header class="hero" style="text-align:center;padding-bottom:24px">' + UI.speed +
        '<div style="position:relative;z-index:1"><div class="avatar lg">' + L.iniciales(u.nombre, u.apellido) + '</div>' +
        '<h1 style="font-size:20px">' + esc(UI.nombreDe(u)) + '</h1><p>' + esc(u.rol) + ' · ' + esc(u.usuario) + '</p></div></header>' +
        '<div class="content"><div class="stack">' +
        '<form class="stack" data-form="perfil" novalidate><div class="section-title"><h3>Mis datos</h3></div>' + UI.formError(ctx) +
        '<div class="row-2">' + UI.field(ctx, { id: 'nombre', label: 'Nombre', def: u.nombre, auto: 'given-name' }) +
        UI.field(ctx, { id: 'apellido', label: 'Apellido', def: u.apellido, auto: 'family-name' }) + '</div>' +
        UI.field(ctx, { id: 'correo', label: 'Correo electrónico', type: 'email', icon: 'mail', def: u.correo, auto: 'email' }) +
        UI.field(ctx, { id: 'telefono', label: 'Teléfono', type: 'tel', icon: 'phone', def: u.telefono, auto: 'tel' }) +
        '<button class="btn primary" type="submit">Guardar cambios</button></form>' +
        '<div class="card pad-0"><div class="actions-list">' +
        '<button class="action-row" data-go="cambiar-clave"><span class="ic">' + icon('key', 18) + '</span><span>Cambiar contraseña</span>' + icon('chev', 18) + '</button>' +
        '<button class="action-row danger" data-act="logout"><span class="ic">' + icon('logout', 18) + '</span><span>Cerrar sesión</span></button>' +
        '</div></div>' +
        '<p class="center small muted" style="margin:0">DNI ' + u.dni.toLocaleString('es-AR') + ' · Último acceso: ' +
        esc(u.ultimoAcceso ? L.diaRelativo(u.ultimoAcceso, ctx.hoy).toLowerCase() : 'nunca') + '</p>' +
        '<p class="center small" style="margin:0"><button class="link" data-act="reiniciar">Reiniciar la demo</button></p>' +
        '</div></div>' + UI.tabbar(u.rol, 'perfil') + '</div>';
    },
    forms: {
      perfil(ctx, v) {
        const r = ctx.S.modificarPerfil(v);
        ctx.result(r, 'perfil', v, () => { ctx.refresh(); ctx.toast('Guardamos tus datos.'); });
      },
    },
    acts: {
      reiniciar(ctx) {
        ctx.overlay({ kind: 'confirm', title: '¿Reiniciar la demo?', danger: true, icon: 'refresh', confirm: 'Reiniciar', act: 'reiniciar-ok',
          text: 'Se borran los cambios que hiciste y vuelven los datos de ejemplo. Vas a tener que iniciar sesión de nuevo.' });
      },
    },
  };
})(window);
