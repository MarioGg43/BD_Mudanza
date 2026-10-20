# Mudanzas y Fletes Salta — Django + MySQL + Docker

Sistema de gestión del Grupo 5. Reúne los dos hitos de Taller de Programación
en un solo proyecto:

- **Hito 1** — CRUD de vehículos (app `vehiculos`).
- **Hito 2** — usuarios, roles y permisos: alta, modificación, baja,
  restablecimiento de clave y cambio obligatorio en el próximo ingreso
  (app `usuarios`).
- **Hito 3** — proceso completo del pedido de mudanza: registro por el cliente, consulta con filtros, confirmación, anulación y comprobante; ABM de servicios (app `pedidos`).
- **App móvil** — prototipo navegable de 35 pantallas para Desarrollo Móvil
  (carpeta `app-movil/`, independiente de Django).

La base de datos sigue el DER del grupo: **13 tablas**, con los mismos nombres
de tablas y columnas que el diagrama.

## Cómo levantarlo

Con Docker Desktop abierto:

```bash
docker compose up -d --build
```

El contenedor se encarga de todo: espera a MySQL, aplica las migraciones,
carga los datos iniciales y levanta el servidor. El `--build` solo hace falta
la primera vez o cuando cambian las dependencias.

Para bajarlo:

```bash
docker compose down
```

## Direcciones

| Dirección | Qué es |
|---|---|
| http://localhost:8002/ | Portada del sistema |
| http://localhost:8002/vehiculos/ | CRUD de vehículos (Hito 1, solo administrador) |
| http://localhost:8002/vehiculos/&lt;patente&gt;/ | Agenda del vehículo: próximos pedidos e historial |
| http://localhost:8002/login/ | Ingreso al sistema (Hito 2) |
| http://localhost:8002/registro/ | Crear cuenta de cliente |
| http://localhost:8002/pedidos/ | Pedidos: el cliente ve los suyos y el admin todos |
| http://localhost:8002/pedidos/nuevo/ | Pedir una mudanza (solo clientes) |
| http://localhost:8002/servicios/ | ABM de servicios (solo admin) |
| http://localhost:8002/objetos/ | Catálogo de objetos que el cliente elige para el inventario (solo admin) |
| http://localhost:8002/roles/ | Roles y sus permisos (quien tenga `ROL_GESTIONAR`) |
| http://localhost:8002/panel/ | Panel del administrador |
| http://localhost:8002/portal/ | Portal del personal operativo |
| http://localhost:8002/admin/ | Admin de Django |
| http://localhost:8082/ | phpMyAdmin |

## Usuarios de prueba

| Usuario | Contraseña | Rol | Qué ve |
|---|---|---|---|
| `sarmientoc` | `Admin123!` | Administrador | El panel completo |
| `fernandezl` | `Usuario123!` | Chofer | El portal del personal |
| `romerol` | `Temporal123!` | Ayudante de Carga | Le exige cambiar la clave al entrar |
| `gomezm` | `Cliente123!` | Cliente | Sus pedidos; puede pedir mudanzas |

