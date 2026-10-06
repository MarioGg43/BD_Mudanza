from decimal import Decimal

from django import forms
from django.db import transaction

from usuarios.models import Pedido, RecursoAsignado, Rol, Servicio, Usuario, Vehiculo
from usuarios.utils import hash_password, nombre_usuario_libre, validate_strong_password


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


class AnularForm(forms.Form):
    motivo = forms.CharField(min_length=5, max_length=200, label='Motivo de la anulación',
                             widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}))


class RegistroClienteForm(forms.Form):
    dni = forms.IntegerField(label='DNI', min_value=1000000, max_value=99999999)
    apellido = forms.CharField(max_length=100, label='Apellido')
    nombre = forms.CharField(max_length=100, label='Nombre')
    correo = forms.EmailField(max_length=150, label='Correo')
    telefono = forms.CharField(max_length=30, required=False, label='Teléfono')
    clave = forms.CharField(label='Clave', widget=forms.PasswordInput,
                            help_text='8 o más caracteres, con mayúscula, minúscula, número y un caracter especial.')
    clave2 = forms.CharField(label='Repetir clave', widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        con_bootstrap(self)

    def clean_dni(self):
        dni = self.cleaned_data['dni']
        if Usuario.objects.filter(DNI=dni).exists():
            raise forms.ValidationError('Ya hay una cuenta con ese DNI.')
        return dni

    def clean_correo(self):
        correo = self.cleaned_data['correo'].strip().lower()
        if Usuario.objects.filter(Correo=correo).exists():
            raise forms.ValidationError('Ese correo ya está en uso.')
        return correo

    def clean_clave(self):
        valida, mensaje = validate_strong_password(self.cleaned_data['clave'])
        if not valida:
            raise forms.ValidationError(mensaje)
        return self.cleaned_data['clave']

    def clean(self):
        datos = super().clean()
        if datos.get('clave') and datos.get('clave2') and datos['clave'] != datos['clave2']:
            self.add_error('clave2', 'Las claves no coinciden.')
        return datos

    def crear_cliente(self):
        d = self.cleaned_data
        return Usuario.objects.create(
            DNI=d['dni'], Apellido=d['apellido'].strip(), Nombre=d['nombre'].strip(), Correo=d['correo'],
            Telefono=d['telefono'] or None,
            NombreUsuario=nombre_usuario_libre(d['apellido'], d['nombre']),
            Clave=hash_password(d['clave']), Activo=True,
            DebeCambiarClave=False,  # la clave la eligió el cliente
            idRol=Rol.objects.get(nom_rol='Cliente'))


class ServicioForm(forms.ModelForm):
    materiales = forms.CharField(required=False, label='Materiales que incluye',
                                 help_text='Separados por coma. Ej.: Mantas, film, cintas')

    class Meta:
        model = Servicio
        fields = ['Tipo_servicio', 'Precio_base', 'Activo']
        labels = {'Tipo_servicio': 'Tipo de servicio', 'Precio_base': 'Precio base ($)'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['materiales'].initial = ', '.join(
                self.instance.recursos.values_list('Materiales', flat=True))
        con_bootstrap(self)
        self.fields['Activo'].widget.attrs['class'] = 'form-check-input'

    def clean_Precio_base(self):
        precio = self.cleaned_data['Precio_base']
        if precio <= 0:
            raise forms.ValidationError('El precio tiene que ser mayor a 0.')
        return precio

    def clean_materiales(self):
        lista = [m.strip() for m in self.cleaned_data['materiales'].split(',') if m.strip()]
        largos = [m for m in lista if len(m) > 50]
        if largos:
            raise forms.ValidationError(f'«{largos[0][:20]}…» supera los 50 caracteres.')
        return lista

    def save(self, commit=True):
        with transaction.atomic():
            servicio = super().save()
            servicio.recursos.all().delete()  # los materiales se reemplazan; el servicio no se borra
            RecursoAsignado.objects.bulk_create(
                [RecursoAsignado(idServicio=servicio, Materiales=m) for m in self.cleaned_data['materiales']])
        return servicio
