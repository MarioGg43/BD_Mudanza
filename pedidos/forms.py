from django import forms

from usuarios.models import Pedido, Servicio, Usuario


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
