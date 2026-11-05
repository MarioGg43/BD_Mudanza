"""Controladores REST del log de auditoría. Usan la misma consulta y las mismas frases legibles que
la pantalla de Django (usuarios/views_auditoria.py): «Carlos Sarmiento anuló el pedido N° 13»,
con cada campo en Antes / Después, la plata con $ y las personas por su nombre."""
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.utils import timezone

from usuarios import views_auditoria as aud
from usuarios.models import LogAuditoria, Usuario
from .autenticacion import endpoint

POR_PAGINA = 50


def _enlace(log, antes):
    """A qué pantalla de React lleva el «Ver» de cada registro."""
    t, pk = log.tabla, log.id_registro
    if t == 'PEDIDOS':
        return f'/pedidos/{pk}'
    if t in ('PERSONAL_PEDIDO', 'DETALLE_PEDIDOS', 'INVENTARIO_DETALLES', 'REPROGRAMACIONES') and antes.get('idPedido'):
        return f'/pedidos/{antes["idPedido"]}'
    if t == 'VEHICULOS':
        return f'/vehiculos/{pk}'
    if t == 'SERVICIOS':
        return f'/servicios/{pk}/editar'
    if t == 'ROLES':
        return f'/roles/{pk}/editar'
    if t == 'OBJETOS':
        return '/objetos'
    if t == 'USUARIOS':
        return '/usuarios'
    return None


@endpoint('AUD_CONSULTAR')
def auditoria(request):
    """GET /api/auditoria?desde=&hasta=&tabla=&accion=&usuario=&registro=&pagina="""
    form, logs = aud._consulta(request)
    pagina = Paginator(logs, POR_PAGINA).get_page(request.GET.get('pagina'))
    aud._preparar(pagina)
    registros = []
    for log in pagina:
        antes, _ = aud._valores(log)
        momento = timezone.localtime(log.fecha_hora)
        registros.append({
            'id': log.id_log, 'fecha': momento.strftime('%d/%m/%Y'), 'hora': momento.strftime('%H:%M:%S'),
            'accion': log.accion, 'tabla': log.nombre_tabla, 'frase': log.frase, 'detalle': log.detalle,
            'link': _enlace(log, antes), 'cambios': [list(c) for c in log.cambios]})
    return JsonResponse({
        'registros': registros, 'pagina': pagina.number, 'paginas': pagina.paginator.num_pages,
        'total': pagina.paginator.count,
        'errores': {k: ' '.join(v) for k, v in form.errors.items()},
    })


@endpoint('AUD_CONSULTAR')
def opciones(request):
    """GET /api/auditoria/opciones: las listas de los filtros."""
    return JsonResponse({
        'tablas': [{'value': k, 'label': v} for k, v in sorted(aud.TABLAS.items(), key=lambda t: t[1])],
        'acciones': [a for a, _ in LogAuditoria.ACCIONES],
        'usuarios': [{'value': str(u.id_usuario), 'label': f'{u.Apellido}, {u.Nombre}'} for u in
                     Usuario.objects.exclude(idRol__nom_rol='Cliente').order_by('Apellido', 'Nombre')],
    })


@endpoint('AUD_CONSULTAR')
def pdf(request):
    """GET /api/auditoria/pdf con los mismos filtros: el PDF que también genera la pantalla de Django."""
    return aud.pdf(request)
