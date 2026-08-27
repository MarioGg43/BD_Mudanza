# Diseño: CRUD de Vehículos — Sistema Mudanzas y Fletes Salta

## Contexto

El Grupo 5 (Taller de Programación, ISDM 8207) tiene ya resueltos, como
material estático (HTML/JS + imágenes + Word), los otros 3 puntos del
Hito 1: presentación de 5 diapositivas, DER de alto refinamiento (11
entidades) y DFDs del CRUD. Ese material vive en
`C:\Users\gaboo\Downloads\proyecto mudanzas\proyecto mudanza\` y no se
toca.

Lo que falta es que el **Punto 3 (CRUD/ABM de la tabla `vehiculos`)**
deje de ser una demo en `localStorage` y sea una aplicación real con
backend y base de datos persistente, siguiendo el mismo esquema que
usó otro grupo de la cursada para su propio CRUD (Django + MySQL +
Docker, ver `C:\repo git\BD_Proyecto` como referencia de estructura,
no de contenido).

## Objetivo

Aplicación Django que implemente el ABM completo (alta, baja,
modificación, consulta) de la tabla `vehiculos`, corriendo sobre MySQL
en Docker. Sin las otras 10 entidades del DER como código, sin
presentación ni DFDs embebidos en la app — esos deliverables ya
existen aparte.

## Alcance

**Incluye:**
- Proyecto Django `core` con una app `flota`.
- Modelo `Vehiculo` con los campos definidos en el DDL ya elaborado
  por el grupo.
- 4 vistas: listar, crear, editar, eliminar.
- Templates Bootstrap simples: tabla + formularios. Sin buscador, sin
  filtros, sin tarjetas de estadísticas, sin badges de color por
  estado (se simplifica respecto a la demo HTML original).
- Registro del modelo en Django Admin.
- Docker Compose con 3 servicios: MySQL 8.0, phpMyAdmin, Django
  (instalación manual de dependencias dentro del contenedor, igual
  que el proyecto de referencia).
- `.env` con credenciales de desarrollo (gitignored).

**No incluye (fuera de alcance para este spec):**
- Los otros 10 modelos del DER (usuarios, clientes, pedidos, etc.).
- Autenticación/roles de usuario.
- La presentación, el DER gráfico, los DFDs — siguen siendo los
  archivos estáticos ya entregados.
- Búsqueda, filtros o estadísticas en la UI.

## Arquitectura

```
mudanzas_django/
├── docker-compose.yml       # MySQL + phpMyAdmin + Django (manual install)
├── requirements.txt         # Django, PyMySQL, cryptography
├── .env                     # credenciales MySQL (gitignored)
├── manage.py
├── core/
│   ├── settings.py          # DB por variables de entorno (MySQL)
│   ├── urls.py
│   └── wsgi.py / asgi.py
└── flota/
    ├── models.py            # Vehiculo
    ├── forms.py             # VehiculoForm (ModelForm)
    ├── admin.py             # registro de Vehiculo
    ├── views.py             # listar / crear / editar / eliminar
    ├── urls.py
    └── templates/flota/
        ├── base.html
        ├── lista_vehiculos.html
        ├── create_vehiculo.html
        └── edit_vehiculo.html
```

## Modelo de datos

Tabla `vehiculos`, campos tomados del DDL ya definido por el grupo:

| Campo | Tipo Django | Notas |
|---|---|---|
| `id_vehiculo` | `AutoField` (PK) | |
| `patente` | `CharField(15)` | `unique=True` |
| `marca_modelo` | `CharField(100)` | |
| `tipo_vehiculo` | `CharField(50)` | |
| `capacidad_kg` | `DecimalField(10,2)` | |
| `capacidad_m3` | `DecimalField(10,2)` | |
| `estado` | `CharField` con `choices` | Disponible / En Viaje / En Mantenimiento / Fuera de Servicio; default `Disponible` |
| `kilometraje` | `DecimalField(10,2)` | default 0 |
| `anio` | `IntegerField` | opcional |
| `observaciones` | `TextField` | opcional |
| `created_at` | `DateTimeField(auto_now_add=True)` | |

## Vistas y flujo

Mismo patrón que el proyecto de referencia (`views.py` con funciones,
`ModelForm`, `django.contrib.messages` para feedback):

- `listaVehiculos` (`GET /vehiculos/`): lista completa, sin filtros.
- `createVehiculo` (`GET/POST /vehiculos/crear/`): formulario de alta.
- `editarVehiculo` (`GET/POST /vehiculos/editar/<id>/`): formulario de
  edición, `get_object_or_404`.
- `eliminarVehiculo` (`POST /vehiculos/eliminar/<id>/`, decorada con
  `@require_POST`): borrado directo (sin FKs que la referencien, no
  hace falta manejar `ProtectedError`).

## Manejo de errores

- Formulario inválido (ej. patente duplicada, campos obligatorios
  vacíos): se re-renderiza el formulario con los errores de Django
  Forms, más un mensaje de error vía `messages`.
- Edición/eliminación de un id inexistente: `get_object_or_404` → 404
  estándar de Django.

## Testing / verificación

Antes de dar el trabajo por terminado:
1. `docker compose up -d`, `migrate`, `createsuperuser`.
2. Verificar en el navegador: alta de un vehículo, que aparezca en el
   listado, edición de ese vehículo, eliminación, y que el listado
   quede vacío o correcto después.
3. Verificar `/admin/` para confirmar que el modelo quedó bien
   registrado.

No se agregan tests automatizados (no los tiene tampoco el proyecto
de referencia); la verificación es manual vía navegador, igual que se
hizo con Infinito Sonido.
