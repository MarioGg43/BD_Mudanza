# Sistema de Gestión "Mudanzas y Fletes Salta" — CRUD de Flota

Django + MySQL + phpMyAdmin sobre Docker. Implementa el ABM (alta,
baja, modificación, consulta) de la tabla `vehiculos` — Punto 3 del
Hito 1. La presentación, el DER y los DFDs del proyecto son el
material aparte en `proyecto mudanza/` (fuera de este repo).

## Puesta en marcha

```bash
cp .env.example .env  # crea el .env real con credenciales de desarrollo
docker compose up -d
docker exec mudanzas_web pip install -r requirements.txt
docker exec mudanzas_web python manage.py migrate
docker exec -it mudanzas_web python manage.py createsuperuser
docker exec -d mudanzas_web python manage.py runserver 0.0.0.0:8000
```

## Acceso

- Flota de vehículos: http://localhost:8002/
- Panel de administración: http://localhost:8002/admin/
- phpMyAdmin: http://localhost:8082/ (usuario y contraseña del archivo `.env`)

## Detener todo

```bash
docker compose down
```
