from datetime import date

from django.core.management.base import BaseCommand

from usuarios.models import (
    Rol, Permiso, PermisoRol, Usuario, Vehiculo, Sueldo, Servicio,
    RecursoAsignado, Pedido, DetallePedido, InventarioDetalle,
    Cobranza, DetalleCobranza,
)
from usuarios.utils import hash_password, generate_username


class Command(BaseCommand):
    help = 'Carga los roles, permisos, usuarios, vehículos y datos de ejemplo del DER'

    def handle(self, *args, **options):
        # 1. Permisos
        permisos_data = [
            ('USR_CREAR', 'Permite dar de alta nuevos usuarios'),
            ('USR_EDITAR_CORREO', 'Permite editar el correo del usuario'),
            ('USR_BAJA', 'Permite dar de baja usuarios'),
            ('USR_RESET_CLAVE', 'Permite restablecer contraseñas de usuarios'),
            ('MUDANZAS_ADMIN', 'Permite administrar mudanzas y fletes'),
            ('MUDANZAS_OPERAR', 'Permite operar y consultar servicios asignados'),
        ]
        permisos = {}
        for code, desc in permisos_data:
            p, _ = Permiso.objects.get_or_create(nom_permiso=code, defaults={'desc_permiso': desc})
            permisos[code] = p

        # 2. Roles
        r_admin, _ = Rol.objects.get_or_create(
            nom_rol='Administrador',
            defaults={'desc_rol': 'Acceso total a la administración de seguridad y usuarios'})
        r_chofer, _ = Rol.objects.get_or_create(
            nom_rol='Chofer',
            defaults={'desc_rol': 'Conducción de vehículos y visualización de rutas de mudanza'})
        r_ayudante, _ = Rol.objects.get_or_create(
            nom_rol='Ayudante de Carga',
            defaults={'desc_rol': 'Personal operativo de carga, descarga y embalaje de bultos'})

        for perm in permisos.values():
            PermisoRol.objects.get_or_create(idRol=r_admin, idPermiso=perm)
        PermisoRol.objects.get_or_create(idRol=r_chofer, idPermiso=permisos['MUDANZAS_OPERAR'])
        PermisoRol.objects.get_or_create(idRol=r_ayudante, idPermiso=permisos['MUDANZAS_OPERAR'])

        # 3. Sueldos
        sueldo_admin, _ = Sueldo.objects.get_or_create(Monto=980000, Fecha_pago=date(2026, 9, 5))
        sueldo_oper, _ = Sueldo.objects.get_or_create(Monto=720000, Fecha_pago=date(2026, 9, 5))

        # 4. Usuarios de prueba
        usuarios_data = [
            (35123456, 'Sarmiento', 'Carlos', 'carlos.sarmiento@mudanzassalta.com.ar',
             '3874158820', 'Admin123!', False, r_admin, sueldo_admin),
            (40987654, 'Fernandez', 'Luciana', 'luciana.f@mudanzassalta.com.ar',
             '3875550101', 'Usuario123!', False, r_chofer, sueldo_oper),
            (38999888, 'Romero', 'Lucas', 'lucas.romero@mudanzassalta.com',
             '3875550202', 'Temporal123!', True, r_ayudante, sueldo_oper),
        ]
        for dni, ape, nom, correo, tel, clave, debe_cambiar, rol, sueldo in usuarios_data:
            if not Usuario.objects.filter(DNI=dni).exists():
                u = Usuario.objects.create(
                    DNI=dni, Apellido=ape, Nombre=nom, Correo=correo, Telefono=tel,
                    NombreUsuario=generate_username(ape, nom),
                    Clave=hash_password(clave),
                    Activo=True, DebeCambiarClave=debe_cambiar,
                    idRol=rol, idSueldo=sueldo,
                )
                self.stdout.write(self.style.SUCCESS(
                    f'Usuario {u.NombreUsuario} ({rol.nom_rol}) creado.'))

        chofer = Usuario.objects.filter(DNI=40987654).first()

        # 5. Vehículos
        vehiculos_data = [
            ('AE-123-CD', 'Mercedes-Benz Accelo 815', 'Camión Pesado', 5000.0, 32.0,
             'Disponible', 45200.0, 2022, chofer, 'Equipado con rampa hidráulica y mantas de protección.'),
            ('AF-456-EF', 'Ford Transit Chasis', 'Utilitario Mediano', 2200.0, 18.0,
             'En Viaje', 28100.0, 2023, None, 'Asignado a servicio interurbano Salta - Cafayate.'),
            ('AC-789-GH', 'Iveco Daily 70C17', 'Camión Liviano', 3500.0, 24.0,
             'En Mantenimiento', 89300.0, 2020, None, 'Service programado de frenos y amortiguadores.'),
            ('AD-321-JK', 'Renault Master Furgón', 'Furgón Urbano', 1600.0, 12.0,
             'Disponible', 34500.0, 2021, None, 'Ideal para fletes rápidos en microcentro.'),
        ]
        for pat, marca, tipo, kg, m3, est, km, anio, ch, obs in vehiculos_data:
            if not Vehiculo.objects.filter(patente=pat).exists():
                Vehiculo.objects.create(
                    patente=pat, marca_modelo=marca, tipo_vehiculo=tipo,
                    capacidad_kg=kg, capacidad_m3=m3, estado=est, kilometraje=km,
                    anio=anio, chofer_asignado=ch, observaciones=obs)
                self.stdout.write(self.style.SUCCESS(f'Vehículo {pat} ({marca}) creado.'))

        # 6. Servicios y sus materiales
        servicios_data = [
            ('Mudanza local', 185000, 'Mantas, film y cintas'),
            ('Mudanza nacional', 640000, 'Mantas, film, cintas y zunchos'),
            ('Flete urbano', 75000, 'Correas y mantas'),
        ]
        for tipo, precio, materiales in servicios_data:
            serv, creado = Servicio.objects.get_or_create(
                Tipo_servicio=tipo, defaults={'Precio_base': precio})
            if creado:
                RecursoAsignado.objects.create(idServicio=serv, Materiales=materiales)
                self.stdout.write(self.style.SUCCESS(f'Servicio "{tipo}" creado.'))

        # 7. Un pedido de ejemplo, con su detalle, inventario y cobranza
        admin = Usuario.objects.filter(DNI=35123456).first()
        vehiculo = Vehiculo.objects.filter(patente='AE-123-CD').first()
        if admin and vehiculo and not Pedido.objects.exists():
            pedido = Pedido.objects.create(
                patente_vehiculo=vehiculo, idUsuario=admin, Fecha_pedido=date(2026, 9, 20))
            DetallePedido.objects.create(
                idPedido=pedido, idServicio=Servicio.objects.get(Tipo_servicio='Mudanza local'))
            InventarioDetalle.objects.create(idPedido=pedido, Peso=320.50, Cantidad=42, Fragil=True)
            cobranza = Cobranza.objects.create(Monto_cob=185000, Met_pag_cob='Transferencia')
            DetalleCobranza.objects.create(idPedido=pedido, idCobranza=cobranza)
            self.stdout.write(self.style.SUCCESS(
                'Pedido de ejemplo creado con detalle, inventario y cobranza.'))

        self.stdout.write(self.style.SUCCESS('Datos iniciales cargados correctamente.'))
