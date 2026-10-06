# Permisos editables y control de acceso por permisos (corrección del Hito 2)

Fecha: 06/10/2026. Rama: `permisos-editables` (sale de `hito3-pedidos`).

## 1. Problema

El Hito 2 pide crear perfiles y permisos para administrar la seguridad del sistema,
pero el sistema tiene dos problemas:

- Las operaciones del Hito 2 (panel, ABM de usuarios, flota y portal) deciden el
  acceso mirando si el rol **se llama** «Administrador». La tabla PERMISOS está
  cargada, pero solo la usan los pedidos y servicios del Hito 3.
- No hay pantalla para crear roles ni para elegir qué permisos tiene cada uno.

El profesor marcó «los permisos y lo editable». Otro grupo lo resolvió con un ABM de
roles que asigna permisos con casillas.

## 2. Objetivo

1. Un **ABM de roles**: listar, crear, editar (nombre, descripción y permisos con
   casillas) y eliminar los que no tengan usuarios.
2. **Todo el control de acceso por permisos**, consultando PERMISOS_ROLES: las
   pantallas, las operaciones, el menú, los botones del panel y la pantalla a la que
   se llega después de iniciar sesión.

La estructura de la base no cambia: PERMISOS, ROLES y PERMISOS_ROLES ya existen.

## 3. Catálogo de permisos

El catálogo es fijo y está definido en el código (`usuarios/permisos.py`, constante
`CATALOGO`, como una lista de `(área, código, descripción)`). Desde la pantalla de
roles los permisos se **asignan**, pero no se crean: un permiso nuevo no tendría efecto
si el código no lo controla.

| Área | Código | Descripción |
|---|---|---|
| Usuarios | USR_CONSULTAR | Ver el panel de usuarios |
| Usuarios | USR_CREAR | Dar de alta usuarios |
| Usuarios | USR_EDITAR_CORREO | Modificar el correo de un usuario |
| Usuarios | USR_CAMBIAR_ROL | Cambiar el rol de un usuario |
| Usuarios | USR_BAJA | Dar de baja y reactivar usuarios |
| Usuarios | USR_RESET_CLAVE | Restablecer la clave de un usuario |
| Roles | ROL_GESTIONAR | Ver, crear y editar roles y sus permisos |
| Vehículos | VEH_GESTIONAR | Alta, modificación y baja de vehículos |
| Personal | MUDANZAS_OPERAR | Ver el portal del personal y sus vehículos asignados |
| Pedidos | PED_REGISTRAR | Registrar pedidos de mudanza |
| Pedidos | PED_CONSULTAR | Consultar pedidos |
| Pedidos | PED_GESTIONAR | Confirmar y finalizar pedidos (y ver los de todos) |
| Pedidos | PED_ANULAR | Anular pedidos |
| Pedidos | PED_COMPROBANTE | Emitir el comprobante del pedido |
| Servicios | SRV_GESTIONAR | Alta, modificación y baja de servicios |

`MUDANZAS_ADMIN` desaparece: se renombra a `VEH_GESTIONAR`.

**Permisos iniciales:**
- **Administrador:** todos, menos PED_REGISTRAR.
- **Chofer y Ayudante de Carga:** MUDANZAS_OPERAR.
- **Cliente:** PED_REGISTRAR, PED_CONSULTAR y PED_COMPROBANTE.

## 4. Datos: cargar sin pisar lo editado

- `init_data` crea los permisos del catálogo (con `get_or_create` y la descripción
  actualizada) y asigna los permisos iniciales **solo cuando crea el rol**. Si el rol
  ya existe, no le toca los permisos: así no pisa lo que se editó desde la pantalla,
  aunque el contenedor arranque de nuevo.
- La migración de datos `usuarios/0006_permisos_editables` es para las bases que ya
  existen:
  - renombra MUDANZAS_ADMIN a VEH_GESTIONAR (con la descripción nueva);
  - crea USR_CONSULTAR, USR_CAMBIAR_ROL y ROL_GESTIONAR;
  - si existe el rol Administrador, le asigna esos tres más VEH_GESTIONAR.

  La reversa no hace nada. En una base nueva, la migración corre antes de que existan
  los roles y no asigna nada; después `init_data` crea los roles con sus permisos
  iniciales.

