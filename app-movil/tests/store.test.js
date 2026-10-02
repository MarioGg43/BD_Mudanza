const test = require('node:test');
const assert = require('node:assert/strict');
const createStore = require('../store.js');

const HOY = '2026-09-29';
function nuevo() {
  const mem = {};
  const storage = {
    getItem: (k) => (k in mem ? mem[k] : null),
    setItem: (k, v) => { mem[k] = String(v); },
    removeItem: (k) => { delete mem[k]; },
  };
  const s = createStore(storage, () => HOY);
  s.load();
  return { s, mem };
}

test('login de cada rol, con usuario, correo o DNI', () => {
  const { s } = nuevo();
  assert.equal(s.login('sarmientoc', 'Admin123!').ok, true);
  assert.equal(s.usuarioActual().rol, 'Administrador');
  s.logout();
  assert.equal(s.login('luciana.f@mudanzassalta.com.ar', 'Usuario123!').ok, true);
  assert.equal(s.usuarioActual().rol, 'Chofer');
  s.logout();
  assert.equal(s.login('29876543', 'Cliente123!').ok, true);
  assert.equal(s.usuarioActual().rol, 'Cliente');
  assert.equal(s.state.usuarios.find((u) => u.dni === 29876543).ultimoAcceso, HOY);
});

test('login rechaza clave mala y usuario dado de baja', () => {
  const { s } = nuevo();
  assert.equal(s.login('sarmientoc', 'mala').error, 'Usuario o contraseña incorrectos.');
  assert.match(s.login('castros', 'Ayudante123!').error, /dado de baja/);
  assert.equal(s.usuarioActual(), null);
});

test('romerol tiene que cambiar la clave antes de entrar', () => {
  const { s } = nuevo();
  const r = s.login('romerol', 'Temporal123!');
  assert.equal(r.ok, true);
  assert.equal(r.cambiarClave, true);
  assert.equal(s.usuarioActual(), null);
  assert.equal(s.cambiarClave('Temporal123!', 'otra', 'otra').errores.nueva !== undefined, true);
  assert.equal(s.cambiarClave('Mala123!', 'Nueva123!', 'Nueva123!').errores.actual, 'La contraseña actual no coincide.');
  assert.equal(s.cambiarClave('Temporal123!', 'Temporal123!', 'Temporal123!').errores.nueva,
    'La contraseña nueva tiene que ser distinta de la actual.');
  assert.equal(s.cambiarClave('Temporal123!', 'Nueva123!', 'Nueva124!').errores.nueva2, 'Las contraseñas no coinciden.');
  assert.equal(s.cambiarClave('Temporal123!', 'Nueva123!', 'Nueva123!').ok, true);
  assert.equal(s.usuarioActual().usuario, 'romerol');
  assert.equal(s.usuarioActual().debeCambiar, false);
});

test('registro de cliente con validaciones y usuario automático', () => {
  const { s } = nuevo();
  const vacio = s.registrarCliente({});
  assert.equal(vacio.ok, false);
  assert.ok(vacio.errores.nombre && vacio.errores.correo && vacio.errores.clave);
  const dup = s.registrarCliente({ nombre: 'Marta', apellido: 'Gómez', dni: '30111222', correo: 'maria.gomez@ejemplo.com',
    telefono: '3874000000', clave: 'Clave123!', clave2: 'Clave123!' });
  assert.equal(dup.errores.correo, 'Ya hay una cuenta con ese correo.');
  const r = s.registrarCliente({ nombre: 'Marta', apellido: 'Gómez', dni: '30111222', correo: 'marta@ejemplo.com',
    telefono: '3874000000', clave: 'Clave123!', clave2: 'Clave123!' });
  assert.equal(r.ok, true);
  assert.equal(r.usuario.usuario, 'gomezm1');
  assert.equal(s.usuarioActual().rol, 'Cliente');
});

test('recuperar clave deja una temporal y obliga a cambiarla', () => {
  const { s } = nuevo();
  assert.equal(s.recuperarClave('nadie@ejemplo.com').error, 'No encontramos una cuenta con ese correo.');
  const r = s.recuperarClave('maria.gomez@ejemplo.com');
  assert.equal(r.ok, true);
  const login = s.login('gomezm', r.temporal);
  assert.equal(login.cambiarClave, true);
});

