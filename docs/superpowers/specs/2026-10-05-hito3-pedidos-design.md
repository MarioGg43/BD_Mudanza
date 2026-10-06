# Hito 3 — Proceso completo: Pedido de mudanza

Fecha: 05/10/2026. Rama: `hito3-pedidos` (sale de `fusion-hitos`).
Consigna: `HITO Nro3_TallerDeProgramacion.pdf`.

## 1. Qué se construye

El proceso principal de negocio de Mudanzas y Fletes Salta: **el pedido de mudanza**,
desde que el cliente lo registra hasta que se finaliza o se anula.

- El **cliente** crea su cuenta, registra pedidos y consulta los suyos.
- El **administrador** consulta todos los pedidos y los confirma, finaliza o anula.
  También administra el catálogo de servicios.
- Chofer y Ayudante no participan en este hito.

Fuera de alcance: cobranzas, asignación de choferes y ayudantes a cada pedido,
y la vista del pedido para el chofer. La consigna no las pide.

## 2. Cómo se cubre la consigna

| Requisito | Solución |
|---|---|
| 3 tablas con FK y cabecera–detalle | PEDIDOS (cabecera) → DETALLE_PEDIDOS (servicios) e INVENTARIO_DETALLES (objetos). FK a USUARIOS, VEHICULOS y SERVICIOS |
| ABM de las tablas maestras que falten | ABM de SERVICIOS (con RECURSOS_ASIGNADOS como sus materiales). Vehículos (Hito 1) y usuarios (Hito 2) ya existen |
| N° de comprobante y fecha automáticos | `id_pedido` (autoincremental) y `Fecha_pedido` = hoy |
| Usuario automático | `id_usuario` = el cliente con la sesión iniciada |
| Datos relacionados por lista | Servicios con casillas y vehículo con lista desplegable. Nunca se escribe una clave a mano |
| Validaciones | Ver sección 6 |
| Cálculos automáticos | Subtotal por servicio, total del pedido y peso total del inventario |
| Estado automático | «Pendiente» al registrar |
| Actualización de entidades, con transacción | El vehículo queda reservado para la fecha del servicio; la anulación lo libera. Cada operación corre en `transaction.atomic()` |
| Anulación sin borrado físico | Estado «Anulado», con fecha, motivo y usuario. No hay ninguna vista que borre pedidos |
| Consulta con filtros | Rango de fechas, estado, cliente y servicio, con acceso al detalle |
| Comprobante imprimible o PDF | Página de comprobante con estilos de impresión; el navegador la guarda como PDF |
| Permisos del Hito 2, con una acción restringida | Se controlan con la tabla PERMISOS. El cliente registra pero no anula |

## 3. Cambios en la base (DER)

Una migración nueva en la app `usuarios`, que es donde viven los modelos del DER.

**PEDIDOS**

| Campo | Columna | Tipo | Nota |
|---|---|---|---|
| fecha_pedido (ya existe) | `Fecha_pedido` | DATE | Ahora es la fecha de registro, la pone el sistema |
| fecha_servicio | `Fecha_servicio` | DATE | Día de la mudanza |
| origen | `Direccion_origen` | VARCHAR(200) | |
| destino | `Direccion_destino` | VARCHAR(200) | |
| estado | `Estado_pedido` | VARCHAR(20) | Pendiente / Confirmado / Finalizado / Anulado |
| total | `Total_pedido` | DECIMAL(12,2) | Suma de los subtotales |
| fecha_anulacion | `Fec_anulacion` | DATETIME, nulo | |
| motivo_anulacion | `Motivo_anulacion` | VARCHAR(200), nulo | |
| usuario_anulacion | `id_usuario_anulacion` | FK USUARIOS, nulo | Quien anuló |

**DETALLE_PEDIDOS:** `Precio_unitario` y `Subtotal` (DECIMAL 12,2). El precio se copia
del servicio al registrar, para que el pedido no cambie si después se modifica el
precio del servicio. Como cada servicio se contrata una sola vez por pedido, el
subtotal es igual al precio. Se guarda igual, porque es el campo que suma el total y
el que muestra el comprobante. No se agrega columna de cantidad (YAGNI).

**INVENTARIO_DETALLES:** `Descripcion` (VARCHAR 100). `Peso` es el peso de cada unidad.

