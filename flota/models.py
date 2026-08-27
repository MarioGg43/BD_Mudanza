from django.db import models


class Vehiculo(models.Model):
    ESTADO_CHOICES = [
        ('Disponible', 'Disponible'),
        ('En Viaje', 'En Viaje'),
        ('En Mantenimiento', 'En Mantenimiento'),
        ('Fuera de Servicio', 'Fuera de Servicio'),
    ]

    id_vehiculo = models.AutoField(primary_key=True)
    patente = models.CharField(max_length=15, unique=True)
    marca_modelo = models.CharField(max_length=100)
    tipo_vehiculo = models.CharField(max_length=50)
    capacidad_kg = models.DecimalField(max_digits=10, decimal_places=2)
    capacidad_m3 = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(max_length=30, choices=ESTADO_CHOICES, default='Disponible')
    kilometraje = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    anio = models.IntegerField(null=True, blank=True)
    observaciones = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Vehículo"
        verbose_name_plural = "Vehículos"

    def __str__(self):
        return f"{self.patente} - {self.marca_modelo}"
