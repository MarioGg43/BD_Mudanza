"""Consulta del log de auditoría: qué se modificó o anuló, cuándo y quién."""
import json
from datetime import date, datetime

from django import forms
from django.apps import apps
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.utils import timezone
from django.core.paginator import Paginator
from django.shortcuts import render

from .models import LogAuditoria, Usuario
from .permisos import requiere_permiso

# Nombres legibles de las tablas que aparecen en el filtro
TABLAS = {
    'PEDIDOS': 'Pedidos', 'DETALLE_PEDIDOS': 'Detalle de pedidos', 'INVENTARIO_DETALLES': 'Inventario de pedidos',
    'PERSONAL_PEDIDO': 'Personal de pedidos', 'REPROGRAMACIONES': 'Reprogramaciones', 'USUARIOS': 'Usuarios',
    'ROLES': 'Roles', 'PERMISOS_ROLES': 'Permisos de roles', 'VEHICULOS': 'Vehículos', 'SERVICIOS': 'Servicios',
    'RECURSOS_ASIGNADOS': 'Materiales de servicios', 'OBJETOS': 'Objetos',
}


class FiltroAuditoriaForm(forms.Form):
    desde = forms.DateField(required=False, label='Desde', widget=forms.DateInput(attrs={'type': 'date'}))
    hasta = forms.DateField(required=False, label='Hasta', widget=forms.DateInput(attrs={'type': 'date'}))
    tabla = forms.ChoiceField(required=False, label='Tabla', choices=[('', 'Todas')] + sorted(TABLAS.items(), key=lambda t: t[1]))
    accion = forms.ChoiceField(required=False, label='Acción', choices=[('', 'Todas')] + LogAuditoria.ACCIONES)
    usuario = forms.ModelChoiceField(required=False, label='Usuario', empty_label='Todos',
                                     queryset=Usuario.objects.exclude(idRol__nom_rol='Cliente').order_by('Apellido', 'Nombre'))
    registro = forms.CharField(required=False, label='N° de registro', max_length=60)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            campo.widget.attrs['class'] = 'form-select' if isinstance(campo.widget, forms.Select) else 'form-control'

    def clean(self):
        d = super().clean()
        if d.get('desde') and d.get('hasta') and d['desde'] > d['hasta']:
            self.add_error('hasta', 'La fecha «Hasta» no puede ser anterior a «Desde».')
        return d


MODELOS = {m._meta.db_table: m for m in apps.get_app_config('usuarios').get_models()}


def _legible(log, campo, valor, nombres):
    """El valor como lo entiende una persona: fechas en hora de Salta, Sí/No y usuarios por su nombre."""
    if valor in (None, ''):
        return '—'
    if isinstance(valor, bool):
        return 'Sí' if valor else 'No'
    modelo = MODELOS.get(log.tabla)
    try:
        f = modelo._meta.get_field(campo) if modelo else None
    except FieldDoesNotExist:
        f = None
    if f is not None and f.is_relation and f.related_model is Usuario:
        if valor not in nombres:
            u = Usuario.objects.filter(pk=valor).first()
            nombres[valor] = f'{u.Apellido}, {u.Nombre}' if u else f'usuario {valor}'
        return nombres[valor]
    if isinstance(f, models.DateTimeField):
        try:
            return timezone.localtime(datetime.fromisoformat(str(valor).replace('Z', '+00:00'))).strftime('%d/%m/%Y %H:%M')
        except ValueError:
            return valor
    if isinstance(f, models.DateField):
        try:
            return date.fromisoformat(str(valor)).strftime('%d/%m/%Y')
        except ValueError:
            return valor
    if isinstance(f, models.TimeField):
        return str(valor)[:5]
    return valor


def _cambios(log, nombres):
    """[(campo, antes, después)] para mostrar en la tabla."""
    try:
        antes = json.loads(log.valores_anteriores or '{}')
        despues = json.loads(log.valores_nuevos) if log.valores_nuevos else {}
    except ValueError:
        return [('—', log.valores_anteriores, log.valores_nuevos)]
    return [(c, _legible(log, c, antes.get(c), nombres), _legible(log, c, despues.get(c), nombres)) for c in antes]


@requiere_permiso('AUD_CONSULTAR')
def lista(request):
    form = FiltroAuditoriaForm(request.GET or None)
    logs = LogAuditoria.objects.select_related('usuario')
    if form.is_valid():
        d = form.cleaned_data
        if d['desde']:
            logs = logs.filter(fecha_hora__date__gte=d['desde'])
        if d['hasta']:
            logs = logs.filter(fecha_hora__date__lte=d['hasta'])
        if d['tabla']:
            logs = logs.filter(tabla=d['tabla'])
        if d['accion']:
            logs = logs.filter(accion=d['accion'])
        if d['usuario']:
            logs = logs.filter(usuario=d['usuario'])
        if d['registro']:
            logs = logs.filter(id_registro=d['registro'].strip())
    pagina = Paginator(logs, 50).get_page(request.GET.get('pagina'))
    nombres = {}
    for log in pagina:
        log.cambios = _cambios(log, nombres)
        log.nombre_tabla = TABLAS.get(log.tabla, log.tabla)
    filtros = request.GET.copy()
    filtros.pop('pagina', None)
    return render(request, 'auditoria_lista.html', {'form': form, 'pagina': pagina, 'filtros': filtros.urlencode()})