**SERVICIOS:** `Activo` (BOOLEAN, por defecto verdadero) para la baja lógica.

**ROLES:** se agrega el rol `Cliente`.

**PERMISOS:** se agregan los permisos de la tabla de la sección 5.

`init_data` carga el rol, los permisos, la clienta de prueba `gomezm` / `Cliente123!`
(la misma de la app móvil) y deja el pedido de ejemplo con los campos nuevos completos.

## 4. Pantallas

Todas usan el estilo Bootstrap de la flota de vehículos (`vehiculos/base.html`), que
ya maneja formularios y mensajes. Viven en una app nueva, `pedidos`.

| Dirección | Quién | Qué hace |
|---|---|---|
| `/registro/` | Público | Crear cuenta de cliente |
| `/pedidos/` | Cliente: los suyos. Admin: todos | Consulta con filtros |
| `/pedidos/nuevo/` | Cliente | Registrar un pedido |
| `/pedidos/<n>/` | El dueño o el admin | Detalle. El admin ve Confirmar / Finalizar / Anular |
| `/pedidos/<n>/anular/` | Admin | Formulario con el motivo (obligatorio) |
| `/pedidos/<n>/comprobante/` | El dueño o el admin | Comprobante para imprimir |
| `/pedidos/vehiculos-libres/?fecha=` | Cliente | JSON con los vehículos libres ese día, para el formulario |
| `/servicios/` y subrutas | Admin | ABM de servicios |

**Crear cuenta:** DNI, apellido, nombre, correo, teléfono, clave y repetir clave. El
usuario se genera con la regla del Hito 2, sumando un número si está repetido. La
clave pasa por `validate_strong_password` y se guarda con hash. El rol es Cliente y
`DebeCambiarClave` queda en falso, porque la clave la eligió el cliente. Después de
crear la cuenta, inicia sesión y va a «Mis pedidos».

**Login:** si el rol es Cliente, redirige a `/pedidos/`. El panel del administrador
suma los enlaces «Pedidos» y «Servicios».

**Registrar pedido**, en una sola página:
1. Fecha de la mudanza, origen y destino.
2. Servicios: casillas con el precio. El total se recalcula en vivo.
3. Inventario: filas con descripción, cantidad, peso por unidad y frágil, agregadas
   con «+ Agregar objeto» (formset de Django). El peso total se calcula en vivo.
4. Vehículo: lista desplegable que se recarga al cambiar la fecha
   (`vehiculos-libres`). Muestra la capacidad de cada uno.
5. Botón «Registrar pedido».

Los cálculos en pantalla son solo una ayuda: el servidor recalcula todo al guardar.
Si todo está bien, va al detalle del pedido con el mensaje
«Pedido N° X registrado. Queda pendiente hasta que la empresa lo confirme».

**Consulta:** tabla con N°, fecha de registro, fecha del servicio, cliente, servicios,
total y estado. Los filtros son: desde, hasta (sobre la fecha del servicio), estado,
servicio y cliente (este último solo para el admin). Por defecto muestra todo, del
más reciente al más viejo.

**Comprobante:** logo y datos de la empresa, N° de pedido, fechas, estado, cliente
(nombre, DNI, correo), origen y destino, vehículo, tabla de servicios con precio y
subtotal, total, inventario con el peso total y, si está anulado, la fecha, el motivo y
quién lo anuló. Tiene un botón «Imprimir / Guardar PDF» (`window.print()`) y una hoja
de estilos `@media print` que oculta el menú.

**ABM de servicios:** lista con tipo, precio, materiales y estado; alta, edición y
baja lógica, como en vehículos. Un servicio inactivo no aparece al registrar pedidos,
pero sigue en los pedidos que ya lo tenían. Los materiales se editan como texto
separado por comas y se guardan como filas de RECURSOS_ASIGNADOS.

## 5. Permisos

Se agrega `tiene_permiso(usuario, nombre)`, que consulta PERMISOS_ROLES. Las pantallas
nuevas usan un decorador `requiere_permiso('PED_...')`: sin sesión manda al login y,
sin el permiso, responde 403. El Hito 2 sigue controlando por nombre de rol; no se
toca porque ya está probado.

