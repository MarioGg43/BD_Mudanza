"""Datos de prueba para la analítica y los reportes del Parcial N° 2.

Carga clientes de prueba y unos 320 pedidos YA PASADOS (de enero de 2026 a ayer), finalizados o
anulados, con su personal, sus horas reales de «Empezamos» / «Terminamos», reprogramaciones,
recargos e inventario. Así los gráficos y los reportes tienen con qué trabajar.

- Todo es del pasado: no ocupa vehículos ni personal en fechas que se puedan pedir.
- Los clientes de prueba tienen el correo @demo.mudanzassalta.com.ar: así se reconocen y se borran.
- Es reproducible: con la misma semilla salen siempre los mismos datos.
- Los pedidos reales no se tocan.

Uso:
    python manage.py cargar_datos_demo              # carga (si ya hay datos de prueba, no hace nada)
    python manage.py cargar_datos_demo --borrar     # borra solo los datos de prueba
    python manage.py cargar_datos_demo --reemplazar # borra los de prueba y los vuelve a cargar
"""
import random
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models.signals import post_delete
from django.utils import timezone

from pedidos import reglas
from usuarios import auditoria
from usuarios.models import (DetallePedido, InventarioDetalle, Objeto, Pedido, PersonalPedido, Reprogramacion, Rol,
                             Servicio, Usuario, Vehiculo)
from usuarios.utils import hash_password

DOMINIO = '@demo.mudanzassalta.com.ar'
DNI_DESDE = 90000001
CLAVE = 'Demo2026!'
DESDE = date(2026, 1, 5)

NOMBRES = ['Ana', 'Bruno', 'Carla', 'Daniel', 'Elena', 'Federico', 'Gabriela', 'Hernán', 'Inés', 'Javier',
           'Karina', 'Leandro', 'Mónica', 'Nahuel', 'Olga', 'Pablo', 'Romina', 'Sergio', 'Tamara', 'Ulises',
           'Valentina', 'Walter', 'Ximena', 'Yamil', 'Zulema', 'Agustín', 'Belén', 'Cristian']
APELLIDOS = ['Aguilar', 'Barrios', 'Cáceres', 'Delgado', 'Escobar', 'Figueroa', 'Guzmán', 'Ibarra', 'Juárez',
             'Ledesma', 'Maidana', 'Núñez', 'Ortiz', 'Paz', 'Ríos', 'Sosa', 'Tolaba', 'Vargas', 'Zerpa', 'Arias',
             'Bustos', 'Cruz', 'Chávez', 'Mamaní', 'Choque', 'Flores', 'Lamas', 'Medina']
CALLES = ['Av. Belgrano', 'Av. San Martín', 'Caseros', 'Alvarado', 'Zuviría', 'Mitre', 'Balcarce', 'Av. Bolivia',
          'Av. Tavella', 'Av. Paraguay', 'Pellegrini', 'Santiago del Estero', 'Av. Entre Ríos', 'Lerma', 'Córdoba']
LOCALIDADES = ['Salta'] * 8 + ['Cerrillos', 'Vaqueros', 'San Lorenzo', 'La Caldera', 'Rosario de Lerma']
DESTINOS_LEJOS = ['San Salvador de Jujuy', 'San Miguel de Tucumán', 'Córdoba', 'Santiago del Estero',
                  'Rosario', 'Buenos Aires']
MOTIVOS_ANULACION = ['El cliente desistió de la mudanza', 'Consiguió otra fecha de entrega del inmueble',
                     'Cambio de presupuesto', 'Problema con el vehículo', 'Duplicado']