test('pedido de punta a punta: cliente, administrador, chofer y cobro', () => {
  const { s } = nuevo();
  s.login('gomezm', 'Cliente123!');
  const malo = s.crearPedido({ fecha: '2026-09-01', origen: '', destino: '', servicios: [], patente: null, inventario: [] });
  assert.equal(malo.ok, false);
  assert.equal(malo.errores.fecha, 'Elegí una fecha de hoy en adelante.');
  const libres = s.vehiculosLibres('2026-10-06');
  assert.ok(libres.some((v) => v.patente === 'AG-234-NP'));
  assert.ok(!libres.some((v) => v.patente === 'AC-789-GH'), 'el que está en mantenimiento no se ofrece');
  const r = s.crearPedido({ fecha: '2026-10-06', origen: 'Zuviría 50, Salta', destino: 'Güemes 900, Salta',
    servicios: [1, 4], patente: 'AG-234-NP',
    inventario: [{ desc: 'Cama', cant: 1, peso: 40, fragil: false }] });
  assert.equal(r.ok, true);
  const id = r.pedido.id;
  assert.equal(id, 1026);
  assert.equal(s.pedido(id).estado, 'Pendiente');
  assert.equal(s.total(s.pedido(id)), 230000);
  s.logout();

  s.login('sarmientoc', 'Admin123!');
  assert.equal(s.confirmarPedido(id).ok, true);
  const choferes = s.empleadosLibres('Chofer', '2026-10-06', id);
  assert.ok(choferes.some((u) => u.dni === 40987654));
  assert.equal(s.asignarRecursos(id, { choferDni: null, ayudantes: [], patente: 'AG-234-NP', materiales: [] }).errores.chofer,
    'Elegí un chofer.');
  assert.equal(s.asignarRecursos(id, { choferDni: 40987654, ayudantes: [41222333], patente: 'AG-234-NP',
    materiales: ['Mantas', 'Cajas'] }).ok, true);
  assert.equal(s.pedido(id).estado, 'Asignado');
  assert.equal(s.registrarCobro(id, 300000, 'Efectivo').error, 'El monto no puede superar el saldo de $ 230.000.');
  assert.equal(s.registrarCobro(id, 100000, 'Efectivo').ok, true);
  assert.equal(s.saldo(s.pedido(id)), 130000);
  s.logout();

  s.login('fernandezl', 'Usuario123!');
  assert.ok(s.pedidosDeEmpleado(40987654).some((p) => p.id === id));
  assert.equal(s.iniciarMudanza(id).ok, true);
  assert.equal(s.vehiculo('AG-234-NP').estado, 'En Viaje');
  assert.equal(s.finalizarMudanza(id).ok, true);
  assert.equal(s.pedido(id).estado, 'Finalizado');
  assert.equal(s.vehiculo('AG-234-NP').estado, 'Disponible');
  assert.deepEqual(s.pedido(id).historial.map((h) => h.estado),
    ['Pendiente', 'Confirmado', 'Asignado', 'En curso', 'Finalizado']);
});

test('un empleado no puede iniciar una mudanza que no es suya', () => {
  const { s } = nuevo();
  s.login('alvarezd', 'Chofer123!');
  assert.equal(s.iniciarMudanza(1023).error, 'Esta mudanza no está asignada a vos.');
});

test('vehículos: alta, patente repetida, edición y baja', () => {
  const { s } = nuevo();
  s.login('sarmientoc', 'Admin123!');
  const base = { patente: 'ah 555 zz', marcaModelo: 'Fiat Ducato', tipo: 'Furgón Urbano', kg: '1500', m3: '11',
    estado: 'Disponible', km: '100', anio: '2025', chofer: '', obs: '' };
  const r = s.guardarVehiculo(base, null);
  assert.equal(r.ok, true);
  assert.equal(s.vehiculo('AH-555-ZZ').kg, 1500);
  assert.equal(s.guardarVehiculo(base, null).errores.patente, 'Ya existe un vehículo con esa patente.');
  assert.equal(s.guardarVehiculo({ ...base, patente: 'XX1', kg: '0' }, null).errores.patente,
    'Usá el formato AB 123 CD o ABC 123.');
  assert.equal(s.guardarVehiculo({ ...base, kg: '2000' }, 'AH-555-ZZ').ok, true);
  assert.equal(s.vehiculo('AH-555-ZZ').kg, 2000);
  assert.equal(s.bajaVehiculo('AH-555-ZZ').ok, true);
  assert.equal(s.vehiculo('AH-555-ZZ').estado, 'Fuera de Servicio');
});

