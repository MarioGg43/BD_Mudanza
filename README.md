# Django + MySQL + phpMyAdmin sobre Docker

Sistema de Gestión "Mudanzas y Fletes Salta" — un stack de 3 contenedores
con **instalación manual** de Django dentro del contenedor de Python.
Implementa el ABM (alta, baja, modificación, consulta) de la tabla
`vehiculos` — Punto 3 del Hito 1. La presentación, el DER y los DFDs
del proyecto son el material aparte en `proyecto mudanza/` (fuera de
este repo).

## Arquitectura

| Contenedor                | Imagen           | Puerto host | Para qué sirve                       |
|----------------------------|------------------|-------------|---------------------------------------|
| `mudanzas_db`              | `mysql:8.0`      | 3308        | Base de datos MySQL                  |
| `mudanzas_phpmyadmin`      | `phpmyadmin:5`   | 8082        | Administrador web de MySQL           |
| `mudanzas_web`             | `python:3.11`    | 8002        | Entorno donde corre Django           |

## Estructura de archivos

```
mudanzas_django/
├── docker-compose.yml      # Orquesta los 3 contenedores
├── requirements.txt        # Django + PyMySQL
├── .env.example            # Plantilla de credenciales de MySQL
├── .env                    # Credenciales reales (no versionado)
├── manage.py               # Lanzador de Django
├── core/                   # Configuración del proyecto
│   ├── __init__.py         # Activa PyMySQL como conector
│   ├── settings.py         # Conexión a MySQL vía variables de entorno
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
└── flota/                  # App del CRUD de vehículos
    ├── models.py           # Modelo Vehiculo
    ├── admin.py
    ├── forms.py
    ├── views.py
    ├── urls.py
    ├── migrations/
    └── templates/flota/
```

## Puesta en marcha (instalación manual)

### 1. Crear el archivo de credenciales

```bash
cp .env.example .env
```

### 2. Levantar los contenedores

En la carpeta del `docker-compose.yml`:

```bash
docker compose up -d
```

### 3. Entrar al contenedor de Django

```bash
docker exec -i -t mudanzas_web bash
```

### 4. Instalar Django y el conector MySQL (dentro del contenedor)

```bash
pip install -r requirements.txt
```

### 5. Aplicar las migraciones (crea las tablas en MySQL)

```bash
python manage.py migrate
```

### 6. Crear un superusuario para el panel /admin

```bash
python manage.py createsuperuser
```

### 7. Iniciar el servidor de desarrollo

```bash
python manage.py runserver 0.0.0.0:8000
```

> Tip: si no querés entrar al contenedor con `bash`, podés correr cada
> paso directo desde tu terminal con `docker exec mudanzas_web <comando>`
> (o `docker exec -it` para el paso de `createsuperuser`, y
> `docker exec -d` para dejar el `runserver` corriendo en segundo plano).

## Acceso

- Aplicación Django: http://localhost:8002/
- Panel de administración: http://localhost:8002/admin/
- phpMyAdmin: http://localhost:8082/ (usuario y contraseña del archivo `.env`)

## Detener todo

```bash
docker compose down
```

Para borrar también la base de datos:

```bash
docker compose down -v
```
