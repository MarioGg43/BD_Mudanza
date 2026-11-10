const test = require('node:test');
const assert = require('node:assert/strict');
const L = require('../logic.js');

test('usuario automático: apellido + inicial, sin tildes ni espacios', () => {
  assert.equal(L.username('Fernández', 'Luciana', []), 'fernandezl');
  assert.equal(L.username('De la Cruz', 'Ana María', []), 'dea');
  assert.equal(L.username('Núñez', 'Óscar', []), 'nunezo');
});

test('usuario automático: si existe agrega 1, 2, 3 como el sistema', () => {
  assert.equal(L.username('Romero', 'Lucas', ['romerol']), 'romerol1');
  assert.equal(L.username('Romero', 'Lucía', ['romerol', 'romerol1']), 'romerol2');
  assert.equal(L.username('Romero', 'Lucía', ['ROMEROL']), 'romerol1');
});

test('clave fuerte con los mismos mensajes que el sistema', () => {
  assert.equal(L.validarClave('Abc1!'), 'La contraseña debe tener al menos 8 caracteres.');
  assert.match(L.validarClave('abcdefg1!'), /MAYÚSCULA/);
  assert.match(L.validarClave('ABCDEFG1!'), /MINÚSCULA/);
  assert.match(L.validarClave('Abcdefgh!'), /NÚMERO/);
  assert.match(L.validarClave('Abcdefg12'), /ESPECIAL/);
  assert.equal(L.validarClave('Admin123!'), null);
});

test('la clave temporal siempre cumple la regla de clave fuerte', () => {
  for (let i = 0; i < 200; i++) {
    const c = L.claveTemporal();
    assert.equal(c.length, 10);
    assert.equal(L.validarClave(c), null, c);
  }
});

test('correo', () => {
  assert.equal(L.validarCorreo('maria.gomez@ejemplo.com'), true);
  assert.equal(L.validarCorreo('maria.gomez@ejemplo'), false);
  assert.equal(L.validarCorreo('maria gomez@ejemplo.com'), false);
});

test('patente: formato viejo y Mercosur, normalizada con guiones', () => {
  assert.equal(L.normalizarPatente('ae 123 cd'), 'AE-123-CD');
  assert.equal(L.normalizarPatente('AE-123-CD'), 'AE-123-CD');
  assert.equal(L.normalizarPatente('abc123'), 'ABC-123');
  assert.equal(L.normalizarPatente('A1B2C3'), null);
  assert.equal(L.normalizarPatente(''), null);
});

test('total, cobrado y saldo del pedido', () => {
  const servicios = [{ id: 1, precio: 185000 }, { id: 4, precio: 45000 }];
  const pedido = { id: 1025, servicios: [1, 4] };
  const cobranzas = [
    { pedidoId: 1025, monto: 100000 },
    { pedidoId: 999, monto: 5000 },
    { pedidoId: 1025, monto: 30000 },
  ];
  assert.equal(L.totalPedido(pedido, servicios), 230000);
  assert.equal(L.cobradoPedido(pedido, cobranzas), 130000);
  assert.equal(L.saldoPedido(pedido, servicios, cobranzas), 100000);
});

test('estados del pedido', () => {
  assert.equal(L.siguienteEstado('Pendiente', 'confirmar'), 'Confirmado');
  assert.equal(L.siguienteEstado('Pendiente', 'rechazar'), 'Rechazado');
  assert.equal(L.siguienteEstado('Confirmado', 'asignar'), 'Asignado');
  assert.equal(L.siguienteEstado('Asignado', 'asignar'), 'Asignado');
  assert.equal(L.siguienteEstado('Asignado', 'iniciar'), 'En curso');
  assert.equal(L.siguienteEstado('En curso', 'finalizar'), 'Finalizado');
  assert.equal(L.siguienteEstado('Pendiente', 'iniciar'), null);
  assert.equal(L.siguienteEstado('Finalizado', 'confirmar'), null);
});

test('candados de baja', () => {
  const usuarios = [
    { dni: 1, rol: 'Administrador', activo: true },
    { dni: 2, rol: 'Administrador', activo: false },
    { dni: 3, rol: 'Chofer', activo: true },
  ];
  assert.equal(L.errorBaja(1, usuarios[0], usuarios), 'No podés darte de baja a vos mismo.');
  assert.equal(L.errorBaja(3, usuarios[0], usuarios), 'No se puede dar de baja al último administrador activo.');
  assert.equal(L.errorBaja(1, usuarios[1], usuarios), 'El usuario ya está dado de baja.');
  assert.equal(L.errorBaja(1, usuarios[2], usuarios), null);
});

test('candados de cambio de rol', () => {
  const u = { dni: 3, usuario: 'fernandezl', rol: 'Chofer' };
  assert.equal(L.errorCambioRol(3, u, 'Administrador'), 'No podés cambiar tu propio rol.');
  assert.equal(L.errorCambioRol(1, u, 'Chofer'), 'fernandezl ya tiene el rol Chofer.');
  assert.equal(L.errorCambioRol(1, u, 'Ayudante de Carga'), null);
});

test('formatos de plata y fechas', () => {
  assert.equal(L.money(185000), '$ 185.000');
  assert.equal(L.money(0), '$ 0');
  assert.equal(L.fecha('2026-10-01'), 'jue 1 oct');
  assert.equal(L.fechaLarga('2026-10-01'), 'jueves 1 de octubre');
  assert.equal(L.sumarDias('2026-09-29', 3), '2026-10-02');
  assert.equal(L.sumarDias('2026-09-29', -30), '2026-08-30');
  assert.equal(L.diaRelativo('2026-09-29', '2026-09-29'), 'Hoy');
  assert.equal(L.diaRelativo('2026-09-30', '2026-09-29'), 'Mañana');
  assert.equal(L.diaRelativo('2026-10-02', '2026-09-29'), 'vie 2 oct');
  assert.equal(L.iniciales('Carlos', 'Sarmiento'), 'CS');
});