## 5. Control de acceso

Todo vive en `usuarios/permisos.py`:
- `get_usuario_actual(request)`, que se mueve desde `usuarios/views.py`.
  `usuarios.views` lo reexporta para no romper lo que lo importa.
- `permisos_de(usuario) -> set[str]`.
- `tiene_permiso(usuario, codigo) -> bool`.
- `requiere_permiso(codigo)`, decorador para pantallas: sin sesión manda a `login`;
  sin el permiso responde 403. Deja el usuario en `request.usuario`.
- `requiere_permiso_api(codigo)`, decorador para las operaciones JSON del panel: sin
  sesión responde 401 y sin el permiso, 403. Usa el mismo JSON
  `{'ok': False, 'error': ...}` que hoy.
- `pantalla_inicio(usuario)`: la redirección después del login. Elige la primera
  que corresponda:
  1. `admin_dashboard`, si tiene USR_CONSULTAR;
  2. `pedidos_lista`, si tiene PED_CONSULTAR;
  3. `pedidos_nuevo`, si tiene PED_REGISTRAR;
  4. `usuario_portal`, si tiene MUDANZAS_OPERAR;
  5. `lista_vehiculos`, si tiene VEH_GESTIONAR;
  6. `servicios_lista`, si tiene SRV_GESTIONAR;
  7. `roles_lista`, si tiene ROL_GESTIONAR;
  8. si no tiene ninguno, `sin_permisos`.

`pedidos/permisos.py` pasa a reexportar `tiene_permiso` y `requiere_permiso` desde
`usuarios.permisos`.

**Qué pide cada cosa:**

| Pantalla / operación | Permiso |
|---|---|
| `/panel/` | USR_CONSULTAR (sin sesión → login; sin permiso → `pantalla_inicio`) |
| Alta de usuario, vista previa del usuario | USR_CREAR |
| Modificar correo | USR_EDITAR_CORREO |
| Cambiar rol | USR_CAMBIAR_ROL |
| Baja y reactivación | USR_BAJA |
| Restablecer clave | USR_RESET_CLAVE |
| `/roles/` y subrutas | ROL_GESTIONAR |
| `/vehiculos/` y subrutas | VEH_GESTIONAR |
| `/portal/` | MUDANZAS_OPERAR (sin el permiso → `pantalla_inicio`) |
| `/` (portada) | Pública; con sesión → `pantalla_inicio` |
| Pedidos y servicios | Sin cambios (ya usan permisos) |

**Pantalla «sin permisos»** (`/sin-permisos/`, requiere sesión): muestra «Tu rol todavía
no tiene pantallas asignadas. Pedile al administrador que te asigne permisos» y el
botón Salir.

**Menú y botones:**
- Un procesador de contexto, `usuarios.context_processors.seguridad`, pone en todas
  las plantillas `permisos` (el conjunto de códigos del usuario, o vacío sin sesión) y
  `usuario_sesion`.
- El menú de `vehiculos/base.html` y los encabezados del panel y del portal muestran cada opción
  según el permiso:
  - Usuarios → USR_CONSULTAR;
  - Roles → ROL_GESTIONAR;
  - Vehículos → VEH_GESTIONAR;
  - Pedidos o Mis pedidos → PED_CONSULTAR («Pedidos» si además tiene PED_GESTIONAR);
  - Pedir mudanza → PED_REGISTRAR;
  - Servicios → SRV_GESTIONAR;
  - Portal → MUDANZAS_OPERAR.
- En el panel, cada botón aparece solo con su permiso: «Alta de Usuario», el selector
  de rol, modificar correo, restablecer clave, baja y reactivar.
- La sesión deja de usar `usuario_rol` para decidir nada (el valor puede quedar
  guardado, pero no se usa).

