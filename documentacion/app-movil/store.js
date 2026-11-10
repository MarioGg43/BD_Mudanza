/* Estado de la demo y una acción por cada proceso del sistema. Cada acción devuelve
   {ok:true, ...} o {ok:false, error} / {ok:false, errores:{campo: mensaje}}.
   Todo se guarda en el navegador de quien usa la demo; si el navegador no deja
   guardar, la app sigue funcionando igual hasta que se recarga. */
(function (root) {
  'use strict';
  const L = root.Logic || require('./logic.js');
  const buildSeed = root.buildSeed || require('./data.js');
  const KEY = 'mudanzas-salta-app-v1';
  const ACTIVOS = ['Pendiente', 'Confirmado', 'Asignado', 'En curso'];

  function createStore(storage, hoyFn) {
    const hoy = hoyFn || L.hoyIso;
    const S = { state: null, session: { dni: null, pendiente: null } };

    function persist() {
      try { if (storage) storage.setItem(KEY, JSON.stringify({ state: S.state, session: S.session })); } catch (e) { /* sin almacenamiento */ }
    }
    function fail(error) { return { ok: false, error }; }
    function failCampos(errores) { return { ok: false, errores }; }
    const vacio = (v) => !String(v == null ? '' : v).trim();
    const limpio = (v) => String(v == null ? '' : v).trim();
    const digitos = (v) => String(v == null ? '' : v).replace(/\D/g, '');

    S.load = function () {
      let data = null;
      try {
        const raw = storage ? storage.getItem(KEY) : null;
        if (raw) data = JSON.parse(raw);
      } catch (e) { data = null; }
      if (data && data.state && data.state.version === 1) {
        S.state = data.state;
        S.session = data.session || { dni: null, pendiente: null };
      } else {
        S.state = buildSeed(hoy());
        S.session = { dni: null, pendiente: null };
      }
    };

    S.reset = function () {
      S.state = buildSeed(hoy());
      S.session = { dni: null, pendiente: null };
      persist();
    };

    S.hoy = hoy;

    // ---------- consultas ----------
    S.usuario = (dni) => S.state.usuarios.find((u) => u.dni === Number(dni)) || null;
    S.usuarioActual = function () {
      const u = S.session.dni ? S.usuario(S.session.dni) : null;
      return u && u.activo ? u : null;
    };
    S.usuarioPendiente = () => (S.session.pendiente ? S.usuario(S.session.pendiente) : null);
    S.pedido = (id) => S.state.pedidos.find((p) => p.id === Number(id)) || null;
    S.vehiculo = (patente) => S.state.vehiculos.find((v) => v.patente === patente) || null;
    S.servicio = (id) => S.state.servicios.find((s) => s.id === Number(id)) || null;
    S.total = (p) => L.totalPedido(p, S.state.servicios);
    S.cobrado = (p) => L.cobradoPedido(p, S.state.cobranzas);
    S.saldo = (p) => L.saldoPedido(p, S.state.servicios, S.state.cobranzas);
    S.cobrosDe = (p) => S.state.cobranzas.filter((c) => c.pedidoId === p.id);
    S.activo = (p) => ACTIVOS.includes(p.estado);
    S.pedidosDeCliente = (dni) => S.state.pedidos.filter((p) => p.clienteDni === Number(dni)).sort((a, b) => b.id - a.id);
    S.pedidosDeEmpleado = (dni) => S.state.pedidos
      .filter((p) => p.choferDni === Number(dni) || p.ayudantes.includes(Number(dni)))
      .sort((a, b) => (a.fecha < b.fecha ? -1 : a.fecha > b.fecha ? 1 : a.id - b.id));

    S.vehiculosLibres = function (fecha, excluirId) {
      return S.state.vehiculos.filter((v) => v.estado !== 'En Mantenimiento' && v.estado !== 'Fuera de Servicio' &&
        !S.state.pedidos.some((p) => p.id !== excluirId && S.activo(p) && p.fecha === fecha && p.patente === v.patente));
    };

    S.empleadosLibres = function (rol, fecha, excluirId) {
      return S.state.usuarios.filter((u) => u.rol === rol && u.activo &&
        !S.state.pedidos.some((p) => p.id !== excluirId && S.activo(p) && p.fecha === fecha &&
          (p.choferDni === u.dni || p.ayudantes.includes(u.dni))));
    };

    function requiereRol(rol) {
      const u = S.usuarioActual();
      if (!u || u.rol !== rol) return rol === 'Administrador'
        ? 'Esta acción es solo para el administrador.' : 'Esta acción es solo para clientes.';
      return null;
    }

    // ---------- sesión ----------
    function entrar(u) {
      u.ultimoAcceso = hoy();
      S.session = { dni: u.dni, pendiente: null };
      persist();
    }

    function buscarPorIdentificador(ident) {
      const id = limpio(ident).toLowerCase();
      if (!id) return null;
      if (/^\d+$/.test(id)) {
        const porDni = S.usuario(Number(id));
        if (porDni) return porDni;
      }
      return S.state.usuarios.find((u) => u.usuario === id) ||
        S.state.usuarios.find((u) => u.correo.toLowerCase() === id) || null;
    }

    function accesoDe(u) {
      if (!u.activo) return fail('Tu usuario está dado de baja. Comunicate con la empresa.');
      if (u.debeCambiar) {
        S.session = { dni: null, pendiente: u.dni };
        persist();
        return { ok: true, cambiarClave: true, usuario: u };
      }
      entrar(u);
      return { ok: true, usuario: u };
    }

    S.login = function (ident, clave) {
      if (vacio(ident) || !clave) return fail('Completá tu usuario y tu contraseña.');
      const u = buscarPorIdentificador(ident);
      if (!u || u.clave !== clave) return fail('Usuario o contraseña incorrectos.');
      return accesoDe(u);
    };

    // Accesos rápidos de la demo: entran sin escribir la clave.
    S.entrarComo = function (dni) {
      const u = S.usuario(dni);
      return u ? accesoDe(u) : fail('No existe ese usuario.');
    };

    S.logout = function () {
      S.session = { dni: null, pendiente: null };
      persist();
    };

    S.cambiarClave = function (actual, nueva, nueva2) {
      const u = S.usuarioPendiente() || S.usuarioActual();
      if (!u) return fail('Volvé a iniciar sesión.');
      const errores = {};
      if (u.clave !== actual) errores.actual = 'La contraseña actual no coincide.';
      const e = L.validarClave(nueva);
      if (e) errores.nueva = e;
      else if (nueva === actual) errores.nueva = 'La contraseña nueva tiene que ser distinta de la actual.';
      if (nueva !== nueva2) errores.nueva2 = 'Las contraseñas no coinciden.';
      if (Object.keys(errores).length) return failCampos(errores);
      u.clave = nueva;
      u.debeCambiar = false;
      u.modificado = hoy();
      entrar(u);
      return { ok: true, usuario: u };
    };

    function validarPersona(f, excluirDni, conDni) {
      const errores = {};
      if (vacio(f.nombre)) errores.nombre = 'Escribí el nombre.';
      if (vacio(f.apellido)) errores.apellido = 'Escribí el apellido.';
      if (conDni) {
        const dni = digitos(f.dni);
        if (!/^\d{7,8}$/.test(dni)) errores.dni = 'Escribí el DNI sin puntos: 7 u 8 números.';
        else if (S.usuario(Number(dni))) errores.dni = 'Ya hay un usuario con ese DNI.';
      }
      const correo = limpio(f.correo).toLowerCase();
      if (!L.validarCorreo(correo)) errores.correo = 'Escribí un correo válido, por ejemplo nombre@correo.com.';
      else if (S.state.usuarios.some((u) => u.correo.toLowerCase() === correo && u.dni !== excluirDni)) {
        errores.correo = 'Ese correo ya lo usa otro usuario.';
      }
      if (digitos(f.telefono).length !== 10) errores.telefono = 'Escribí el teléfono con código de área: 10 números.';
      return errores;
    }

    function nuevaPersona(f, rol, clave, debeCambiar) {
      return {
        dni: Number(digitos(f.dni)), nombre: limpio(f.nombre), apellido: limpio(f.apellido),
        correo: limpio(f.correo).toLowerCase(), telefono: digitos(f.telefono),
        usuario: L.username(f.apellido, f.nombre, S.state.usuarios.map((u) => u.usuario)),
        clave, rol, activo: true, debeCambiar, alta: hoy(), modificado: hoy(), baja: null, ultimoAcceso: null,
      };
    }

    S.registrarCliente = function (f) {
      f = f || {};
      const errores = validarPersona(f, null, true);
      if (errores.dni === 'Ya hay un usuario con ese DNI.') errores.dni = 'Ya hay una cuenta con ese DNI.';
      if (errores.correo === 'Ese correo ya lo usa otro usuario.') errores.correo = 'Ya hay una cuenta con ese correo.';
      const e = L.validarClave(f.clave);
      if (e) errores.clave = e;
      if (f.clave !== f.clave2) errores.clave2 = 'Las contraseñas no coinciden.';
      if (Object.keys(errores).length) return failCampos(errores);
      const u = nuevaPersona(f, 'Cliente', f.clave, false);
      S.state.usuarios.push(u);
      entrar(u);
      return { ok: true, usuario: u };
    };

    S.recuperarClave = function (correo) {
      const c = limpio(correo).toLowerCase();
      if (!L.validarCorreo(c)) return fail('Escribí un correo válido, por ejemplo nombre@correo.com.');
      const u = S.state.usuarios.find((x) => x.correo.toLowerCase() === c);
      if (!u) return fail('No encontramos una cuenta con ese correo.');
      const temporal = L.claveTemporal();
      u.clave = temporal;
      u.debeCambiar = true;
      u.modificado = hoy();
      persist();
      return { ok: true, temporal, usuario: u };
    };

    S.modificarPerfil = function (f) {
      const u = S.usuarioActual();
      if (!u) return fail('Volvé a iniciar sesión.');
      const errores = validarPersona(f, u.dni, false);
      if (Object.keys(errores).length) return failCampos(errores);
      u.nombre = limpio(f.nombre);
      u.apellido = limpio(f.apellido);
      u.correo = limpio(f.correo).toLowerCase();
      u.telefono = digitos(f.telefono);
      u.modificado = hoy();
      persist();
      return { ok: true, usuario: u };
    };

    // ---------- pedidos ----------
    function transicion(p, accion) {
      const nuevo = L.siguienteEstado(p.estado, accion);
      if (!nuevo) return 'No se puede hacer eso con un pedido ' + p.estado.toLowerCase() + '.';
      const cambia = p.estado !== nuevo;
      p.estado = nuevo;
      if (cambia) p.historial.push({ estado: nuevo, fecha: hoy() });
      return null;
    }

    S.crearPedido = function (d) {
      const noCliente = requiereRol('Cliente');
      if (noCliente) return fail(noCliente);
      d = d || {};
      const errores = {};
      if (!d.fecha || d.fecha < hoy()) errores.fecha = 'Elegí una fecha de hoy en adelante.';
      if (vacio(d.origen)) errores.origen = 'Escribí la dirección de origen.';
      if (vacio(d.destino)) errores.destino = 'Escribí la dirección de destino.';
      if (!d.servicios || !d.servicios.length) errores.servicios = 'Elegí al menos un servicio.';
      if (!d.patente) errores.patente = 'Elegí un vehículo.';
      else if (d.fecha && !S.vehiculosLibres(d.fecha).some((v) => v.patente === d.patente)) {
        errores.patente = 'Ese vehículo ya no está libre para esa fecha. Elegí otro.';
      }
      if (!d.inventario || !d.inventario.length) errores.inventario = 'Agregá al menos un objeto.';
      if (Object.keys(errores).length) return failCampos(errores);
      const p = {
        id: S.state.seq.pedido++, clienteDni: S.usuarioActual().dni, fecha: d.fecha,
        origen: limpio(d.origen), destino: limpio(d.destino), servicios: d.servicios.map(Number),
        patente: d.patente, estado: 'Pendiente', motivo: null,
        inventario: d.inventario.map((i) => ({ desc: limpio(i.desc), cant: Number(i.cant), peso: Number(i.peso), fragil: !!i.fragil })),
        choferDni: null, ayudantes: [], materiales: [], historial: [{ estado: 'Pendiente', fecha: hoy() }],
      };
      S.state.pedidos.push(p);
      persist();
      return { ok: true, pedido: p };
    };

    function pedidoAdmin(id) {
      const e = requiereRol('Administrador');
      if (e) return { error: e };
      const p = S.pedido(id);
      return p ? { p } : { error: 'No existe el pedido ' + id + '.' };
    }

    S.confirmarPedido = function (id) {
      const { p, error } = pedidoAdmin(id);
      if (error) return fail(error);
      const e = transicion(p, 'confirmar');
      if (e) return fail(e);
      persist();
      return { ok: true, pedido: p };
    };

    S.rechazarPedido = function (id, motivo) {
      const { p, error } = pedidoAdmin(id);
      if (error) return fail(error);
      if (vacio(motivo)) return failCampos({ motivo: 'Contale al cliente por qué se rechaza.' });
      const e = transicion(p, 'rechazar');
      if (e) return fail(e);
      p.motivo = limpio(motivo);
      persist();
      return { ok: true, pedido: p };
    };

    S.asignarRecursos = function (id, a) {
      const { p, error } = pedidoAdmin(id);
      if (error) return fail(error);
      if (p.estado === 'Pendiente') return fail('Primero confirmá el pedido.');
      a = a || {};
      const errores = {};
      const chofer = Number(a.choferDni) || null;
      const ayudantes = (a.ayudantes || []).map(Number);
      if (!chofer) errores.chofer = 'Elegí un chofer.';
      else if (!S.empleadosLibres('Chofer', p.fecha, p.id).some((u) => u.dni === chofer)) {
        errores.chofer = 'Ese chofer ya tiene otra mudanza ese día.';
      }
      const libres = S.empleadosLibres('Ayudante de Carga', p.fecha, p.id).map((u) => u.dni);
      if (ayudantes.some((dni) => !libres.includes(dni))) errores.ayudantes = 'Uno de los ayudantes ya tiene otra mudanza ese día.';
      if (!a.patente) errores.patente = 'Elegí un vehículo.';
      else if (!S.vehiculosLibres(p.fecha, p.id).some((v) => v.patente === a.patente)) {
        errores.patente = 'Ese vehículo ya está ocupado ese día.';
      }
      if (Object.keys(errores).length) return failCampos(errores);
      const e = transicion(p, 'asignar');
      if (e) return fail(e);
      p.choferDni = chofer;
      p.ayudantes = ayudantes;
      p.patente = a.patente;
      p.materiales = (a.materiales || []).slice();
      persist();
      return { ok: true, pedido: p };
    };

    S.registrarCobro = function (id, monto, metodo) {
      const { p, error } = pedidoAdmin(id);
      if (error) return fail(error);
      if (p.estado === 'Pendiente' || p.estado === 'Rechazado') return fail('Solo se cobra un pedido confirmado.');
      const m = Number(String(monto).replace(/\./g, '').replace(',', '.'));
      if (!(m > 0)) return fail('Escribí un monto mayor a cero.');
      const saldo = S.saldo(p);
      if (m > saldo) return fail('El monto no puede superar el saldo de ' + L.money(saldo) + '.');
      if (!S.state.metodosPago.includes(metodo)) return fail('Elegí cómo pagó el cliente.');
      const c = { id: S.state.seq.cobranza++, pedidoId: p.id, monto: m, metodo, fecha: hoy() };
      S.state.cobranzas.push(c);
      persist();
      return { ok: true, cobranza: c };
    };

    function mudanzaPropia(id) {
      const u = S.usuarioActual();
      const p = S.pedido(id);
      if (!u || !p) return { error: 'No existe esa mudanza.' };
      if (p.choferDni !== u.dni && !p.ayudantes.includes(u.dni)) return { error: 'Esta mudanza no está asignada a vos.' };
      return { p };
    }

    S.iniciarMudanza = function (id) {
      const { p, error } = mudanzaPropia(id);
      if (error) return fail(error);
      const e = transicion(p, 'iniciar');
      if (e) return fail(e);
      const v = S.vehiculo(p.patente);
      if (v) v.estado = 'En Viaje';
      persist();
      return { ok: true, pedido: p };
    };

    S.finalizarMudanza = function (id) {
      const { p, error } = mudanzaPropia(id);
      if (error) return fail(error);
      const e = transicion(p, 'finalizar');
      if (e) return fail(e);
      const v = S.vehiculo(p.patente);
      if (v && v.estado === 'En Viaje') v.estado = 'Disponible';
      persist();
      return { ok: true, pedido: p };
    };

    // ---------- vehículos ----------
    S.guardarVehiculo = function (f, original) {
      const e0 = requiereRol('Administrador');
      if (e0) return fail(e0);
      f = f || {};
      const errores = {};
      const patente = original || L.normalizarPatente(f.patente);
      if (!patente) errores.patente = 'Usá el formato AB 123 CD o ABC 123.';
      else if (!original && S.vehiculo(patente)) errores.patente = 'Ya existe un vehículo con esa patente.';
      if (vacio(f.marcaModelo)) errores.marcaModelo = 'Escribí la marca y el modelo.';
      if (!S.state.tiposVehiculo.includes(f.tipo)) errores.tipo = 'Elegí el tipo de vehículo.';
      const kg = Number(f.kg), m3 = Number(f.m3), km = Number(f.km), anio = Number(f.anio);
      if (!(kg > 0)) errores.kg = 'Tiene que ser mayor a cero.';
      if (!(m3 > 0)) errores.m3 = 'Tiene que ser mayor a cero.';
      if (vacio(f.km) || !(km >= 0)) errores.km = 'Escribí los kilómetros (0 si es nuevo).';
      const maxAnio = Number(hoy().slice(0, 4)) + 1;
      if (!(anio >= 1990 && anio <= maxAnio)) errores.anio = 'Escribí un año entre 1990 y ' + maxAnio + '.';
      if (!S.state.estadosVehiculo.includes(f.estado)) errores.estado = 'Elegí el estado.';
      const chofer = f.chofer ? Number(f.chofer) : null;
      if (chofer && !S.state.usuarios.some((u) => u.dni === chofer && u.rol === 'Chofer' && u.activo)) {
        errores.chofer = 'Elegí un chofer activo.';
      }
      if (Object.keys(errores).length) return failCampos(errores);
      const datos = { patente, marcaModelo: limpio(f.marcaModelo), tipo: f.tipo, kg, m3, estado: f.estado,
        km: Math.round(km), anio, chofer, obs: limpio(f.obs) };
      const v = S.vehiculo(patente);
      if (v) Object.assign(v, datos);
      else S.state.vehiculos.push(datos);
      persist();
      return { ok: true, vehiculo: S.vehiculo(patente) };
    };

    S.bajaVehiculo = function (patente) {
      const e0 = requiereRol('Administrador');
      if (e0) return fail(e0);
      const v = S.vehiculo(patente);
      if (!v) return fail('No existe ese vehículo.');
      if (v.estado === 'Fuera de Servicio') return fail('El vehículo ya está fuera de servicio.');
      v.estado = 'Fuera de Servicio';
      persist();
      return { ok: true, vehiculo: v };
    };

    // ---------- usuarios ----------
    function usuarioAdmin(dni) {
      const e = requiereRol('Administrador');
      if (e) return { error: e };
      const u = S.usuario(dni);
      return u ? { u } : { error: 'No existe ese usuario.' };
    }

    S.altaUsuario = function (f) {
      const e0 = requiereRol('Administrador');
      if (e0) return fail(e0);
      f = f || {};
      const errores = validarPersona(f, null, true);
      if (!S.state.roles.includes(f.rol)) errores.rol = 'Elegí un rol.';
      if (Object.keys(errores).length) return failCampos(errores);
      const temporal = L.claveTemporal();
      const u = nuevaPersona(f, f.rol, temporal, true);
      S.state.usuarios.push(u);
      persist();
      return { ok: true, usuario: u, temporal };
    };

    S.modificarCorreo = function (dni, correo) {
      const { u, error } = usuarioAdmin(dni);
      if (error) return fail(error);
      const c = limpio(correo).toLowerCase();
      if (!L.validarCorreo(c)) return fail('Escribí un correo válido, por ejemplo nombre@correo.com.');
      if (c === u.correo) return fail('Ese ya es su correo.');
      if (S.state.usuarios.some((x) => x.correo.toLowerCase() === c && x.dni !== u.dni)) return fail('Ese correo ya lo usa otro usuario.');
      u.correo = c;
      u.modificado = hoy();
      persist();
      return { ok: true, usuario: u };
    };

    S.cambiarRol = function (dni, rol) {
      const { u, error } = usuarioAdmin(dni);
      if (error) return fail(error);
      if (!S.state.roles.includes(rol)) return fail('Elegí un rol.');
      const e = L.errorCambioRol(S.usuarioActual().dni, u, rol);
      if (e) return fail(e);
      const anterior = u.rol;
      u.rol = rol;
      u.modificado = hoy();
      persist();
      return { ok: true, usuario: u, anterior };
    };

    S.restablecerClave = function (dni) {
      const { u, error } = usuarioAdmin(dni);
      if (error) return fail(error);
      const temporal = L.claveTemporal();
      u.clave = temporal;
      u.debeCambiar = true;
      u.modificado = hoy();
      persist();
      return { ok: true, usuario: u, temporal };
    };

    S.bajaUsuario = function (dni) {
      const { u, error } = usuarioAdmin(dni);
      if (error) return fail(error);
      const e = L.errorBaja(S.usuarioActual().dni, u, S.state.usuarios);
      if (e) return fail(e);
      u.activo = false;
      u.baja = hoy();
      u.modificado = hoy();
      persist();
      return { ok: true, usuario: u };
    };

    S.reactivarUsuario = function (dni) {
      const { u, error } = usuarioAdmin(dni);
      if (error) return fail(error);
      if (u.activo) return fail('El usuario ya está activo.');
      u.activo = true;
      u.baja = null;
      u.modificado = hoy();
      persist();
      return { ok: true, usuario: u };
    };

    // ---------- servicios ----------
    S.guardarServicio = function (f) {
      const e0 = requiereRol('Administrador');
      if (e0) return fail(e0);
      f = f || {};
      const errores = {};
      const tipo = limpio(f.tipo);
      const precio = Number(String(f.precio).replace(/\./g, ''));
      const materiales = (Array.isArray(f.materiales) ? f.materiales : String(f.materiales || '').split(','))
        .map((m) => limpio(m)).filter(Boolean);
      const id = f.id ? Number(f.id) : null;
      if (!tipo) errores.tipo = 'Escribí el nombre del servicio.';
      else if (S.state.servicios.some((s) => s.tipo.toLowerCase() === tipo.toLowerCase() && s.id !== id)) {
        errores.tipo = 'Ya existe un servicio con ese nombre.';
      }
      if (!(precio > 0)) errores.precio = 'El precio tiene que ser mayor a cero.';
      if (!materiales.length) errores.materiales = 'Escribí al menos un material, separados por comas.';
      if (Object.keys(errores).length) return failCampos(errores);
      let s = id ? S.servicio(id) : null;
      if (s) Object.assign(s, { tipo, precio, materiales, detalle: limpio(f.detalle) });
      else {
        s = { id: S.state.seq.servicio++, tipo, precio, materiales, detalle: limpio(f.detalle) };
        S.state.servicios.push(s);
      }
      persist();
      return { ok: true, servicio: s };
    };

    return S;
  }

  if (typeof module !== 'undefined' && module.exports) module.exports = createStore;
  else root.createStore = createStore;
})(typeof window !== 'undefined' ? window : globalThis);
