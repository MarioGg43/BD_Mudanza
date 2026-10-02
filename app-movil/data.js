/* Datos de ejemplo. Los usuarios, vehículos y servicios salen del init_data del
   sistema; el resto son ejemplos inventados. Las fechas se calculan desde hoy para
   que la demo siempre tenga mudanzas "de hoy" y "próximas". */
(function (root) {
  'use strict';
  const L = root.Logic || require('./logic.js');

  function buildSeed(hoy) {
    const d = (n) => L.sumarDias(hoy, n);

    const usuarios = [
      { dni: 35123456, nombre: 'Carlos', apellido: 'Sarmiento', correo: 'carlos.sarmiento@mudanzassalta.com.ar',
        telefono: '3874158820', usuario: 'sarmientoc', clave: 'Admin123!', rol: 'Administrador',
        activo: true, debeCambiar: false, alta: '2025-03-02', modificado: d(-12), baja: null, ultimoAcceso: d(-1) },
      { dni: 40987654, nombre: 'Luciana', apellido: 'Fernández', correo: 'luciana.f@mudanzassalta.com.ar',
        telefono: '3875550101', usuario: 'fernandezl', clave: 'Usuario123!', rol: 'Chofer',
        activo: true, debeCambiar: false, alta: '2025-06-15', modificado: d(-40), baja: null, ultimoAcceso: d(-1) },
      { dni: 38999888, nombre: 'Lucas', apellido: 'Romero', correo: 'lucas.romero@mudanzassalta.com',
        telefono: '3875550202', usuario: 'romerol', clave: 'Temporal123!', rol: 'Ayudante de Carga',
        activo: true, debeCambiar: true, alta: d(-2), modificado: d(-2), baja: null, ultimoAcceso: null },
      { dni: 33456123, nombre: 'Diego', apellido: 'Álvarez', correo: 'diego.alvarez@mudanzassalta.com.ar',
        telefono: '3875550303', usuario: 'alvarezd', clave: 'Chofer123!', rol: 'Chofer',
        activo: true, debeCambiar: false, alta: '2025-01-20', modificado: d(-90), baja: null, ultimoAcceso: d(0) },
      { dni: 41222333, nombre: 'Nicolás', apellido: 'Quispe', correo: 'nicolas.quispe@mudanzassalta.com.ar',
        telefono: '3875550404', usuario: 'quispen', clave: 'Ayudante123!', rol: 'Ayudante de Carga',
        activo: true, debeCambiar: false, alta: '2025-08-04', modificado: d(-60), baja: null, ultimoAcceso: d(0) },
      { dni: 39111444, nombre: 'Sofía', apellido: 'Castro', correo: 'sofia.castro@mudanzassalta.com.ar',
        telefono: '3875550505', usuario: 'castros', clave: 'Ayudante123!', rol: 'Ayudante de Carga',
        activo: false, debeCambiar: false, alta: '2025-02-11', modificado: d(-30), baja: d(-30), ultimoAcceso: d(-31) },
      { dni: 29876543, nombre: 'María', apellido: 'Gómez', correo: 'maria.gomez@ejemplo.com',
        telefono: '3874112233', usuario: 'gomezm', clave: 'Cliente123!', rol: 'Cliente',
        activo: true, debeCambiar: false, alta: '2026-04-18', modificado: d(-20), baja: null, ultimoAcceso: d(-1) },
      { dni: 31555666, nombre: 'Jorge', apellido: 'Herrera', correo: 'jorge.herrera@ejemplo.com',
        telefono: '3874998877', usuario: 'herreraj', clave: 'Cliente123!', rol: 'Cliente',
        activo: true, debeCambiar: false, alta: '2026-07-03', modificado: d(-9), baja: null, ultimoAcceso: d(-2) },
      { dni: 36777888, nombre: 'Ana', apellido: 'Cruz', correo: 'ana.cruz@ejemplo.com',
        telefono: '3875667788', usuario: 'cruza', clave: 'Cliente123!', rol: 'Cliente',
        activo: true, debeCambiar: false, alta: '2026-09-01', modificado: d(-5), baja: null, ultimoAcceso: d(-3) },
    ];

    const vehiculos = [
      { patente: 'AE-123-CD', marcaModelo: 'Mercedes-Benz Accelo 815', tipo: 'Camión Pesado', kg: 5000, m3: 32,
        estado: 'Disponible', km: 45200, anio: 2022, chofer: 40987654,
        obs: 'Equipado con rampa hidráulica y mantas de protección.' },
      { patente: 'AF-456-EF', marcaModelo: 'Ford Transit Chasis', tipo: 'Utilitario Mediano', kg: 2200, m3: 18,
        estado: 'En Viaje', km: 28100, anio: 2023, chofer: 33456123,
        obs: 'Asignado a servicio interurbano Salta - Cafayate.' },
      { patente: 'AC-789-GH', marcaModelo: 'Iveco Daily 70C17', tipo: 'Camión Liviano', kg: 3500, m3: 24,
        estado: 'En Mantenimiento', km: 89300, anio: 2020, chofer: null,
        obs: 'Service programado de frenos y amortiguadores.' },
      { patente: 'AD-321-JK', marcaModelo: 'Renault Master Furgón', tipo: 'Furgón Urbano', kg: 1600, m3: 12,
        estado: 'Disponible', km: 34500, anio: 2021, chofer: null,
        obs: 'Ideal para fletes rápidos en microcentro.' },
      { patente: 'AG-234-NP', marcaModelo: 'Mercedes-Benz Sprinter 515', tipo: 'Furgón Grande', kg: 2500, m3: 16,
        estado: 'Disponible', km: 12040, anio: 2024, chofer: null,
        obs: 'Caja cerrada con amarres internos.' },
    ];

    const servicios = [
      { id: 1, tipo: 'Mudanza local', precio: 185000, materiales: ['Mantas', 'Film', 'Cintas'],
        detalle: 'Dentro de Salta Capital y alrededores.' },
      { id: 2, tipo: 'Mudanza nacional', precio: 640000, materiales: ['Mantas', 'Film', 'Cintas', 'Zunchos'],
        detalle: 'A cualquier provincia del país.' },
      { id: 3, tipo: 'Flete urbano', precio: 75000, materiales: ['Correas', 'Mantas'],
        detalle: 'Traslado de pocos objetos en la ciudad.' },
      { id: 4, tipo: 'Embalaje profesional', precio: 45000, materiales: ['Cajas', 'Papel burbuja', 'Film', 'Cintas'],
        detalle: 'Embalamos todo antes de cargar.' },
    ];

    const hist = (pares) => pares.map(([estado, dia]) => ({ estado, fecha: d(dia) }));

    const pedidos = [
      { id: 1019, clienteDni: 29876543, fecha: d(-10), origen: 'Caseros 890, Salta',
        destino: 'Av. Reyes Católicos 1500, Salta', servicios: [1], patente: 'AD-321-JK', estado: 'Rechazado',
        motivo: 'No hay vehículos disponibles para esa fecha. Probá con otro día.',
        inventario: [{ desc: 'Placard de dos puertas', cant: 1, peso: 60, fragil: false }],
        choferDni: null, ayudantes: [], materiales: [], historial: hist([['Pendiente', -13], ['Rechazado', -12]]) },
      { id: 1020, clienteDni: 31555666, fecha: d(-3), origen: 'Mitre 455, Salta', destino: 'Alvarado 1120, Salta',
        servicios: [3], patente: 'AD-321-JK', estado: 'Finalizado',
        inventario: [{ desc: 'Escritorio', cant: 1, peso: 35, fragil: false },
          { desc: 'Monitor', cant: 2, peso: 5, fragil: true }],
        choferDni: 33456123, ayudantes: [41222333], materiales: ['Correas', 'Mantas'],
        historial: hist([['Pendiente', -6], ['Confirmado', -5], ['Asignado', -4], ['En curso', -3], ['Finalizado', -3]]) },
      { id: 1021, clienteDni: 29876543, fecha: d(-6), origen: 'Balcarce 210, Salta',
        destino: 'Los Ceibos 340, Tres Cerritos, Salta', servicios: [1], patente: 'AG-234-NP', estado: 'Finalizado',
        inventario: [{ desc: 'Juego de living', cant: 1, peso: 90, fragil: false },
          { desc: 'Cajas de libros', cant: 10, peso: 12, fragil: false }],
        choferDni: 33456123, ayudantes: [41222333], materiales: ['Mantas', 'Film', 'Cintas'],
        historial: hist([['Pendiente', -10], ['Confirmado', -9], ['Asignado', -8], ['En curso', -6], ['Finalizado', -6]]) },
      { id: 1022, clienteDni: 36777888, fecha: d(0), origen: 'España 1340, Salta', destino: 'Av. Tavella 3200, Salta',
        servicios: [3], patente: 'AF-456-EF', estado: 'En curso',
        inventario: [{ desc: 'Lavarropas', cant: 1, peso: 70, fragil: false },
          { desc: 'Cajas de ropa', cant: 6, peso: 8, fragil: false }],
        choferDni: 33456123, ayudantes: [41222333], materiales: ['Correas', 'Mantas'],
        historial: hist([['Pendiente', -4], ['Confirmado', -3], ['Asignado', -2], ['En curso', 0]]) },
      { id: 1023, clienteDni: 31555666, fecha: d(0), origen: 'Alvarado 1120, Salta',
        destino: 'Av. San Martín 2100, Salta', servicios: [3], patente: 'AE-123-CD', estado: 'Asignado',
        inventario: [{ desc: 'Heladera con freezer', cant: 1, peso: 85, fragil: false },
          { desc: 'Colchón de dos plazas', cant: 1, peso: 25, fragil: false },
          { desc: 'Vajilla embalada', cant: 4, peso: 9, fragil: true }],
        choferDni: 40987654, ayudantes: [38999888], materiales: ['Correas', 'Mantas'],
        historial: hist([['Pendiente', -3], ['Confirmado', -2], ['Asignado', -1]]) },
      { id: 1024, clienteDni: 36777888, fecha: d(5), origen: 'Pellegrini 780, Salta',
        destino: 'Bv. San Juan 1020, Córdoba', servicios: [2, 4], patente: 'AE-123-CD', estado: 'Confirmado',
        inventario: [{ desc: 'Juego de comedor', cant: 1, peso: 120, fragil: false },
          { desc: 'Televisor 55"', cant: 1, peso: 18, fragil: true },
          { desc: 'Cajas de cocina', cant: 12, peso: 7, fragil: true }],
        choferDni: null, ayudantes: [], materiales: [],
        historial: hist([['Pendiente', -2], ['Confirmado', -1]]) },
      { id: 1025, clienteDni: 29876543, fecha: d(3), origen: 'Av. Belgrano 1250, Salta',
        destino: 'Los Ceibos 340, Tres Cerritos, Salta', servicios: [1, 4], patente: 'AD-321-JK', estado: 'Pendiente',
        inventario: [{ desc: 'Heladera', cant: 1, peso: 80, fragil: false },
          { desc: 'Televisor 50"', cant: 1, peso: 14, fragil: true },
          { desc: 'Sillas', cant: 6, peso: 4, fragil: false }],
        choferDni: null, ayudantes: [], materiales: [],
        historial: hist([['Pendiente', -1]]) },
    ];

    const cobranzas = [
      { id: 1, pedidoId: 1020, monto: 40000, metodo: 'Efectivo', fecha: d(-3) },
      { id: 2, pedidoId: 1021, monto: 185000, metodo: 'Transferencia', fecha: d(-6) },
      { id: 3, pedidoId: 1022, monto: 75000, metodo: 'Tarjeta de débito', fecha: d(-1) },
    ];

    return {
      version: 1,
      creado: hoy,
      roles: ['Administrador', 'Chofer', 'Ayudante de Carga', 'Cliente'],
      tiposVehiculo: ['Camión Pesado', 'Camión Liviano', 'Furgón Grande', 'Furgón Urbano', 'Utilitario Mediano'],
      estadosVehiculo: ['Disponible', 'En Viaje', 'En Mantenimiento', 'Fuera de Servicio'],
      metodosPago: ['Efectivo', 'Transferencia', 'Tarjeta de débito', 'Tarjeta de crédito'],
      usuarios, vehiculos, servicios, pedidos, cobranzas,
      seq: { pedido: 1026, cobranza: 4, servicio: 5 },
    };
  }

  if (typeof module !== 'undefined' && module.exports) module.exports = buildSeed;
  else root.buildSeed = buildSeed;
})(typeof window !== 'undefined' ? window : globalThis);
