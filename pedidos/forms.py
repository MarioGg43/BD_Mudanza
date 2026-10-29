from django import forms
from django.db import transaction

from django.db.models import Case, IntegerField, Q, Value, When

from usuarios.models import Objeto, Pedido, RecursoAsignado, Reprogramacion, Rol, Servicio, Usuario, Vehiculo
from usuarios.utils import hash_password, nombre_usuario_libre, validate_strong_password
from . import reglas


def con_bootstrap(form):
    """Las mismas clases que usa el CRUD de vehículos."""
    for field in form.fields.values():
        w = field.widget
        if isinstance(w, (forms.CheckboxInput, forms.CheckboxSelectMultiple, forms.RadioSelect)):
            continue
        w.attrs.setdefault('class', 'form-select' if isinstance(w, forms.Select) else 'form-control')


class PatenteField(forms.ModelChoiceField):
    """En el filtro alcanza con la patente (la descripción larga no entra en la columna)."""
    def label_from_instance(self, v):
        return v.patente


class FiltroPedidosForm(forms.Form):
    desde = forms.DateField(required=False, label='Desde',
                            widget=forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'))
    hasta = forms.DateField(required=False, label='Hasta',
                            widget=forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'))
    estado = forms.ChoiceField(required=False, label='Estado',
                               choices=[('', 'Todos')] + Pedido.ESTADOS
                                       + [(reglas.ATRASADA, 'Atrasadas'), (reglas.VENCIDO, 'Vencidos'), (reglas.PARA_FINALIZAR, 'Para finalizar'),
                                          (reglas.POR_CONFIRMAR, 'Por confirmar'), (reglas.SIN_CHOFER, 'Sin chofer')])
    servicio = forms.ModelChoiceField(required=False, label='Servicio', empty_label='Todos',
                                      queryset=Servicio.objects.order_by('Tipo_servicio'))
    cliente = forms.ModelChoiceField(required=False, label='Cliente', empty_label='Todos',
                                     queryset=Usuario.objects.filter(idRol__nom_rol='Cliente')
                                                             .order_by('Apellido', 'Nombre'))
    vehiculo = PatenteField(required=False, label='Vehículo', empty_label='Todos',
                            queryset=Vehiculo.objects.order_by('patente'))

    def __init__(self, *args, ve_todos=False, **kwargs):
        super().__init__(*args, **kwargs)
        if not ve_todos:
            del self.fields['cliente']
            del self.fields['vehiculo']
        con_bootstrap(self)

    def clean(self):
        d = super().clean()
        if d.get('desde') and d.get('hasta') and d['desde'] > d['hasta']:
            self.add_error('hasta', 'La fecha «Hasta» no puede ser anterior a «Desde».')
        return d

    def filtros(self):
        d = self.cleaned_data
        return {'desde': d.get('desde'), 'hasta': d.get('hasta'), 'estado': d.get('estado') or None,
                'id_servicio': d['servicio'].id_servicio if d.get('servicio') else None,
                'id_cliente': d['cliente'].id_usuario if d.get('cliente') else None,
                'patente': d['vehiculo'].patente if d.get('vehiculo') else None}


class VehiculoField(forms.ModelChoiceField):
    def label_from_instance(self, v):
        return (f'{v.patente} · {v.tipo_vehiculo} · {v.marca_modelo} · '
                f'hasta {v.capacidad_kg:.0f} kg / {v.capacidad_m3:.0f} m³')


class PedidoForm(forms.Form):
    """Solo convierte tipos; las reglas (fecha, hora, disponibilidad) están en reglas.py."""
    fecha_servicio = forms.DateField(label='Fecha de la mudanza',
                                     widget=forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'))
    hora_servicio = forms.TimeField(label='Hora de inicio', widget=forms.TimeInput(
        attrs={'type': 'time', 'step': 900}, format='%H:%M'))
    origen = forms.CharField(max_length=200, label='Desde', widget=forms.TextInput(
        attrs={'placeholder': 'Calle, número y ciudad'}))
    destino = forms.CharField(max_length=200, label='Hasta', widget=forms.TextInput(
        attrs={'placeholder': 'Calle, número y ciudad'}))
    servicio = forms.ModelChoiceField(queryset=Servicio.objects.none(), label='Servicio',
                                      widget=forms.RadioSelect, empty_label=None)
    adicionales = forms.ModelMultipleChoiceField(queryset=Servicio.objects.none(), required=False,
                                                 label='Adicionales', widget=forms.CheckboxSelectMultiple)
    vehiculo = VehiculoField(queryset=Vehiculo.objects.none(), label='Vehículo',
                             empty_label='Elegí primero la fecha, la hora y el servicio')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        activos = Servicio.objects.filter(Activo=True).order_by('Tipo_servicio')
        self.fields['servicio'].queryset = activos.filter(Categoria=Servicio.PRINCIPAL)
        self.fields['adicionales'].queryset = activos.filter(Categoria=Servicio.ADICIONAL)
        self.fields['vehiculo'].queryset = Vehiculo.objects.filter(estado='Disponible').order_by('patente')
        con_bootstrap(self)


def objetos_para_elegir():
    """El catálogo activo en orden alfabético, con «Otro» al final."""
    return (Objeto.objects.filter(Activo=True)
            .annotate(al_final=Case(When(nom_objeto=Objeto.OTRO, then=Value(1)), default=Value(0),
                                    output_field=IntegerField()))
            .order_by('al_final', 'nom_objeto'))


class ItemInventarioForm(forms.Form):
    # Se elige del catálogo: no se escribe el nombre (ver reglas._validar_items)
    objeto = forms.ModelChoiceField(queryset=Objeto.objects.none(), label='Objeto', empty_label='Elegí un objeto')
    cantidad = forms.IntegerField(min_value=1, max_value=reglas.MAX_CANTIDAD, label='Cantidad')
    fragil = forms.BooleanField(required=False, label='Frágil')
    observacion = forms.CharField(max_length=reglas.MAX_OBSERVACION, required=False, label='Observación',
                                  widget=forms.TextInput(attrs={'placeholder': 'Ej.: se desarma, tiene vidrio'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['objeto'].queryset = objetos_para_elegir()
        con_bootstrap(self)


InventarioFormSet = forms.formset_factory(ItemInventarioForm, extra=0, min_num=1,
                                          validate_min=True, max_num=50, validate_max=True)


class ReprogramarForm(forms.Form):
    """Solo convierte tipos; lo que decide si el horario sirve está en reglas.reprogramar."""
    fecha_servicio = forms.DateField(label='Fecha nueva',
                                     widget=forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'))
    hora_servicio = forms.TimeField(label='Hora nueva', widget=forms.TimeInput(
        attrs={'type': 'time', 'step': 900}, format='%H:%M'))
    vehiculo = VehiculoField(queryset=Vehiculo.objects.none(), label='Vehículo', empty_label=None)
    motivo = forms.ChoiceField(choices=[('', 'Elegí el motivo')] + Reprogramacion.MOTIVOS, label='Motivo')
    observacion = forms.CharField(max_length=reglas.MAX_OBSERVACION, required=False, label='Observación',
                                  widget=forms.TextInput(attrs={'autocomplete': 'off',
                                                                'placeholder': 'Opcional; con «Otro», contá el motivo'}))
    quitar_ocupados = forms.BooleanField(required=False, label='Si alguien del personal no está libre en el '
                                                                'horario nuevo, sacarlo del pedido')

    def __init__(self, *args, pedido, **kwargs):
        super().__init__(*args, **kwargs)
        # los disponibles, más el que ya tiene (aunque ahora esté en mantenimiento)
        self.fields['vehiculo'].queryset = Vehiculo.objects.filter(
            Q(estado='Disponible') | Q(pk=pedido.patente_vehiculo_id)).order_by('patente')
        con_bootstrap(self)
        self.fields['quitar_ocupados'].widget.attrs['class'] = 'form-check-input'


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
        fields = ['Tipo_servicio', 'Categoria', 'Precio_base', 'Duracion_horas', 'Activo']
        labels = {'Tipo_servicio': 'Tipo de servicio', 'Precio_base': 'Precio base ($)'}
        help_texts = {'Categoria': 'El cliente elige un principal por pedido y, si quiere, le suma adicionales. '
                                   'El principal se cobra con un recargo según el camión (Mediano +25 %, '
                                   'Grande +50 %); los adicionales, a su precio.',
                      'Duracion_horas': f'Cuánto ocupa el vehículo y el personal: de {reglas.MIN_HORAS} horas '
                                        f'a {reglas.MAX_HORAS} (5 días). Un día de trabajo son unas 10.'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['materiales'].initial = ', '.join(
                self.instance.recursos.values_list('Materiales', flat=True))
        self.fields['Precio_base'].required = False  # en los adicionales puede quedar en 0
        self.fields['Duracion_horas'].widget.attrs.update(min=reglas.MIN_HORAS, max=reglas.MAX_HORAS)
        con_bootstrap(self)
        self.fields['Activo'].widget.attrs['class'] = 'form-check-input'

    def clean(self):
        d = super().clean()
        if d.get('Categoria') == Servicio.ADICIONAL:
            d['Precio_base'] = d.get('Precio_base') or 0  # sin precio = gratis
            d['Duracion_horas'] = None  # no suman tiempo: la duración es la del principal
            self.errors.pop('Duracion_horas', None)
            if d['Precio_base'] < 0:
                self.add_error('Precio_base', 'El precio no puede ser negativo.')
        elif d.get('Categoria') == Servicio.PRINCIPAL:
            if not (d.get('Precio_base') or 0) > 0:
                self.add_error('Precio_base', 'El precio tiene que ser mayor a 0.')
            horas = d.get('Duracion_horas')
            if horas is None:
                self.add_error('Duracion_horas', 'Indicá cuántas horas dura el servicio.')
            elif not reglas.MIN_HORAS <= horas <= reglas.MAX_HORAS:
                self.add_error('Duracion_horas', f'La duración tiene que ser de {reglas.MIN_HORAS} '
                                                 f'a {reglas.MAX_HORAS} horas.')
        return d

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


class ObjetoForm(forms.ModelForm):
    class Meta:
        model = Objeto
        fields = ['nom_objeto', 'Activo']
        labels = {'nom_objeto': 'Nombre del objeto'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        con_bootstrap(self)
        self.fields['nom_objeto'].widget.attrs['placeholder'] = 'Ej.: Piano'
        self.fields['Activo'].widget.attrs['class'] = 'form-check-input'

    def clean_nom_objeto(self):
        nombre = ' '.join(self.cleaned_data['nom_objeto'].split())
        nombre = nombre[:1].upper() + nombre[1:]
        if nombre.lower() == Objeto.OTRO.lower():
            raise forms.ValidationError('«Otro» ya existe y es fijo.')
        clave = reglas.clave_objeto(nombre)
        repetido = next((o for o in Objeto.objects.exclude(pk=self.instance.pk)
                         if reglas.clave_objeto(o.nom_objeto) == clave), None)
        if repetido:
            raise forms.ValidationError(f'Ya existe «{repetido}» en la lista.')
        return nombre


class PersonaField(forms.ModelChoiceField):
    def label_from_instance(self, u):
        return f'{u.Apellido}, {u.Nombre}'


class PersonasField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, u):
        return f'{u.Apellido}, {u.Nombre}'


class AsignarPersonalForm(forms.Form):
    """Solo ofrece al personal libre en el horario del pedido; las reglas se vuelven a controlar en reglas.py."""
    chofer = PersonaField(queryset=Usuario.objects.none(), label='Chofer', empty_label='Elegí el chofer')
    ayudantes = PersonasField(queryset=Usuario.objects.none(), required=False, label='Ayudantes de carga',
                              widget=forms.CheckboxSelectMultiple)

    def __init__(self, *args, pedido, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['chofer'].queryset = reglas.personal_libre(pedido, reglas.ROL_CHOFER)
        self.fields['ayudantes'].queryset = reglas.personal_libre(pedido, reglas.ROL_AYUDANTE)
        con_bootstrap(self)
