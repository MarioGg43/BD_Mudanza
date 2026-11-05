"""Consulta del log de auditoría: qué se modificó o anuló, cuándo y quién."""
import json
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from django import forms
from django.apps import apps
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.utils import timezone
from django.core.paginator import Paginator
from django.shortcuts import render
from django.urls import reverse

from pedidos.pdf import respuesta_pdf

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

# Nombres para mostrar donde el del modelo no sirve («fecha anulacion», «estado», «total»…)
ETIQUETAS = {
    'estado': 'Estado', 'total': 'Total', 'fecha_anulacion': 'Fecha de anulación',
    'motivo_anulacion': 'Motivo de anulación', 'Precio_base': 'Precio', 'subtotal': 'Subtotal',
    'kilometraje': 'Kilometraje', 'observaciones': 'Observaciones', 'Activo': 'Activo', 'Clave': 'Clave',
    'Telefono': 'Teléfono', 'fecha_anterior': 'Fecha anterior', 'hora_anterior': 'Hora anterior',
    'fecha_nueva': 'Fecha nueva', 'hora_nueva': 'Hora nueva', 'motivo': 'Motivo', 'observacion': 'Observación',
    'visto_cliente': 'Visto por el cliente', 'estado_objeto': 'Activo',
    'inicio_real': 'Inicio real', 'fin_real': 'Fin real',
}
# Campos de plata: se muestran como «$20.000»
DINERO = {'Precio_base', 'total', 'precio_unitario', 'subtotal', 'Monto', 'Monto_cob'}
VERBOS = {LogAuditoria.ANULACION: 'anuló', LogAuditoria.BAJA: 'dio de baja', LogAuditoria.REACTIVACION: 'reactivó',
          LogAuditoria.ELIMINACION: 'quitó', LogAuditoria.MODIFICACION: 'modificó'}


def _campo(log, nombre):
    modelo = MODELOS.get(log.tabla)
    try:
        return modelo._meta.get_field(nombre) if modelo else None
    except FieldDoesNotExist:
        return None


def _etiqueta(log, nombre):
    if nombre in ETIQUETAS:
        return ETIQUETAS[nombre]
    f = _campo(log, nombre)
    texto = str(f.verbose_name) if f is not None else nombre.replace('_', ' ')
    return texto[:1].upper() + texto[1:]


def _plata(valor):
    """«20000» → «$20.000»; con centavos solo si los hay."""
    try:
        n = Decimal(str(valor))
    except InvalidOperation:
        return valor
    texto = f'{n:,.2f}' if n != n.to_integral_value() else f'{n:,.0f}'
    return '$' + texto.replace(',', 'X').replace('.', ',').replace('X', '.')


def _legible(log, campo, valor, nombres):
    """El valor como lo entiende una persona: plata con $, fechas en hora de Salta, Sí/No y personas por su nombre."""
    if valor in (None, ''):
        return '—'
    if isinstance(valor, bool):
        return 'Sí' if valor else 'No'
    if campo in DINERO:
        return _plata(valor)
    f = _campo(log, campo)
    if f is not None and f.is_relation and f.related_model is Usuario:
        if valor not in nombres:
            u = Usuario.objects.filter(pk=valor).first()
            nombres[valor] = f'{u.Nombre} {u.Apellido}' if u else f'usuario {valor}'
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


def _valores(log):
    try:
        antes = json.loads(log.valores_anteriores or '{}')
        despues = json.loads(log.valores_nuevos) if log.valores_nuevos else {}
    except ValueError:
        return {}, {}
    return antes, despues


def _que_registro(log, antes, nombres):
    """(texto, link) del registro: «el pedido N° 13», «el vehículo AA123XR», «a María Gómez»…"""
    t, pk = log.tabla, log.id_registro
    if t == 'PEDIDOS':
        return f'el pedido N° {pk}', reverse('pedidos_detalle', args=[pk])
    if t == 'VEHICULOS':
        return f'el vehículo {pk}', reverse('detalleVehiculo', args=[pk])
    if t == 'USUARIOS':
        return f'a {_nombre_usuario(pk, nombres)}', None
    if t in ('PERSONAL_PEDIDO', 'DETALLE_PEDIDOS', 'INVENTARIO_DETALLES', 'REPROGRAMACIONES') and antes.get('idPedido'):
        return f'del pedido N° {antes["idPedido"]}', reverse('pedidos_detalle', args=[antes['idPedido']])
    modelo = MODELOS.get(t)
    obj = modelo.objects.filter(pk=pk).first() if modelo else None
    if t == 'SERVICIOS':
        return f'el servicio «{obj or pk}»', reverse('servicios_editar', args=[pk]) if obj else None
    if t == 'OBJETOS':
        return f'el objeto «{obj or pk}»', reverse('objetos_editar', args=[pk]) if obj else None
    if t == 'ROLES':
        return f'el rol «{obj or pk}»', reverse('roles_editar', args=[pk]) if obj else None
    if t == 'RECURSOS_ASIGNADOS':
        return f'el material «{antes.get("Materiales", pk)}»', None
    if t == 'PERMISOS_ROLES':
        return 'un permiso de un rol', None
    return f'el registro {pk} de {TABLAS.get(t, t).lower()}', None


