# App móvil Mudanzas Salta — diseño aprobado

Fecha: 2026-09-29. Aprobado por el usuario en el chat, sección por sección.

## Objetivo
Prototipo navegable de la app móvil completa para presentar en Desarrollo Móvil. Debe
funcionar "casi como programado" y poder importarse a Figma (plugin html.to.design) para
conectar las pantallas en modo Prototype.

## Decisiones
- Usuarios: Cliente, Administrador y Empleado (Chofer / Ayudante de Carga). Menú propio por rol.
- Estilo: manual de identidad. Poppins; naranja #FF7A00, rojo #E10E0E, coral #FC7753,
  amarillo #FFC107; degradé naranja→rojo; sobre fondo de color, logo en blanco.
- Forma: página web (Artifact multi-archivo) + copia local en Descargas + guía para Figma.
- Datos: en memoria + localStorage del navegador (try/catch), botón "Reiniciar demo".
- Sin Sueldos.

## Pantallas (★ = consigna)
Sin sesión: ★Inicio, ★Iniciar sesión (con accesos rápidos por rol), ★Registrarse (cliente),
Recuperar contraseña, Cambiar contraseña (obligatorio).
Cliente: Inicio, Pedir mudanza (fecha+direcciones → servicios → vehículo → inventario →
resumen), Mis pedidos, Detalle del pedido.
Administrador: Panel, Pedidos (lista + detalle con confirmar/rechazar), Asignar recursos,
Registrar cobro, ★Vehículos (lista con buscador/filtros, detalle, agregar, editar, baja con
confirmación), Usuarios (lista, alta con usuario automático, modificar correo, cambiar rol,
restablecer clave, baja/reactivar con candados), Servicios (catálogo, precio, materiales).
Empleado: Mis mudanzas (hoy / próximas / realizadas), Detalle (iniciar / finalizar).
Todos: ★Perfil (editar, guardar, cerrar sesión).
Extra: página "Todas las pantallas" (galería estática para importar a Figma).

## Reglas de negocio
- Estados del pedido: Pendiente → Confirmado → Asignado → En curso → Finalizado; o Rechazado.
- Total del pedido = suma de precios base de sus servicios; saldo = total − cobros.
- Clave fuerte: 8+ caracteres, mayúscula, número y símbolo. Claves nuevas deben coincidir.
- Usuario automático: apellido + inicial del nombre, en minúsculas y sin tildes; si existe, se
  agrega un número.
- Candados: nadie se da de baja ni se cambia el rol a sí mismo; no se puede dar de baja al
  último administrador activo.
- Baja de vehículo = estado "Fuera de Servicio".
- Vehículo del pedido: el cliente elige entre los disponibles; el administrador puede cambiarlo
  al asignar.

## Datos de ejemplo (del init_data del sistema)
Usuarios: Carlos Sarmiento (sarmientoc, Administrador, Admin123!), Luciana Fernández
(fernandezl, Chofer, Usuario123!), Lucas Romero (romerol, Ayudante, Temporal123!, debe cambiar
clave) + empleados y clientes extra. Vehículos: AE-123-CD, AF-456-EF, AC-789-GH, AD-321-JK.
Servicios: Mudanza local $185.000, Mudanza nacional $640.000, Flete urbano $75.000.

## Fuera del DER (se usan igual, lo decide el grupo)
Estado del pedido, direcciones de origen y destino, rol Cliente, descripción del objeto en el
inventario, empleados asignados por pedido.
