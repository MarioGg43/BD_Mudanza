/* Reglas de negocio de la app. Son funciones puras: no tocan la pantalla ni el
   almacenamiento, así se pueden probar con Node (tests/logic.test.js). */
(function (root) {
  'use strict';

  function limpiar(texto) {
    return String(texto || '')
      .normalize('NFKD').replace(/[̀-ͯ]/g, '')
      .replace(/[^a-zA-Z0-9]/g, '').toLowerCase();
  }

  // Igual que generate_username del sistema: primer apellido + inicial del primer nombre.
  // Si ya existe, el sistema agrega 1, 2, 3...
  function username(apellido, nombre, existentes) {
    const ape = String(apellido || '').trim().split(/\s+/)[0];
    const nom = String(nombre || '').trim().split(/\s+/)[0];
    const base = (limpiar(ape) || 'usuario') + (limpiar(nom).charAt(0) || 'x');
    const usados = new Set((existentes || []).map((u) => String(u).toLowerCase()));
    let final = base;
    let i = 1;
    while (usados.has(final)) final = base + i++;
    return final;
  }

  // Mismos mensajes que validate_strong_password del sistema.
  function validarClave(clave) {
    const p = String(clave || '').trim();
    if (p.length < 8) return 'La contraseña debe tener al menos 8 caracteres.';
    if (!/[A-Z]/.test(p)) return 'La contraseña debe contener al menos una letra MAYÚSCULA (A-Z).';
    if (!/[a-z]/.test(p)) return 'La contraseña debe contener al menos una letra MINÚSCULA (a-z).';
    if (!/[0-9]/.test(p)) return 'La contraseña debe contener al menos un NÚMERO (0-9).';
    if (!/[^A-Za-z0-9]/.test(p)) return 'La contraseña debe contener al menos un caracter ESPECIAL (!@#$%&*-_).';
    return null;
  }

  function claveTemporal() {
    const mayus = 'ABCDEFGHJKLMNPQRSTUVWXYZ';
    const minus = 'abcdefghjkmnpqrstuvwxyz';
    const nums = '23456789';
    const specs = '!@#$%*-_';
    const todos = mayus + minus + nums + specs;
    const elegir = (s) => s[Math.floor(Math.random() * s.length)];
    const chars = [elegir(mayus), elegir(minus), elegir(nums), elegir(specs)];
    while (chars.length < 10) chars.push(elegir(todos));
    for (let i = chars.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [chars[i], chars[j]] = [chars[j], chars[i]];
    }
    return chars.join('');
  }

  function validarCorreo(c) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(String(c || '').trim());
  }

  // Acepta el formato viejo (ABC 123) y el Mercosur (AB 123 CD). Devuelve la
  // patente con guiones, como la guarda el sistema, o null si no es válida.
  function normalizarPatente(p) {
    const s = String(p || '').toUpperCase().replace(/[\s-]/g, '');
    let m = s.match(/^([A-Z]{2})(\d{3})([A-Z]{2})$/);
    if (m) return m[1] + '-' + m[2] + '-' + m[3];
    m = s.match(/^([A-Z]{3})(\d{3})$/);
    if (m) return m[1] + '-' + m[2];
    return null;
  }

  function totalPedido(pedido, servicios) {
    return (pedido.servicios || []).reduce((acc, id) => {
      const s = servicios.find((x) => x.id === id);
      return acc + (s ? s.precio : 0);
    }, 0);
  }

  function cobradoPedido(pedido, cobranzas) {
    return cobranzas.filter((c) => c.pedidoId === pedido.id).reduce((acc, c) => acc + c.monto, 0);
  }

  function saldoPedido(pedido, servicios, cobranzas) {
    return totalPedido(pedido, servicios) - cobradoPedido(pedido, cobranzas);
  }

  const TRANSICIONES = {
    Pendiente: { confirmar: 'Confirmado', rechazar: 'Rechazado' },
    Confirmado: { asignar: 'Asignado', rechazar: 'Rechazado' },
    Asignado: { asignar: 'Asignado', iniciar: 'En curso' },
    'En curso': { finalizar: 'Finalizado' },
  };

  function siguienteEstado(estado, accion) {
    return (TRANSICIONES[estado] && TRANSICIONES[estado][accion]) || null;
  }

  // Candados del sistema para la baja de usuarios.
  function errorBaja(actorDni, objetivo, usuarios) {
    if (objetivo.dni === actorDni) return 'No podés darte de baja a vos mismo.';
    if (!objetivo.activo) return 'El usuario ya está dado de baja.';
    if (objetivo.rol === 'Administrador') {
      const quedan = usuarios.filter((u) => u.rol === 'Administrador' && u.activo && u.dni !== objetivo.dni).length;
      if (quedan === 0) return 'No se puede dar de baja al último administrador activo.';
    }
    return null;
  }

  function errorCambioRol(actorDni, objetivo, nuevoRol) {
    if (objetivo.dni === actorDni) return 'No podés cambiar tu propio rol.';
    if (objetivo.rol === nuevoRol) return objetivo.usuario + ' ya tiene el rol ' + nuevoRol + '.';
    return null;
  }

  function money(n) {
    const entero = Math.round(Number(n) || 0);
    const conPuntos = String(Math.abs(entero)).replace(/\B(?=(\d{3})+(?!\d))/g, '.');
    return (entero < 0 ? '-$ ' : '$ ') + conPuntos;
  }

  const DIAS = ['dom', 'lun', 'mar', 'mié', 'jue', 'vie', 'sáb'];
  const DIAS_LARGOS = ['domingo', 'lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado'];
  const MESES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'];
  const MESES_LARGOS = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto',
    'septiembre', 'octubre', 'noviembre', 'diciembre'];

  function aFecha(iso) {
    const [y, m, d] = String(iso).split('-').map(Number);
    return new Date(y, m - 1, d);
  }

  function aIso(date) {
    const p = (n) => String(n).padStart(2, '0');
    return date.getFullYear() + '-' + p(date.getMonth() + 1) + '-' + p(date.getDate());
  }

  function hoyIso() {
    return aIso(new Date());
  }

  function sumarDias(iso, n) {
    const d = aFecha(iso);
    d.setDate(d.getDate() + n);
    return aIso(d);
  }

  function fecha(iso) {
    const d = aFecha(iso);
    return DIAS[d.getDay()] + ' ' + d.getDate() + ' ' + MESES[d.getMonth()];
  }

  function fechaLarga(iso) {
    const d = aFecha(iso);
    return DIAS_LARGOS[d.getDay()] + ' ' + d.getDate() + ' de ' + MESES_LARGOS[d.getMonth()];
  }

  function diaRelativo(iso, hoy) {
    if (iso === hoy) return 'Hoy';
    if (iso === sumarDias(hoy, 1)) return 'Mañana';
    if (iso === sumarDias(hoy, -1)) return 'Ayer';
    return fecha(iso);
  }

  function iniciales(nombre, apellido) {
    return (String(nombre || '').charAt(0) + String(apellido || '').charAt(0)).toUpperCase();
  }

  const Logic = {
    username, validarClave, claveTemporal, validarCorreo, normalizarPatente,
    totalPedido, cobradoPedido, saldoPedido, siguienteEstado, errorBaja, errorCambioRol,
    money, fecha, fechaLarga, sumarDias, diaRelativo, hoyIso, iniciales,
  };

  if (typeof module !== 'undefined' && module.exports) module.exports = Logic;
  else root.Logic = Logic;
})(typeof window !== 'undefined' ? window : globalThis);
