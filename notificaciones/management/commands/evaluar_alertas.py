"""Tarea programada del Parcial N° 2 (M3): evalúa las reglas 1 y 2 (pedidos sin confirmar cerca
de la fecha y mudanzas atrasadas). La corre cada 15 minutos el contenedor «alertas» de
docker-compose; también se puede correr a mano: python manage.py evaluar_alertas
Correrla dos veces no duplica nada: cada notificación tiene una clave única."""
from django.core.management.base import BaseCommand
from django.utils import timezone

from notificaciones.reglas import evaluar_programadas


class Command(BaseCommand):
    help = 'Evalúa las reglas de notificación programadas (pedidos sin confirmar y mudanzas atrasadas).'

    def handle(self, *args, **options):
        nuevas = evaluar_programadas()
        detalle = ', '.join(f'{regla}: {n}' for regla, n in nuevas.items())
        self.stdout.write(f'[{timezone.localtime():%d/%m/%Y %H:%M}] Alertas evaluadas. Nuevas -> {detalle}')
