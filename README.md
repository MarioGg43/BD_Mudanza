# Mudanzas y Fletes Salta — Django + MySQL + Docker

Sistema de gestión del Grupo 5. Reúne los dos hitos de Taller de Programación
en un solo proyecto:

- **Hito 1** — CRUD de vehículos (app `vehiculos`).
- **Hito 2** — usuarios, roles y permisos: alta, modificación, baja,
  restablecimiento de clave y cambio obligatorio en el próximo ingreso
  (app `usuarios`).
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
├── app-movil/              # Prototipo de la app móvil (HTML + JS)
└── docs/
    ├── diagramas/          # DER y DFDs
    └── superpowers/        # Especificaciones de diseño
```

El modelo `Vehiculo` vive en la app `usuarios`, junto al resto del DER; la app
`vehiculos` lo importa para su CRUD.

## Datos de acceso a MySQL

Están en `.env`. Por defecto: usuario `mudanzas_user`, base `mudanzas_db`.
