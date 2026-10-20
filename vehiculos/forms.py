from django import forms
from django.utils import timezone

from pedidos.reglas import tiene_pedidos_activos
from usuarios.models import Usuario, Vehiculo


class VehiculoForm(forms.ModelForm):
    class Meta:
        model = Vehiculo
        fields = [
            'patente', 'marca_modelo', 'tipo_vehiculo',
            'capacidad_kg', 'capacidad_m3', 'estado',
            'kilometraje', 'anio', 'chofer_asignado', 'observaciones',
        ]
        labels = {
            'patente': 'Patente',
            'marca_modelo': 'Marca y Modelo',
            'tipo_vehiculo': 'Tipo de Vehículo',
            'capacidad_kg': 'Capacidad Máxima (kg)',
            'capacidad_m3': 'Capacidad Máxima (m³)',
            'estado': 'Estado',
            'kilometraje': 'Kilometraje',
            'anio': 'Año',
            'chofer_asignado': 'Chofer habitual',
            'observaciones': 'Observaciones',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # La patente es la clave primaria: si se cambiara al editar, Django
        # insertaría un vehículo nuevo en vez de modificar el existente.
        if self.instance.pk:
            self.fields['patente'].disabled = True
        # Solo se puede asignar un chofer activo
        self.fields['chofer_asignado'].queryset = Usuario.objects.filter(
            idRol__nom_rol='Chofer', Activo=True).order_by('Apellido', 'Nombre')
        # Asignación automática de clases CSS de Bootstrap según el tipo de widget
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': 'form-select'})
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'class': 'form-control', 'rows': 3})
            else:
                field.widget.attrs.update({'class': 'form-control'})

    def clean(self):
        datos = super().clean()
        if (self.instance.pk and datos.get('estado') and datos['estado'] != 'Disponible'
                and tiene_pedidos_activos(patente_vehiculo=self.instance.pk)):
            self.add_error('estado', 'Tiene pedidos pendientes o confirmados: no puede dejar de estar disponible.')
        return datos

    # Rangos razonables para un vehículo de mudanzas: frenan errores de tipeo (un cero de más)
    RANGOS = {
        'capacidad_kg': (100, 40000, 'La capacidad va de 100 a 40.000 kg.'),
        'capacidad_m3': (1, 100, 'El volumen va de 1 a 100 m³.'),
        'kilometraje': (0, 2000000, 'El kilometraje va de 0 a 2.000.000 km.'),
    }

    def _en_rango(self, campo):
        valor = self.cleaned_data.get(campo)
        minimo, maximo, mensaje = self.RANGOS[campo]
        if valor is not None and not minimo <= valor <= maximo:
            raise forms.ValidationError(mensaje)
        return valor

    def clean_capacidad_kg(self):
        return self._en_rango('capacidad_kg')

    def clean_capacidad_m3(self):
        return self._en_rango('capacidad_m3')

    def clean_kilometraje(self):
        return self._en_rango('kilometraje')

    def clean_anio(self):
        anio = self.cleaned_data.get('anio')
        if anio is not None and not 1980 <= anio <= timezone.localdate().year + 1:
            raise forms.ValidationError(f'El año va de 1980 a {timezone.localdate().year + 1}.')
        return anio

    def clean_patente(self):
        # Se guarda siempre en mayúsculas y sin espacios, como en el Hito 2
        return self.cleaned_data['patente'].strip().upper().replace(' ', '')