**Lo que sigue usando el nombre del rol** (es un dato, no un control de acceso):
- el registro de clientes asigna el rol «Cliente»;
- el combo de chofer en vehículos lista los usuarios con rol «Chofer»;
- el filtro «Cliente» de la consulta de pedidos lista los usuarios con rol «Cliente».

## 6. ABM de roles

Vive en `usuarios/roles.py` (vistas), `usuarios/forms.py` (RolForm) y las plantillas
`usuarios/templates/roles/` (estilo Bootstrap de marca, extienden
`vehiculos/base.html`). Las rutas:
- `/roles/`: lista con nombre, descripción, cantidad de usuarios y permisos como
  etiquetas, más el botón «Nuevo rol».
- `/roles/nuevo/` y `/roles/<id>/editar/`: nombre (obligatorio, hasta 100 caracteres
  y único), descripción (opcional, hasta 100) y las casillas del catálogo agrupadas por
  área, cada una con su descripción.
- `/roles/<id>/eliminar/` (POST): solo si el rol no tiene usuarios y no es un rol del
  sistema. Es borrado físico, porque nada referencia un rol sin usuarios: se borran
  sus filas de PERMISOS_ROLES y el rol.

**Candados** (en `usuarios/reglas_roles.py`; se muestran como errores del formulario
o como mensaje):
1. `ROLES_DEL_SISTEMA = ('Administrador', 'Cliente', 'Chofer', 'Ayudante de Carga')`
   (los cuatro que `init_data` vuelve a crear por nombre): se les pueden editar
   la descripción y los permisos, pero no el nombre, y no se pueden eliminar.
2. Nadie puede quitarle ROL_GESTIONAR a su propio rol: «No podés quitarte el permiso
   de gestionar roles».
3. Siempre tiene que quedar al menos un usuario **activo** con ROL_GESTIONAR. Se
   controla en tres lugares:
   - al editar un rol (quitar el permiso);
   - al cambiar el rol de un usuario;
   - al dar de baja un usuario.

   Reemplaza al candado de «último administrador activo». Mensaje: «El sistema tiene que
   quedar con al menos un usuario activo que pueda gestionar roles».

Siguen como hasta ahora los candados del Hito 2 de «no te podés dar de baja ni cambiar
tu propio rol».

## 7. Pruebas

- **Siguen pasando** todas las pruebas actuales. Las que verifican 401/403 del panel
  siguen siendo válidas, porque el Administrador inicial tiene todos los permisos de
  usuarios y el Chofer ninguno.
- **Nuevas:**
  - **Catálogo e `init_data`:**
    - existen los 15 permisos y no existe MUDANZAS_ADMIN;
    - correr `init_data` dos veces no repone un permiso que se le quitó a un rol.
  - **ABM de roles:**
    - crear un rol con permisos;
    - editar sus permisos;
    - nombre repetido;
    - eliminar un rol sin usuarios;
    - no eliminar un rol con usuarios ni un rol del sistema;
    - no renombrar un rol del sistema;
    - solo entra quien tiene ROL_GESTIONAR.
  - **Candados:**
    - quitarse ROL_GESTIONAR;
    - dejar el sistema sin gestor activo, al editar el rol, al cambiar el rol y al dar
      de baja.
  - **Rol a medida, «Recepcionista»** (USR_CONSULTAR, USR_CREAR, PED_CONSULTAR,
    PED_GESTIONAR):
    - entra al panel y da de alta;
    - recibe 403 en baja, cambio de rol y restablecer clave;
    - ve los pedidos y confirma, pero no anula;
    - no entra a vehículos ni a roles;
    - el menú muestra solo lo suyo.
  - **Inicio:**
    - cada rol inicial llega a su pantalla;
    - un rol sin permisos llega a «sin permisos».
  - **Panel:** un rol sin USR_BAJA no ve el botón de baja.

## 8. Entregables

- README: actualizar «Reglas del Hito 2» y la tabla de permisos.
- Archivo de contexto y página de cambios del DER/DFD: el DER no cambia de
  estructura, pero sí cambian los datos de PERMISOS. El DFD «Gestionar Usuarios» suma
  el proceso «Gestionar Roles».
