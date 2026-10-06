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
| http://localhost:8002/login/ | Ingreso al sistema (Hito 2) |
| http://localhost:8002/registro/ | Crear cuenta de cliente |
| http://localhost:8002/pedidos/ | Pedidos: el cliente ve los suyos y el admin todos |
| http://localhost:8002/pedidos/nuevo/ | Pedir una mudanza (solo clientes) |
| http://localhost:8002/servicios/ | ABM de servicios (solo admin) |
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

## Reglas del Hito 2

- El **nombre de usuario se genera solo**: apellido más la inicial del nombre.
- La **clave se guarda cifrada** con SHA-256; nunca se guarda en texto plano.
- La **modificación solo permite editar el correo**, y actualiza la fecha de
  última modificación.
- La **baja es lógica**: pasa `Estado_usuario` a falso y asienta la fecha de baja.
- El **alta y el restablecimiento** exigen cambiar la clave en el próximo ingreso.
- Hay **tres roles** con accesos distintos: Administrador, Chofer y Ayudante de Carga.
- Cada operación valida del lado del servidor que quien la llama sea un
  administrador activo.
- No se puede dar de baja al **último administrador activo** ni a uno mismo.

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
- Al **registrar** se valida del lado del servidor: fecha de hoy a un año, origen y
  destino distintos, al menos un servicio activo y un objeto, y que el peso total no
  supere la capacidad del vehículo. Todo va en una transacción: si algo falla, no se
  guarda nada.
- Las **transiciones** son: confirmar (Pendiente a Confirmado), finalizar (Confirmado a
  Finalizado) y anular (Pendiente o Confirmado a Anulado). Cualquier otra se rechaza.
- La **anulación no borra**: exige un motivo de 5 a 200 caracteres, guarda fecha y
  usuario, y libera el vehículo para ese día. Nunca se elimina un pedido.
- El cliente solo ve sus propios pedidos; si pide uno ajeno recibe 404.
- Los **servicios** se dan de baja de forma lógica: no se ofrecen en pedidos nuevos,
  pero los pedidos viejos los conservan.

| Permiso | Administrador | Cliente |
|---|---|---|
| `PED_REGISTRAR` | | Sí |
| `PED_CONSULTAR` | Sí (todos) | Sí (solo los suyos) |
| `PED_GESTIONAR` (confirmar y finalizar) | Sí | |
| `PED_ANULAR` | Sí | |
| `PED_COMPROBANTE` | Sí | Sí (solo los suyos) |
| `SRV_GESTIONAR` | Sí | |

Chofer y Ayudante de Carga no tienen permisos sobre pedidos.

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
