from django import forms

from .models import Vehiculo


class VehiculoForm(forms.ModelForm):
    class Meta:
        model = Vehiculo
        fields = [
            'patente', 'marca_modelo', 'tipo_vehiculo',
            'capacidad_kg', 'capacidad_m3', 'estado',
            'kilometraje', 'anio', 'observaciones',
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
            'observaciones': 'Observaciones',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Asignación automática de clases CSS de Bootstrap según el tipo de widget
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': 'form-select'})
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'class': 'form-control', 'rows': 3})
            else:
                field.widget.attrs.update({'class': 'form-control'})
