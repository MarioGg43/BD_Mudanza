from django.contrib import admin

from .models import Vehiculo


@admin.register(Vehiculo)
class VehiculoAdmin(admin.ModelAdmin):
    list_display = ('id_vehiculo', 'patente', 'marca_modelo', 'tipo_vehiculo', 'estado', 'kilometraje')
    list_filter = ('estado', 'tipo_vehiculo')
    search_fields = ('patente', 'marca_modelo')
