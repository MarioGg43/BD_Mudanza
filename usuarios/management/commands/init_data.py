from datetime import date, time

from django.core.management.base import BaseCommand

from usuarios.models import (
    Rol, Permiso, PermisoRol, Usuario, Vehiculo, Sueldo, Servicio,
    RecursoAsignado, Pedido, DetallePedido, InventarioDetalle, Objeto,
    Cobranza, DetalleCobranza,
)
from usuarios.permisos import CATALOGO, PERMISOS_INICIALES
from usuarios.utils import hash_password, generate_username


class Command(BaseCommand):
    help = 'Carga los roles, permisos, usuarios, vehículos y datos de ejemplo del DER'

    def handle(self, *args, **options):
        # 1. Permisos del catálogo (la descripción se mantiene al día)
        for _, codigo, descripcion in CATALOGO:
            p, creado = Permiso.objects.get_or_create(nom_permiso=codigo, defaults={'desc_permiso': descripcion})
            if not creado and p.desc_permiso != descripcion:
                p.desc_permiso = descripcion
                p.save(update_fields=['desc_permiso'])

        # 2. Roles: los permisos iniciales se cargan solo al crear el rol, para no pisar
        #    lo que se edite después desde la pantalla de roles.
        descripciones_rol = {
            'Administrador': 'Acceso total a la administración de seguridad y usuarios',
            'Chofer': 'Conducción de vehículos y visualización de rutas de mudanza',
            'Ayudante de Carga': 'Personal operativo de carga, descarga y embalaje de bultos',
            'Cliente': 'Cliente que registra y sigue sus pedidos de mudanza',
        }
        roles = {}
        for nombre, descripcion in descripciones_rol.items():
            rol, creado = Rol.objects.get_or_create(nom_rol=nombre, defaults={'desc_rol': descripcion})
            if creado:
                for p in Permiso.objects.filter(nom_permiso__in=PERMISOS_INICIALES[nombre]):
                    PermisoRol.objects.create(idRol=rol, idPermiso=p)
            roles[nombre] = rol
        r_admin, r_chofer = roles['Administrador'], roles['Chofer']
        r_ayudante, r_cliente = roles['Ayudante de Carga'], roles['Cliente']

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
            (29876543, 'Gómez', 'María', 'maria.gomez@ejemplo.com',
             '3874112233', 'Cliente123!', False, r_cliente, None),
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
            ('AE-123-CD', 'Mercedes-Benz Accelo 815', 'Camión Grande', 5000.0, 32.0,
             'Disponible', 45200.0, 2022, chofer, 'Equipado con rampa hidráulica y mantas de protección.'),
            ('AF-456-EF', 'Ford Transit Chasis', 'Camión Mediano', 2200.0, 18.0,
             'En Viaje', 28100.0, 2023, None, 'Asignado a servicio interurbano Salta - Cafayate.'),
            ('AC-789-GH', 'Iveco Daily 70C17', 'Camión Mediano', 3500.0, 24.0,
             'En Mantenimiento', 89300.0, 2020, None, 'Service programado de frenos y amortiguadores.'),
            ('AD-321-JK', 'Renault Master Furgón', 'Camión Chico', 1600.0, 12.0,
             'Disponible', 34500.0, 2021, None, 'Ideal para fletes rápidos en microcentro.'),
        ]
        for pat, marca, tipo, kg, m3, est, km, anio, ch, obs in vehiculos_data:
            if not Vehiculo.objects.filter(patente=pat).exists():
                Vehiculo.objects.create(
                    patente=pat, marca_modelo=marca, tipo_vehiculo=tipo,
                    capacidad_kg=kg, capacidad_m3=m3, estado=est, kilometraje=km,
                    anio=anio, chofer_asignado=ch, observaciones=obs)
                self.stdout.write(self.style.SUCCESS(f'Vehículo {pat} ({marca}) creado.'))

        # 6. Servicios y sus materiales: los principales (uno por pedido) y los adicionales
        P, A = Servicio.PRINCIPAL, Servicio.ADICIONAL
        servicios_data = [
            ('Mudanza local', P, 185000, 10, 'Mantas, film y cintas'),
            ('Mudanza nacional', P, 640000, 48, 'Mantas, film, cintas y zunchos'),
            ('Flete urbano', P, 75000, 5, 'Correas y mantas'),
            ('Embalaje', A, 25000, None, 'Cajas, papel burbuja y cinta'),
            ('Desarmado y armado de muebles', A, 35000, None, 'Herramientas'),
            ('Ayudante extra', A, 20000, None, None),
        ]
        for tipo, categoria, precio, horas, materiales in servicios_data:
            serv, creado = Servicio.objects.get_or_create(
                Tipo_servicio=tipo, defaults={'Precio_base': precio, 'Categoria': categoria, 'Duracion_horas': horas})
            if creado:
                if materiales:
                    RecursoAsignado.objects.create(idServicio=serv, Materiales=materiales)
                self.stdout.write(self.style.SUCCESS(f'Servicio "{tipo}" creado.'))

        # 7. Un pedido de ejemplo de la clienta, ya finalizado, con detalle, inventario y cobranza
        cliente = Usuario.objects.filter(DNI=29876543).first()
        vehiculo = Vehiculo.objects.filter(patente='AE-123-CD').first()
        if cliente and vehiculo and not Pedido.objects.exists():
            servicio = Servicio.objects.get(Tipo_servicio='Mudanza local')
            pedido = Pedido.objects.create(
                patente_vehiculo=vehiculo, idUsuario=cliente, Fecha_pedido=date(2026, 9, 15),
                fecha_servicio=date(2026, 9, 20), hora_servicio=time(9, 0), origen='Av. Belgrano 1250, Salta',
                destino='Los Ceibos 340, Cerrillos', estado=Pedido.FINALIZADO, duracion_horas=servicio.Duracion_horas,
                total=servicio.Precio_base)
            DetallePedido.objects.create(idPedido=pedido, idServicio=servicio,
                                         precio_unitario=servicio.Precio_base,
                                         subtotal=servicio.Precio_base)
            InventarioDetalle.objects.create(idPedido=pedido, idObjeto=Objeto.objects.get(nom_objeto='Cajas'),
                                             Cantidad=42, Fragil=True)
            cobranza = Cobranza.objects.create(Monto_cob=185000, Met_pag_cob='Transferencia')
            DetalleCobranza.objects.create(idPedido=pedido, idCobranza=cobranza)
            self.stdout.write(self.style.SUCCESS(
                'Pedido de ejemplo creado con detalle, inventario y cobranza.'))

        self.stdout.write(self.style.SUCCESS('Datos iniciales cargados correctamente.'))
