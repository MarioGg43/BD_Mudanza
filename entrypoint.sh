#!/bin/sh
set -e

echo "Esperando a que MySQL este disponible..."
python - <<'PY'
import socket, sys, time
for intento in range(40):
    try:
        s = socket.create_connection(("db", 3306), timeout=2)
        s.close()
        print("--> Conexion con MySQL establecida.")
        sys.exit(0)
    except OSError:
        print(f"--> Reintentando conexion con MySQL ({intento + 1}/40)...")
        time.sleep(2)
print("No se pudo conectar a la base de datos.")
sys.exit(1)
PY

echo "Aplicando migraciones..."
python manage.py makemigrations usuarios --noinput
python manage.py migrate --noinput

echo "Cargando datos iniciales..."
python manage.py init_data

echo "Levantando el servidor en http://0.0.0.0:8000 ..."
exec python manage.py runserver 0.0.0.0:8000