test('usuarios: alta, correo, rol, clave, baja y reactivación con candados', () => {
  const { s } = nuevo();
  s.login('sarmientoc', 'Admin123!');
  const r = s.altaUsuario({ dni: '42123123', nombre: 'Pablo', apellido: 'Romero', correo: 'pablo.romero@mudanzassalta.com.ar',
    telefono: '3875000000', rol: 'Chofer' });
  assert.equal(r.ok, true);
  assert.equal(r.usuario.usuario, 'romerop');
  assert.equal(r.usuario.debeCambiar, true);
  assert.equal(s.altaUsuario({ dni: '42123123', nombre: 'X', apellido: 'Y', correo: 'x@ejemplo.com', telefono: '1', rol: 'Chofer' })
    .errores.dni, 'Ya hay un usuario con ese DNI.');
  assert.equal(s.modificarCorreo(42123123, 'luciana.f@mudanzassalta.com.ar').error, 'Ese correo ya lo usa otro usuario.');
  assert.equal(s.modificarCorreo(42123123, 'pablo.r@mudanzassalta.com.ar').ok, true);
  assert.equal(s.cambiarRol(35123456, 'Chofer').error, 'No podés cambiar tu propio rol.');
  assert.equal(s.cambiarRol(42123123, 'Ayudante de Carga').ok, true);
  const t = s.restablecerClave(42123123);
  assert.equal(t.ok, true);
  assert.equal(s.usuario(42123123).clave, t.temporal);
  assert.equal(s.bajaUsuario(35123456).error, 'No podés darte de baja a vos mismo.');
  assert.equal(s.bajaUsuario(42123123).ok, true);
  assert.equal(s.usuario(42123123).activo, false);
  assert.equal(s.usuario(42123123).baja, HOY);
  assert.equal(s.reactivarUsuario(42123123).ok, true);
  assert.equal(s.usuario(42123123).baja, null);
});

test('servicios: alta y cambio de precio', () => {
  const { s } = nuevo();
  s.login('sarmientoc', 'Admin123!');
  assert.equal(s.guardarServicio({ tipo: '', precio: '0', materiales: '' }).ok, false);
  const r = s.guardarServicio({ tipo: 'Guardamuebles', precio: '90000', materiales: 'Mantas, Film', detalle: 'Por mes' });
  assert.equal(r.ok, true);
  assert.deepEqual(s.servicio(r.servicio.id).materiales, ['Mantas', 'Film']);
  assert.equal(s.guardarServicio({ id: 1, tipo: 'Mudanza local', precio: '190000', materiales: 'Mantas', detalle: '' }).ok, true);
  assert.equal(s.servicio(1).precio, 190000);
});

test('los cambios se guardan y reiniciar vuelve a los datos de ejemplo', () => {
  const { s, mem } = nuevo();
  s.login('sarmientoc', 'Admin123!');
  s.bajaVehiculo('AD-321-JK');
  const otro = require('../store.js')({ getItem: (k) => mem[k] ?? null, setItem() {}, removeItem() {} }, () => HOY);
  otro.load();
  assert.equal(otro.vehiculo('AD-321-JK').estado, 'Fuera de Servicio');
  assert.equal(otro.usuarioActual().usuario, 'sarmientoc');
  s.reset();
  assert.equal(s.vehiculo('AD-321-JK').estado, 'Disponible');
  assert.equal(s.usuarioActual(), null);
});

test('funciona aunque el almacenamiento del navegador falle', () => {
  const roto = { getItem() { throw new Error('bloqueado'); }, setItem() { throw new Error('bloqueado'); }, removeItem() {} };
  const s = createStore(roto, () => HOY);
  s.load();
  assert.equal(s.login('sarmientoc', 'Admin123!').ok, true);
});
