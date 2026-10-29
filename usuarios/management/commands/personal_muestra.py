"""Suma el personal de muestra que armó José (3 administradores, 2 choferes y 8 ayudantes en total).

Es aparte de init_data para que las pruebas sigan partiendo de una base mínima, y solo agrega: si
la persona ya existe (por DNI o correo) no la toca. Uso: python manage.py personal_muestra
"""
from datetime import date

from django.core.management.base import BaseCommand

from usuarios.models import Rol, Sueldo, Usuario
from usuarios.utils import hash_password, nombre_usuario_libre

PERSONAL = [
    ('Administrador', 34222111, 'Morales', 'Valeria', 'valeria.morales@mudanzassalta.com.ar', '3874158821', 'Admin123!'),
    ('Administrador', 36444333, 'Quiroga', 'Martín', 'martin.quiroga@mudanzassalta.com.ar', '3874158822', 'Admin123!'),
    ('Chofer', 39111222, 'Gutiérrez', 'Diego', 'diego.gutierrez@mudanzassalta.com.ar', '3875550102', 'Usuario123!'),
    ('Ayudante de Carga', 43111222, 'Acosta', 'Franco', 'franco.acosta@mudanzassalta.com.ar', '3875550203', 'Usuario123!'),
    ('Ayudante de Carga', 43333444, 'Benítez', 'Lautaro', 'lautaro.benitez@mudanzassalta.com.ar', '3875550204', 'Usuario123!'),
    ('Ayudante de Carga', 44555666, 'Pereyra', 'Camila', 'camila.pereyra@mudanzassalta.com.ar', '3875550205', 'Usuario123!'),
    ('Ayudante de Carga', 44777888, 'Rojas', 'Nicolás', 'nicolas.rojas@mudanzassalta.com.ar', '3875550206', 'Usuario123!'),
    ('Ayudante de Carga', 45111333, 'Aguirre', 'Tomás', 'tomas.aguirre@mudanzassalta.com.ar', '3875550207', 'Usuario123!'),
    ('Ayudante de Carga', 45888999, 'Herrera', 'Matías', 'matias.herrera@mudanzassalta.com.ar', '3875550208', 'Usuario123!'),
    ('Ayudante de Carga', 46222333, 'Díaz', 'Facundo', 'facundo.diaz@mudanzassalta.com.ar', '3875550209', 'Usuario123!'),
]


class Command(BaseCommand):
    help = 'Agrega el personal de muestra (no borra ni modifica a nadie).'

    def handle(self, *args, **options):
        sueldos = {'Administrador': Sueldo.objects.get_or_create(Monto=980000, Fecha_pago=date(2026, 9, 5))[0]}
        operario = Sueldo.objects.get_or_create(Monto=720000, Fecha_pago=date(2026, 9, 5))[0]
        creados = 0
        for nom_rol, dni, ape, nom, correo, tel, clave in PERSONAL:
            rol = Rol.objects.filter(nom_rol=nom_rol).first()
            if not rol or Usuario.objects.filter(DNI=dni).exists() or Usuario.objects.filter(Correo=correo).exists():
                continue
            Usuario.objects.create(DNI=dni, Apellido=ape, Nombre=nom, Correo=correo, Telefono=tel,
                                   NombreUsuario=nombre_usuario_libre(ape, nom), Clave=hash_password(clave),
                                   Activo=True, DebeCambiarClave=False, idRol=rol,
                                   idSueldo=sueldos.get(nom_rol, operario))
            creados += 1
        self.stdout.write(self.style.SUCCESS(f'Personal de muestra: {creados} persona(s) agregada(s).'))
