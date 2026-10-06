from decimal import Decimal

from django import forms

from usuarios.models import Pedido, Servicio, Usuario, Vehiculo


def con_bootstrap(form):
    """Las mismas clases que usa el CRUD de vehículos."""
    for field in form.fields.values():
        w = field.widget
        if isinstance(w, (forms.CheckboxInput, forms.CheckboxSelectMultiple)):
            continue
        w.attrs.setdefault('class', 'form-select' if isinstance(w, forms.Select) else 'form-control')


class FiltroPedidosForm(forms.Form):
    desde = forms.DateField(required=False, label='Desde',
                            widget=forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'))
    hasta = forms.DateField(required=False, label='Hasta',
                            widget=forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'))
    estado = forms.ChoiceField(required=False, label='Estado',
                               choices=[('', 'Todos')] + Pedido.ESTADOS)
    servicio = forms.ModelChoiceField(required=False, label='Servicio', empty_label='Todos',
                                      queryset=Servicio.objects.order_by('Tipo_servicio'))
    cliente = forms.ModelChoiceField(required=False, label='Cliente', empty_label='Todos',
                                     queryset=Usuario.objects.filter(idRol__nom_rol='Cliente')
                                                             .order_by('Apellido', 'Nombre'))

    def __init__(self, *args, ve_todos=False, **kwargs):
        super().__init__(*args, **kwargs)
        if not ve_todos:
            del self.fields['cliente']
        con_bootstrap(self)

    def filtros(self):
        d = self.cleaned_data
        return {'desde': d.get('desde'), 'hasta': d.get('hasta'), 'estado': d.get('estado') or None,
                'id_servicio': d['servicio'].id_servicio if d.get('servicio') else None,
                'id_cliente': d['cliente'].id_usuario if d.get('cliente') else None}


class VehiculoField(forms.ModelChoiceField):
    def label_from_instance(self, v):
        return f'{v.patente} · {v.tipo_vehiculo} · hasta {v.capacidad_kg:.0f} kg'


class PedidoForm(forms.Form):
    """Solo convierte tipos; las reglas (fechas, capacidad, disponibilidad) están en reglas.py."""
    fecha_servicio = forms.DateField(label='Fecha de la mudanza',
                                     widget=forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'))
    origen = forms.CharField(max_length=200, label='Desde', widget=forms.TextInput(
        attrs={'placeholder': 'Calle, número y ciudad'}))
    destino = forms.CharField(max_length=200, label='Hasta', widget=forms.TextInput(
        attrs={'placeholder': 'Calle, número y ciudad'}))
    servicios = forms.ModelMultipleChoiceField(queryset=Servicio.objects.none(), label='Servicios',
                                               widget=forms.CheckboxSelectMultiple)
    vehiculo = VehiculoField(queryset=Vehiculo.objects.none(), label='Vehículo',
                             empty_label='Elegí primero la fecha')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['servicios'].queryset = Servicio.objects.filter(Activo=True).order_by('Tipo_servicio')
        self.fields['vehiculo'].queryset = Vehiculo.objects.filter(estado='Disponible').order_by('patente')
        con_bootstrap(self)


class ItemInventarioForm(forms.Form):
    descripcion = forms.CharField(max_length=100, label='Qué es')
    cantidad = forms.IntegerField(min_value=1, max_value=999, label='Cantidad')
    peso = forms.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.01'),
                              max_value=Decimal('5000'), label='Peso c/u (kg)')
    fragil = forms.BooleanField(required=False, label='Frágil')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        con_bootstrap(self)


InventarioFormSet = forms.formset_factory(ItemInventarioForm, extra=0, min_num=1,
                                          validate_min=True, max_num=50, validate_max=True)
