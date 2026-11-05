"""Controladores REST del portal del personal (choferes y ayudantes): sus mudanzas, «Empezamos»,
«Terminamos» y el relevamiento. Sin precios: el personal ve qué hay que hacer, no cuánto sale.
Las reglas son las de pedidos/reglas.py (marcar_inicio, marcar_fin, relevamiento)."""
from datetime import timedelta

from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone

from pedidos import reglas
from pedidos.forms import objetos_para_elegir
from usuarios.models import Pedido, PersonalPedido, Servicio, Vehiculo
from usuarios.permisos import permisos_de
from .autenticacion import endpoint, error, leer_json


def _hora(dt):
    return timezone.localtime(dt).strftime('%H:%M') if dt else None


def _mudanza(p, usuario, ahora):
    soy_chofer = any(x.idUsuario_id == usuario.pk and x.Funcion == PersonalPedido.CHOFER for x in p.personal.all())
    sin_empezar = soy_chofer and p.estado == Pedido.CONFIRMADO and not p.inicio_real
    puede_empezar = sin_empezar and reglas.se_puede_empezar(p, ahora)
    return {
        'id': p.id_pedido, 'fecha_servicio': p.fecha_servicio.isoformat(), 'hora_servicio': p.hora_servicio.strftime('%H:%M'),
        'hasta': p.hasta, 'estado': p.estado, 'en_curso': p.en_curso, 'vencido': p.vencido,
        'inicio_real': _hora(p.inicio_real), 'fin_esperado': _hora(p.fin_esperado),
        'soy_chofer': soy_chofer, 'puede_empezar': puede_empezar,
        'empieza_tarde': puede_empezar and ahora > p.inicio,                       # ya pasó la hora y no empezaron
        'ya_paso': sin_empezar and timezone.localtime(ahora).date() > p.fecha_servicio,
        'origen': p.origen, 'destino': p.destino,
        'vehiculo': f'{p.patente_vehiculo_id} · {p.patente_vehiculo.marca_modelo}',
        'servicios': [d.idServicio.Tipo_servicio for d in p.detalles.all()],
        'equipo': [f'{x.idUsuario.Nombre} {x.idUsuario.Apellido} ({x.get_Funcion_display().lower()})' for x in p.personal.all()],
        'cliente': f'{p.idUsuario.Nombre} {p.idUsuario.Apellido}', 'telefono': p.idUsuario.Telefono or '',
        'inventario': [{'cantidad': i.Cantidad, 'nombre': i.idObjeto.nom_objeto, 'fragil': i.Fragil,
                        'observacion': i.Observacion or ''} for i in p.inventario.all()],
    }


@endpoint('MUDANZAS_OPERAR')
def portal(request):
    """GET /api/portal: las mudanzas por venir de quien entra y las confirmadas de los últimos días
    que todavía no se finalizaron (las que están en curso), y los vehículos que maneja."""
    usuario = request.usuario
    recientes = Q(estado=Pedido.CONFIRMADO, fecha_servicio__gte=timezone.localdate() - timedelta(days=5))
    mudanzas = (Pedido.objects.filter(reglas.filtro_por_venir() | recientes, personal__idUsuario=usuario)
                .distinct().select_related('patente_vehiculo', 'idUsuario')
                .prefetch_related('detalles__idServicio', 'inventario__idObjeto', 'personal__idUsuario')
                .order_by('fecha_servicio', 'hora_servicio'))
    ahora = timezone.now()
    return JsonResponse({
        'mudanzas': [_mudanza(p, usuario, ahora) for p in mudanzas],
        'vehiculos': [{'patente': v.patente, 'modelo': v.marca_modelo, 'tipo': v.tipo_vehiculo, 'anio': v.anio,
                       'estado': v.estado} for v in Vehiculo.objects.filter(chofer_asignado=usuario).order_by('patente')],
        'permisos': sorted(permisos_de(usuario)),
    })