def _nombre_usuario(pk, nombres):
    if pk not in nombres:
        u = Usuario.objects.filter(pk=pk).first()
        nombres[pk] = f'{u.Nombre} {u.Apellido}' if u else f'usuario {pk}'
    return nombres[pk]


def _resumen(log, antes, despues, nombres):
    """La frase de arriba de cada cambio: «Carlos Sarmiento anuló el pedido N° 13» y un detalle corto."""
    quien = f'{log.usuario.Nombre} {log.usuario.Apellido}' if log.usuario else 'El sistema'
    registro, link = _que_registro(log, antes, nombres)
    verbo, detalle = VERBOS.get(log.accion, 'modificó'), ''
    if log.accion == LogAuditoria.ANULACION:
        detalle = despues.get('motivo_anulacion') or ''
    elif log.accion == LogAuditoria.ELIMINACION and log.tabla == 'PERSONAL_PEDIDO':
        verbo = f'sacó a {_nombre_usuario(antes.get("idUsuario"), nombres)} ({str(antes.get("Funcion", "")).lower()})'
    elif log.tabla == 'PEDIDOS' and 'fin_real' in antes:
        verbo = 'marcó «Terminamos» y finalizó'
    elif log.tabla == 'PEDIDOS' and 'inicio_real' in antes:
        verbo = 'marcó «Empezamos» en'
    elif log.tabla == 'PEDIDOS' and despues.get('estado') == 'Confirmado':
        verbo = 'confirmó'
    elif log.tabla == 'PEDIDOS' and despues.get('estado') == 'Finalizado':
        verbo = 'finalizó'
    elif log.tabla == 'PEDIDOS' and {'fecha_servicio', 'hora_servicio'} & set(antes):
        verbo = 'reprogramó'
    elif log.tabla == 'USUARIOS' and set(antes) == {'Clave'}:
        verbo = 'cambió la clave de'
        registro = registro[2:]  # «a María» → «María»
    return f'{quien} {verbo} {registro}', detalle, link


def _cambios(log, antes, despues, nombres):
    """[(campo, antes, después)] para mostrar debajo de la frase."""
    return [(_etiqueta(log, c), _legible(log, c, antes.get(c), nombres), _legible(log, c, despues.get(c), nombres))
            for c in antes]


MAX_PDF = 500  # registros como máximo en el PDF (los más nuevos)


def _consulta(request):
    """El formulario y los registros con los filtros del GET: la usan la pantalla y el PDF."""
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
    return form, logs


def _preparar(logs):
    """Le agrega a cada registro la frase, el detalle, el link y los cambios para mostrar."""
    nombres = {}
    for log in logs:
        antes, despues = _valores(log)
        log.frase, log.detalle, log.link = _resumen(log, antes, despues, nombres)
        log.cambios = _cambios(log, antes, despues, nombres)  # siempre en Antes / Después, aunque sea uno
        log.nombre_tabla = TABLAS.get(log.tabla, log.tabla)
    return logs


@requiere_permiso('AUD_CONSULTAR')
def lista(request):
    form, logs = _consulta(request)
    pagina = Paginator(logs, 50).get_page(request.GET.get('pagina'))
    _preparar(pagina)
    filtros = request.GET.copy()
    filtros.pop('pagina', None)
    return render(request, 'auditoria_lista.html', {'form': form, 'pagina': pagina, 'filtros': filtros.urlencode()})


@requiere_permiso('AUD_CONSULTAR')
def descargar(request):
    return pdf(request)


def pdf(request):
    """El log en PDF, con los mismos filtros que la pantalla (lo usan esta vista y la API de React,
    cada una con su control de permiso)."""
    form, logs = _consulta(request)
    total = logs.count()
    usados = []
    if form.is_valid():
        for nombre, campo in form.fields.items():
            valor = form.cleaned_data.get(nombre)
            if valor:
                if hasattr(valor, 'strftime'):
                    texto = valor.strftime('%d/%m/%Y')
                elif isinstance(campo, forms.ChoiceField):
                    texto = dict(campo.choices).get(valor, valor)
                elif isinstance(valor, Usuario):
                    texto = f'{valor.Nombre} {valor.Apellido}'
                else:
                    texto = str(valor)
                usados.append((campo.label, texto))
    return respuesta_pdf(request, 'auditoria_pdf.html', {
        'logs': _preparar(list(logs[:MAX_PDF])), 'total': total, 'max_pdf': MAX_PDF,
        'filtros_usados': usados, 'emitido': timezone.localtime()}, 'Auditoria.pdf')