**Admin de Django** (http://localhost:8002/admin/): usuario `admin`, contraseña `Admin123!`.
Es una cuenta aparte de las del sistema. En una instalación nueva no existe: se crea una vez con
`docker exec -it mudanzas_web python manage.py createsuperuser`.

**Base de datos** (phpMyAdmin en http://localhost:8082/, o un cliente MySQL en `localhost:3308`):
base `mudanzas_db`, usuario `mudanzas_user` / `mudanzas_pass`, o `root` / `root_pass`
(valores de `.env.example`, solo para desarrollo).

## Reglas del Hito 2

- El **nombre de usuario se genera solo**: apellido más la inicial del nombre.
- La **clave se guarda cifrada** con SHA-256; nunca se guarda en texto plano.
- La **modificación solo permite editar el correo**, y actualiza la fecha de
  última modificación.
- La **baja es lógica**: pasa `Estado_usuario` a falso y asienta la fecha de baja.
- El **alta y el restablecimiento** exigen cambiar la clave en el próximo ingreso.
- El **acceso se decide por permisos**, no por el nombre del rol: cada pantalla y cada
  operación consulta la tabla PERMISOS_ROLES del lado del servidor. El menú y los
  botones del panel muestran solo lo que el rol tiene habilitado.
- Los **roles se editan en `/roles/`**: se crean roles nuevos y se tildan sus permisos.
  Administrador, Cliente, Chofer y Ayudante de Carga son roles del sistema (se editan sus
  permisos, no su nombre); un rol solo se elimina si no tiene usuarios.
- **Clientes y personal son cuentas separadas:** un cliente no puede pasar a otro rol, ni
  alguien del personal a Cliente, y al rol Cliente solo se le pueden dar permisos sobre
  sus propios pedidos (registrar, consultar, anular y comprobante).
- La **clave de un cliente no la restablece la empresa**: el botón no aparece en su fila
  y el servidor lo rechaza. El cliente la recupera desde «Olvidé mi clave».
- **Candados:** nadie se da de baja ni se cambia el rol a sí mismo, nadie se quita el
  permiso de gestionar roles, y siempre queda al menos un usuario activo que pueda
  gestionar roles.
- **Sin escalada de privilegios:** quien no tiene ROL_GESTIONAR no puede crear, editar,
  dar de baja ni restablecer la clave de un usuario cuyo rol tenga permisos
  administrativos que él no tiene, ni asignarle ese rol a nadie.

| Permiso | Habilita | Administrador | Cliente | Chofer / Ayudante |
|---|---|---|---|---|
| `USR_CONSULTAR` | Ver el panel de usuarios | Sí | | |
| `USR_CREAR` | Dar de alta usuarios | Sí | | |
| `USR_EDITAR_CORREO` | Modificar el correo | Sí | | |
| `USR_CAMBIAR_ROL` | Cambiar el rol de un usuario | Sí | | |
| `USR_BAJA` | Dar de baja y reactivar | Sí | | |
| `USR_RESET_CLAVE` | Restablecer la clave | Sí | | |
| `ROL_GESTIONAR` | Ver, crear y editar roles | Sí | | |
| `VEH_GESTIONAR` | ABM de vehículos | Sí | | |
| `MUDANZAS_OPERAR` | Portal del personal | Sí | | Sí |
| `PED_REGISTRAR` | Registrar pedidos | | Sí | |
| `PED_CONSULTAR` | Consultar pedidos | Sí (todos) | Sí (los suyos) | |
| `PED_GESTIONAR` | Confirmar y finalizar pedidos | Sí | | |
| `PED_ANULAR` | Anular pedidos | Sí | | |
| `PED_COMPROBANTE` | Emitir el comprobante | Sí | Sí (los suyos) | |
| `SRV_GESTIONAR` | ABM de servicios | Sí | | |
| `OBJ_GESTIONAR` | Catálogo de objetos | Sí | | |

Estos son los permisos iniciales. `init_data` los carga solo cuando crea cada rol, así que
lo que se edite en `/roles/` no se pisa al reiniciar el contenedor.

## Reglas de vehículos

- Solo entra el **administrador**; sin sesión, la flota manda al login.
- La **patente es la clave**: se guarda en mayúsculas y sin espacios, y no se
  puede cambiar al editar.
- La **baja es lógica**: el vehículo pasa a «Fuera de Servicio» y conserva sus
  pedidos. Se reactiva editando el estado.
- Como **chofer asignado** solo se puede elegir un usuario activo con rol Chofer.

## Reglas del Hito 3

- El pedido tiene **cuatro estados**: Pendiente, Confirmado, Finalizado y Anulado.
- Un **vehículo está libre** en una fecha si está «Disponible» y no tiene otro pedido
  Pendiente o Confirmado ese día. Un vehículo hace un solo pedido por día.
- Al **registrar** se valida del lado del servidor: fecha de hoy a un año, hora de
  inicio libre, incluso de madrugada (si es para hoy, una hora que todavía no pasó), origen y
  destino distintos, **un solo servicio** activo (el total es su precio) y al menos un
  objeto. No se controla peso ni capacidad: la capacidad del vehículo se muestra solo
  como dato. Todo va en una transacción: si algo falla, no se guarda nada.
- En el **inventario**, cada objeto se elige de una lista de sugerencias
  (`reglas.OBJETOS_INVENTARIO`: Heladera, Cocina, Lavarropas, Microondas, Cama 1 plaza,
  Cama 2 plazas, Colchón, Ropero, Cómoda, Mesa, Sillas, Sillón, Televisor, Escritorio,
  Biblioteca, Cajas, Bolsos y valijas, Bicicleta y Plantas) o se escribe a mano si no está.
  Cada fila lleva objeto (hasta 100 caracteres), cantidad (1 a 999), si es frágil y una
  observación opcional (hasta 200 caracteres, por ejemplo «se desarma»).
- Las **transiciones** son: confirmar (Pendiente a Confirmado), finalizar (Confirmado a
  Finalizado) y anular (Pendiente o Confirmado a Anulado). Cualquier otra se rechaza.
- Un pedido **se finaliza recién cuando empezó la mudanza** (desde su fecha y hora de
  inicio). Antes, el detalle muestra desde cuándo se va a poder finalizar.
- La **anulación no borra**: exige un motivo de 5 a 200 caracteres, guarda fecha y
  usuario, y libera el vehículo para ese día. Nunca se elimina un pedido.
- El cliente solo ve sus propios pedidos; si pide uno ajeno recibe 404.
- Los **servicios** se dan de baja de forma lógica: no se ofrecen en pedidos nuevos,
  pero los pedidos viejos los conservan.
- **Lo que hay que llevar se elige de un catálogo** (tabla `OBJETOS`), no se escribe: así no se
  guardan variantes como «mesa» y «meza». Lo que no está en la lista va como **«Otro»**, con la
  observación obligatoria; el mismo objeto no se repite en un pedido (se suma la cantidad). El
  administrador amplía la lista desde `/objetos/`.
- El **tipo de vehículo** se elige de una lista cerrada (Utilitario Mediano, Furgón Urbano,
  Camión Liviano, Camión Pesado).
- Un **vehículo o cliente con pedidos activos** a futuro no se puede dar de baja (ni el vehículo pasar a mantenimiento) hasta anularlos.

| Permiso | Administrador | Cliente |
|---|---|---|
| `PED_REGISTRAR` | | Sí |
| `PED_CONSULTAR` | Sí (todos) | Sí (solo los suyos) |
| `PED_GESTIONAR` (confirmar y finalizar) | Sí | |
| `PED_ANULAR` | Sí | |
| `PED_COMPROBANTE` | Sí | Sí (solo los suyos) |
| `SRV_GESTIONAR` | Sí | |
| `OBJ_GESTIONAR` | Sí | |

Chofer y Ayudante de Carga no tienen permisos sobre pedidos.

## Limitaciones conocidas

- «Olvidé mi clave» es público y devuelve una clave provisoria para cualquier usuario.
  Viene del Hito 2 y el grupo todavía tiene que decidir qué hacer con él.

## Pruebas

Con los contenedores levantados (corren sobre MySQL, en una base temporal):

```bash
docker exec mudanzas_web python manage.py test
```

Las de la app móvil, con Node:

```bash
node --test app-movil/tests/logic.test.js app-movil/tests/store.test.js
```

## Arquitectura

| Contenedor | Imagen | Puerto | Para qué |
|---|---|---|---|
| `mudanzas_db` | `mysql:8.0` | 3308 | Base de datos |
| `mudanzas_phpmyadmin` | `phpmyadmin:5` | 8082 | Administrador web de MySQL |
| `mudanzas_web` | build local | 8002 | Django |

## Estructura

```
mudanzas_django/
├── docker-compose.yml      # Los 3 contenedores
├── Dockerfile              # Imagen de Django
├── entrypoint.sh           # Migra, carga datos y levanta el servidor
├── docker/mysql-init/      # Permiso para la base de pruebas (corre al crear el volumen)
├── requirements.txt
├── .env                    # Credenciales de MySQL (no versionado)
├── manage.py
├── core/                   # Configuración del proyecto
├── vehiculos/              # Hito 1: CRUD de vehículos
│   ├── views.py, forms.py, urls.py
│   └── templates/vehiculos/
├── usuarios/               # Hito 2: las 13 tablas del DER y la seguridad
│   ├── models.py           # Roles, Permisos, Usuarios, Vehículos, Pedidos…
│   ├── views.py, urls.py, utils.py, admin.py
│   ├── management/commands/init_data.py
│   ├── static/             # Logo y paleta de colores
│   └── templates/
├── pedidos/                # Hito 3: reglas.py, permisos.py, vistas y ABM de servicios
├── app-movil/              # Prototipo de la app móvil (HTML + JS)
└── docs/
    ├── sql/                # Script del esquema para la entrega
    ├── diagramas/          # DER y DFDs
    └── superpowers/        # Especificaciones de diseño
```

El modelo `Vehiculo` vive en la app `usuarios`, junto al resto del DER; la app
`vehiculos` lo importa para su CRUD.

## Datos de acceso a MySQL

Están en `.env`. Por defecto: usuario `mudanzas_user`, base `mudanzas_db`.
