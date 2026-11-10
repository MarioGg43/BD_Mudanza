"""Deja lista una mudanza para mostrar el control de materiales en la defensa.

    docker exec mudanzas_web python manage.py preparar_demo_materiales
    docker exec mudanzas_web python manage.py preparar_demo_materiales --hora 16:00 --sin-alerta

Crea un pedido de la clienta de prueba (María Gómez) para HOY, con Mudanza local + Embalaje, lo asigna
a la chofer Luciana Fernández y lo confirma. Así, entrando como la chofer (DNI 40987654), aparece
«Empezamos» y se puede mostrar en vivo:

1. Al tocar «Empezamos», bajan del stock las mantas, el film, la cinta, las cajas y el papel burbuja.
2. Si no se pasó --sin-alerta, el papel burbuja queda justo arriba de su mínimo (con un Ajuste
   registrado), así que al salir con la mudanza baja del mínimo y salta la regla 5 (campanita del
   administrador y correo a la empresa).
3. Al tocar «Terminamos», se cuentan los materiales: lo que se gastó, lo que sobró y lo que no volvió.

Hay que correrlo el mismo día de la defensa: «Empezamos» solo se puede tocar el día de la mudanza.
"""
from datetime import datetime, time, timedelta
from unittest import mock

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from pedidos import materiales, reglas
from usuarios.models import Material, Objeto, Servicio, Usuario

CLIENTA, CHOFER = 29876543, 40987654


class Command(BaseCommand):
    help = 'Crea una mudanza confirmada para hoy, lista para mostrar el control de materiales.'

    def add_arguments(self, parser):
        parser.add_argument('--hora', help='Hora de inicio, HH:MM (por defecto, la próxima hora en punto).')
        parser.add_argument('--sin-alerta', action='store_true',
                            help='No acercar el papel burbuja a su mínimo (no salta la alerta de stock bajo).')

    def handle(self, *args, **opciones):
        ahora = timezone.localtime()
        if opciones['hora']:
            try:
                hora = datetime.strptime(opciones['hora'], '%H:%M').time()
            except ValueError as e:
                raise CommandError('La hora va como HH:MM, por ejemplo 16:00.') from e
        else:
            hora = time((ahora + timedelta(hours=1)).hour, 0)
        hoy = ahora.date()
        clienta = Usuario.objects.get(DNI=CLIENTA)
        chofer = Usuario.objects.get(DNI=CHOFER)
        local = Servicio.objects.get(Tipo_servicio='Mudanza local')
        embalaje = Servicio.objects.get(Tipo_servicio='Embalaje')

        libres = reglas.vehiculos_libres(reglas.inicio_de(hoy, hora), local.Duracion_horas)
        vehiculo = libres.order_by('patente').first()
        if vehiculo is None:
            raise CommandError('No hay ningún vehículo libre en ese horario. Probá con otra --hora.')
        items = [{'objeto': Objeto.objects.get(nom_objeto=n), 'cantidad': c, 'fragil': f}
                 for n, c, f in (('Heladera', 1, True), ('Cajas', 15, False), ('Sillas', 6, False))]
        try:
            pedido = reglas.registrar_pedido(clienta, hoy, hora, 'Caseros 800, Salta', 'Av. Bolivia 5150, Salta',
                                             local.id_servicio, vehiculo.patente, items,
                                             ids_adicionales=[embalaje.id_servicio])
            reglas.asignar_personal(pedido.pk, chofer.pk)
            # la clienta de prueba tiene un correo inventado (@ejemplo.com): la notificación de
            # «mudanza confirmada» queda en su bandeja, pero no se manda el correo
            with mock.patch('notificaciones.reglas._mandar_correo'):
                reglas.confirmar(pedido.pk)
        except reglas.ErrorPedido as e:
            raise CommandError(' '.join(e.errores.values()) if e.errores else str(e)) from e

        if not opciones['sin_alerta']:
            papel = Material.objects.get(nom_material='Papel burbuja')
            objetivo = papel.stock_min_material + 1  # al salir 2 rollos con el Embalaje, queda debajo del mínimo
            if papel.stock_material != objetivo:
                materiales.registrar_ajuste(papel, objetivo - papel.stock_material, None,
                                            'Preparación de la demostración del control de materiales')
            self.stdout.write(f'Papel burbuja: {objetivo} rollos (mínimo {papel.stock_min_material}). '
                              'Al tocar «Empezamos» baja del mínimo y salta la alerta.')

        desde = timezone.localtime(pedido.inicio - timedelta(hours=reglas.HORAS_ANTES_DE_EMPEZAR))
        self.stdout.write(self.style.SUCCESS(
            f'Pedido N° {pedido.pk} confirmado para hoy a las {hora:%H:%M} con {vehiculo.patente}. '
            f'La chofer (DNI {CHOFER}) puede tocar «Empezamos» desde las {desde:%H:%M}.'))
        sugeridos = ', '.join(f'{m.nom_material} ×{c}' for m, c in materiales.sugeridos(pedido).items())
        self.stdout.write(f'Materiales que van a salir: {sugeridos}.')