def _marcar(request, id_pedido, funcion, estado):
    get_object_or_404(Pedido, pk=id_pedido)
    try:
        p = funcion(id_pedido, request.usuario)
    except reglas.ErrorPedido as e:
        return error(str(e))
    return JsonResponse({'id': id_pedido, 'estado': estado, 'hora': _hora(p.inicio_real if estado == 'En curso' else p.fin_real)})


@endpoint('MUDANZAS_OPERAR', metodos=('POST',))
def empezar(request, id_pedido):
    """POST /api/portal/<id>/empezar: «Empezamos» (solo el chofer, el día de la mudanza)."""
    return _marcar(request, id_pedido, reglas.marcar_inicio, 'En curso')


@endpoint('MUDANZAS_OPERAR', metodos=('POST',))
def terminar(request, id_pedido):
    """POST /api/portal/<id>/terminar: «Terminamos» (guarda la hora y finaliza el pedido)."""
    return _marcar(request, id_pedido, reglas.marcar_fin, Pedido.FINALIZADO)


@endpoint('MUDANZAS_OPERAR', metodos=('GET', 'POST'))
def relevamiento(request, id_pedido):
    """GET /api/portal/<id>/relevamiento: lo declarado, el catálogo y los adicionales que se pueden sumar.
    POST {reales: {id_item: cantidad}, nuevos: [...], adicionales: [...], recargo, motivo}."""
    pedido = get_object_or_404(Pedido.objects.select_related('idUsuario')
                                             .prefetch_related('inventario__idObjeto', 'detalles__idServicio'), pk=id_pedido)
    es_chofer = pedido.personal.filter(Funcion=PersonalPedido.CHOFER, idUsuario=request.usuario).exists()
    if not es_chofer or not pedido.en_curso:
        return error('El relevamiento lo hace el chofer de la mudanza, después de marcar «Empezamos».', 403)

    if request.method == 'POST':
        d = leer_json(request)
        reales = d.get('reales') if isinstance(d.get('reales'), dict) else {}
        nuevos = [{'objeto': n.get('objeto'), 'cantidad': n.get('cantidad'), 'fragil': bool(n.get('fragil')),
                   'observacion': str(n.get('observacion') or '')}
                  for n in (d.get('nuevos') or []) if isinstance(n, dict)]
        try:
            reglas.relevamiento(id_pedido, request.usuario, reales, nuevos,
                                [int(x) for x in d.get('adicionales') or [] if str(x).isdigit()],
                                d.get('recargo') or 0, str(d.get('motivo') or ''))
        except reglas.ErrorPedido as e:
            return error(str(e) if '__all__' in e.errores else 'Revisá los datos marcados.', errores=e.errores)
        return JsonResponse({'id': id_pedido})

    tiene = {d.idServicio_id for d in pedido.detalles.all()}
    return JsonResponse({
        'id': pedido.id_pedido, 'cliente': f'{pedido.idUsuario.Nombre} {pedido.idUsuario.Apellido}',
        'items': [{'id': i.pk, 'objeto': i.idObjeto_id, 'nombre': i.idObjeto.nom_objeto, 'otro': i.idObjeto.es_otro,
                   'cantidad': i.Cantidad, 'fragil': i.Fragil, 'observacion': i.Observacion or ''}
                  for i in pedido.inventario.all()],
        'adicionales': [{'id': s.id_servicio, 'nombre': s.Tipo_servicio} for s in
                        Servicio.objects.filter(Activo=True, Categoria=Servicio.ADICIONAL).exclude(pk__in=tiene)
                        .order_by('Tipo_servicio')],
        'objetos': [{'id': o.pk, 'nombre': o.nom_objeto, 'clave': reglas.clave_objeto(o.nom_objeto), 'otro': o.es_otro}
                    for o in objetos_para_elegir()],
        'max_cantidad': reglas.MAX_CANTIDAD,
        'recargo': float(pedido.recargo), 'motivo': pedido.motivo_recargo or '',
    })