| Permiso | Administrador | Cliente | Chofer / Ayudante |
|---|---|---|---|
| PED_REGISTRAR | | ✓ | |
| PED_CONSULTAR | ✓ (todos) | ✓ (solo los suyos) | |
| PED_GESTIONAR (confirmar y finalizar) | ✓ | | |
| PED_ANULAR | ✓ | | |
| PED_COMPROBANTE | ✓ | ✓ (solo los suyos) | |
| SRV_ABM | ✓ | | |

«Ver todos» frente a «solo los suyos» no es un permiso aparte: quien tiene
PED_GESTIONAR ve todos, y el resto solo los propios. Si un cliente pide el detalle o el
comprobante de un pedido ajeno, recibe 404, para no revelar que el pedido existe.

## 6. Reglas del negocio (`pedidos/servicios.py`)

**Vehículo libre en una fecha:** su estado es «Disponible» y no tiene otro pedido
en estado Pendiente o Confirmado con esa misma `Fecha_servicio`. Un vehículo hace un
solo pedido por día.

**`registrar_pedido(cliente, datos)`**, dentro de `transaction.atomic()`:
1. Bloquea la fila del vehículo (`select_for_update`) y verifica que siga libre. Así,
   si dos clientes eligen el mismo vehículo para el mismo día, el segundo recibe un
   error y no se guarda nada.
2. Valida:
   - `Fecha_servicio` de hoy en adelante y como máximo a un año;
   - origen y destino obligatorios (hasta 200 caracteres) y distintos entre sí;
   - al menos un servicio, todos activos;
   - al menos un objeto: cantidad entera de 1 a 999, peso mayor a 0 y hasta
     5000 kg, descripción obligatoria;
   - el peso total (cantidad × peso, sumado) no supera la `capacidad_kg` del vehículo.
3. Crea la cabecera (estado Pendiente, `Fecha_pedido` = hoy), los detalles con el
   precio copiado y el inventario, y guarda el total.

Si falla cualquier paso, no queda nada guardado. Los errores vuelven al formulario
con los datos cargados.

**Transiciones:**

| Acción | Desde | Hacia | Permiso |
|---|---|---|---|
| confirmar | Pendiente | Confirmado | PED_GESTIONAR |
| finalizar | Confirmado | Finalizado | PED_GESTIONAR |
| anular | Pendiente o Confirmado | Anulado | PED_ANULAR |

Una transición inválida (por ejemplo, anular un pedido Finalizado) se rechaza con un
mensaje y no cambia nada. La anulación exige un motivo de 5 a 200 caracteres y guarda
la fecha y el usuario. Como un pedido Anulado ya no cuenta como ocupado, el vehículo
vuelve a estar libre ese día. Todas las acciones van por POST.

## 7. Pruebas

Sobre MySQL, en la base temporal, con `init_data` como en las 48 actuales.

- **Registro de cuenta:** genera el usuario, guarda la clave con hash, asigna el rol
  Cliente, no exige cambio de clave y rechaza un DNI o correo repetidos o una clave débil.
- **Registrar pedido:** caso correcto (estado, total, subtotales, precio copiado,
  usuario de la sesión, `Fecha_pedido` = hoy). Un caso por cada validación de la
  sección 6. Vehículo ocupado. Integridad: si falla un objeto del inventario, no queda
  la cabecera.
- **Transiciones:** las tres válidas y las inválidas. La anulación guarda fecha, motivo
  y usuario, y libera el vehículo.
- **Permisos:** el cliente no confirma ni anula (403), no ve pedidos ajenos (404) y su
  consulta solo lista los suyos. El chofer no registra. Sin sesión, todo va al login.
- **Consulta:** cada filtro por separado y combinados.
- **Comprobante:** muestra el total y los datos de la anulación cuando corresponde.
- **Servicios:** alta, modificación y baja lógica. Un servicio inactivo no se ofrece y
  el pedido viejo lo conserva. El cliente no entra al ABM.
- **Vehículos libres:** excluye los que están en mantenimiento y los ocupados, e
  incluye los que tienen el pedido anulado.

## 8. Entregables además del código

- `docs/sql/`: script del esquema completo, generado desde las migraciones
  (`sqlmigrate`), para «Scripts de base de datos actualizados».
- DFD «Registrar un Pedido» corregido con la notación del grupo. Es aparte del código:
  se arma después, con los nombres de esta especificación.
- Capturas de registración, consulta, anulación y comprobante.
- README y archivo de contexto actualizados.
