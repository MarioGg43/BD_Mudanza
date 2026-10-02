from django import forms

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
            'chofer_asignado': 'Chofer Asignado',
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

    def clean_patente(self):
        # Se guarda siempre en mayúsculas y sin espacios, como en el Hito 2
        return self.cleaned_data['patente'].strip().upper().replace(' ', '')