MOTIVOS_RECARGO = ['Objetos de más no declarados', 'Escaleras sin ascensor', 'Espera en destino']
# cuántas mudanzas hay en cada mes (enero y febrero, temporada alta; invierno, baja)
PESO_MES = {1: 1.5, 2: 1.4, 3: 1.2, 4: 0.9, 5: 0.8, 6: 0.7, 7: 0.9, 8: 0.8, 9: 0.9, 10: 1.0, 11: 1.1, 12: 1.4}
PESO_DIA = [0.9, 0.8, 0.8, 0.9, 1.2, 1.6, 0.3]          # lunes a domingo: el sábado es el día fuerte
HORAS = [(7, 3), (8, 6), (9, 5), (10, 3), (11, 1), (13, 1), (14, 2), (15, 1), (16, 1), (5, 1), (6, 1)]


def _es_demo(qs):
    return qs.filter(Correo__endswith=DOMINIO)


class Command(BaseCommand):
    help = 'Carga (o borra) pedidos de prueba del pasado para la analítica y los reportes del Parcial N° 2.'

    def add_arguments(self, parser):
        parser.add_argument('--borrar', action='store_true', help='Borra solo los datos de prueba.')
        parser.add_argument('--reemplazar', action='store_true', help='Borra los de prueba y los vuelve a cargar.')
        parser.add_argument('--cantidad', type=int, default=320, help='Cuántos pedidos cargar (por defecto 320).')
        parser.add_argument('--semilla', type=int, default=2026, help='Semilla: la misma da los mismos datos.')

    def handle(self, *args, **o):
        if o['borrar'] or o['reemplazar']:
            self.borrar()
            if o['borrar']:
                return
        if _es_demo(Usuario.objects).exists():
            raise CommandError('Ya hay datos de prueba cargados. Usá --reemplazar para cargarlos de nuevo.')
        self.cargar(o['cantidad'], random.Random(o['semilla']))

    # ------------------------------------------------------------------ borrar
    def borrar(self):
        clientes = _es_demo(Usuario.objects)
        # borrar datos de prueba no es una operación de la empresa: no va a la auditoría
        post_delete.disconnect(dispatch_uid='auditoria_post_delete')
        try:
            with transaction.atomic():
                n, _ = Pedido.objects.filter(idUsuario__in=clientes).delete()
                c = clientes.count()
                clientes.delete()
        finally:
            auditoria.conectar()
        self.stdout.write(self.style.SUCCESS(f'Borrados {c} clientes de prueba y sus pedidos ({n} registros en total).'))

    # ------------------------------------------------------------------ cargar
    @transaction.atomic
    def cargar(self, cantidad, rnd):
        rol_cliente = Rol.objects.get(nom_rol='Cliente')
        choferes = list(Usuario.objects.filter(Activo=True, idRol__nom_rol=reglas.ROL_CHOFER))
        ayudantes = list(Usuario.objects.filter(Activo=True, idRol__nom_rol=reglas.ROL_AYUDANTE))
        admin = Usuario.objects.filter(Activo=True, idRol__nom_rol='Administrador').first()
        vehiculos = list(Vehiculo.objects.exclude(estado='Fuera de Servicio'))
        principales = {s.Tipo_servicio: s for s in Servicio.objects.filter(Categoria=Servicio.PRINCIPAL, Activo=True)}
        adicionales = list(Servicio.objects.filter(Categoria=Servicio.ADICIONAL, Activo=True))
        objetos = list(Objeto.objects.filter(Activo=True).exclude(nom_objeto=Objeto.OTRO))
        if not (choferes and vehiculos and principales and objetos and admin):
            raise CommandError('Faltan datos básicos (choferes, vehículos, servicios u objetos). Corré init_data.')

        clientes = self._clientes(rol_cliente, rnd)
        # cada chofer tiene su ritmo: unos tardan más que otros (lo muestra el reporte de desempeño)
        ritmo = {c.pk: rnd.uniform(0.92, 1.18) for c in choferes}
        frecuentes = clientes[:6]  # algunos clientes piden varias veces (ranking y heatmap más reales)

        dias = self._dias(cantidad, rnd)
        pedidos, detalles, personal, inventario, reprogs = [], [], [], [], []
        for n, dia in enumerate(dias):
            tipo = rnd.choices(list(principales), weights=[self._peso_servicio(t) for t in principales])[0]
            principal = principales[tipo]
            vehiculo = self._vehiculo(tipo, vehiculos, rnd)
            hora = time(rnd.choices([h for h, _ in HORAS], weights=[p for _, p in HORAS])[0], rnd.choice([0, 0, 30]))
            cliente = rnd.choice(frecuentes) if rnd.random() < 0.35 else rnd.choice(clientes)
            origen = f'{rnd.choice(CALLES)} {rnd.randint(100, 2900)}, Salta'
            lejos = 'nacional' in tipo.lower()
            destino = (f'{rnd.choice(CALLES)} {rnd.randint(100, 2900)}, '
                       + (rnd.choice(DESTINOS_LEJOS) if lejos else rnd.choice(LOCALIDADES)))
            extras = [s for s in adicionales if rnd.random() < 0.35]
            precio = reglas.precio_principal(principal, vehiculo)
            recargo = Decimal(rnd.choice([10000, 15000, 25000, 40000])) if rnd.random() < 0.1 else Decimal(0)
            total = precio + sum((s.Precio_base for s in extras), Decimal(0)) + recargo
            horas = principal.Duracion_horas or reglas.MIN_HORAS
            inicio = timezone.make_aware(datetime.combine(dia, hora))
            anulado = rnd.random() < 0.12
            chofer = rnd.choice(choferes)

            p = Pedido(patente_vehiculo=vehiculo, idUsuario=cliente, fecha_servicio=dia, hora_servicio=hora,
                       Fecha_pedido=dia - timedelta(days=rnd.randint(3, 30)), duracion_horas=horas,
                       origen=origen, destino=destino, total=total, recargo=recargo,
                       motivo_recargo=rnd.choice(MOTIVOS_RECARGO) if recargo else None)
            if anulado:
                p.estado = Pedido.ANULADO
                p.fecha_anulacion = inicio - timedelta(days=rnd.randint(1, 6), hours=rnd.randint(0, 12))
                p.motivo_anulacion = rnd.choice(MOTIVOS_ANULACION)
                p.usuario_anulacion = cliente if rnd.random() < 0.6 else admin
            else:
                p.estado = Pedido.FINALIZADO
                demora = max(-10, rnd.gauss(12, 15))                           # minutos tarde al empezar
                p.inicio_real = inicio + timedelta(minutes=demora)
                p.fin_real = p.inicio_real + timedelta(hours=horas * ritmo[chofer.pk] * rnd.gauss(1.0, 0.08))
            pedidos.append(p)
            detalles.append([(principal, precio)] + [(s, s.Precio_base) for s in extras])
            equipo = [(chofer, PersonalPedido.CHOFER)]
            if ayudantes and 'flete' not in tipo.lower():
                for a in rnd.sample(ayudantes, k=min(len(ayudantes), rnd.choice([1, 2, 2, 3]))):
                    equipo.append((a, PersonalPedido.AYUDANTE))
            personal.append(equipo)
            inventario.append([(o, rnd.randint(1, 4) if o.nom_objeto != 'Cajas' else rnd.randint(5, 40))
                               for o in rnd.sample(objetos, k=rnd.randint(2, 6))])
            reprogs.append(rnd.random() < 0.13)

        # uno por uno: en MySQL bulk_create no devuelve los id, y los detalles los necesitan.
        # Las altas no van a la auditoría (registra modificaciones, anulaciones y bajas).
        for p in pedidos:
            p.save()
        DetallePedido.objects.bulk_create([DetallePedido(idPedido=p, idServicio=s, precio_unitario=v, subtotal=v)
                                           for p, ds in zip(pedidos, detalles) for s, v in ds])
        PersonalPedido.objects.bulk_create([PersonalPedido(idPedido=p, idUsuario=u, Funcion=f)
                                            for p, eq in zip(pedidos, personal) for u, f in eq])
        InventarioDetalle.objects.bulk_create([InventarioDetalle(idPedido=p, idObjeto=o, Cantidad=c,
                                                                 Fragil=o.nom_objeto in ('Heladera', 'Televisor', 'Microondas'))
                                               for p, items in zip(pedidos, inventario) for o, c in items])
        motivos = [m for m, _ in Reprogramacion.MOTIVOS if m != 'Otro']
        Reprogramacion.objects.bulk_create([
            Reprogramacion(idPedido=p, fecha_anterior=p.fecha_servicio - timedelta(days=rnd.randint(1, 7)),
                           hora_anterior=p.hora_servicio, vehiculo_anterior=p.patente_vehiculo,
                           fecha_nueva=p.fecha_servicio, hora_nueva=p.hora_servicio, vehiculo_nuevo=p.patente_vehiculo,
                           motivo=rnd.choices(motivos, weights=[2, 2, 3, 4, 1])[0], usuario=admin, visto_cliente=True,
                           fecha_registro=timezone.make_aware(datetime.combine(p.fecha_servicio, time(9)))
                           - timedelta(days=rnd.randint(8, 12)))
            for p, si in zip(pedidos, reprogs) if si])
        anulados = sum(p.estado == Pedido.ANULADO for p in pedidos)
        self.stdout.write(self.style.SUCCESS(
            f'Cargados {len(clientes)} clientes de prueba y {len(pedidos)} pedidos del '
            f'{dias[0]:%d/%m/%Y} al {dias[-1]:%d/%m/%Y} ({len(pedidos) - anulados} finalizados, {anulados} anulados, '
            f'{sum(reprogs)} reprogramados). Clave de los clientes de prueba: {CLAVE}'))

    def _clientes(self, rol, rnd):
        clave = hash_password(CLAVE)
        usados = set()
        clientes = []
        for i in range(28):
            nom, ape = NOMBRES[i], rnd.choice(APELLIDOS)
            usuario = f'{ape.lower()}{nom[0].lower()}.demo'
            while usuario in usados:
                usuario = usuario.replace('.demo', '1.demo')
            usados.add(usuario)
            clientes.append(Usuario(DNI=DNI_DESDE + i, Nombre=nom, Apellido=ape, NombreUsuario=usuario,
                                    Correo=f'{nom.lower()}.{ape.lower()}{i}{DOMINIO}'.replace('á', 'a').replace(
                                        'é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u'),
                                    Telefono=f'387{rnd.randint(4000000, 5999999)}', Clave=clave,
                                    Activo=True, DebeCambiarClave=False, idRol=rol))
        for c in clientes:
            c.save()
        return clientes

    def _dias(self, cantidad, rnd):
        """Días de mudanza del pasado, con más mudanzas en verano y los sábados."""
        ayer = timezone.localdate() - timedelta(days=1)
        todos = [DESDE + timedelta(days=d) for d in range((ayer - DESDE).days + 1)]
        pesos = [PESO_MES[d.month] * PESO_DIA[d.weekday()] for d in todos]
        return sorted(rnd.choices(todos, weights=pesos, k=cantidad))

    @staticmethod
    def _peso_servicio(tipo):
        t = tipo.lower()
        return 1 if 'nacional' in t else 4 if 'local' in t else 4

    @staticmethod
    def _vehiculo(tipo, vehiculos, rnd):
        """Los fletes van en camiones chicos; las nacionales, en los grandes."""
        t = tipo.lower()
        preferidos = [v for v in vehiculos if (v.tipo_vehiculo == Vehiculo.CHICO) == ('flete' in t)]
        if 'nacional' in t:
            preferidos = [v for v in vehiculos if v.tipo_vehiculo != Vehiculo.CHICO] or preferidos
        return rnd.choice(preferidos or vehiculos)
