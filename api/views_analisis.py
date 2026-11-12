"""Controladores REST del Parcial N° 2 para React: el tablero, los reportes consolidados (M2) y las
notificaciones con sus umbrales (M3). No calculan nada propio: usan las mismas funciones que las
pantallas de Django (reportes/tablero.py, reportes/consultas.py y notificaciones/reglas.py)."""
from datetime import date

from django.core.paginator import Paginator
from django.http import JsonResponse
from django.utils import timezone

from notificaciones import reglas as alertas
from notificaciones.views import LIMITES
from pedidos.pdf import respuesta_pdf
from reportes import tablero as tab
from reportes.templatetags.reportes import formato
from reportes.views import REPORTES, FiltroReporteForm
from usuarios.models import Configuracion
from usuarios.permisos import tiene_permiso
from .autenticacion import endpoint, error, leer_json


# ------------------------------------------------------------------ tablero
@endpoint('PED_GESTIONAR')
def tablero(request):
    """GET /api/tablero?periodo=7|30|90: indicadores, gráficos y las próximas mudanzas."""
    d = tab.calcular(request.GET.get('periodo', '30'))
    pesos = lambda v: formato(v, 'pesos')
    return JsonResponse({
        'saludo': d['saludo'], 'hoy': d['hoy'].isoformat(),
        'hoy_resumen': {'mudanzas_hoy': d['mudanzas_hoy'], 'en_curso': d['en_curso'],
                        'por_confirmar': d['por_confirmar'], 'disponibles': d['disponibles'], 'flota': d['flota']},
        'mes': {'mudanzas': d['mes']['mudanzas'], 'facturacion': pesos(d['mes']['facturacion']),
                'ticket': pesos(d['mes']['ticket']), 'anulados': d['mes']['anulados'],
                'cancelacion': round(d['cancelacion'], 1)},
        'variacion': {'mudanzas': d['var_mudanzas'], 'facturacion': d['var_facturacion'],
                      'ticket': d['var_ticket'], 'cancelacion': d['var_cancelacion']},
        'periodo': d['periodo'], 'periodos': [{'value': k, 'label': v} for k, v in d['periodos'].items()],
        'graficos': d['graficos'], 'total_periodo': d['total_periodo'],
        'proximas': [{
            'id': p.pk, 'fecha': p.fecha_servicio.strftime('%d/%m'), 'hora': p.hora_servicio.strftime('%H:%M'),
            'cliente': f'{p.idUsuario.Nombre} {p.idUsuario.Apellido}', 'estado': p.estado,
            'vehiculo': p.patente_vehiculo_id, 'origen': p.origen, 'destino': p.destino,
            'chofer': next((f'{x.idUsuario.Nombre} {x.idUsuario.Apellido}' for x in p.personal.all()
                            if x.Funcion == 'Chofer'), None),
        } for p in d['proximas']],
    })


# ------------------------------------------------------------------ reportes (M2)
def _reporte(request, clave):
    """(reporte, form, datos) o una respuesta de error. Sin fechas: del 1 de enero hasta hoy."""
    reporte = REPORTES.get(clave)
    if not reporte:
        return None, None, None, error('Reporte inexistente.', 404)
    if not tiene_permiso(request.usuario, reporte['permiso']):
        return None, None, None, error('No tenés permiso para este reporte.', 403)
    hoy = timezone.localdate()
    datos_get = request.GET.copy()
    datos_get.setdefault('desde', date(hoy.year, 1, 1).isoformat())
    datos_get.setdefault('hasta', hoy.isoformat())
    form = FiltroReporteForm(datos_get, filtro=reporte['filtro'])
    if not form.is_valid():
        return reporte, form, None, error('Revisá los filtros.', 400, {k: ' '.join(v) for k, v in form.errors.items()})
    d = form.cleaned_data
    return reporte, form, reporte['calcular'](d['desde'], d['hasta'], d.get(form.extra) or ''), None


def _filtros_usados(form):
    usados = []
    for nombre, campo in form.fields.items():
        valor = form.cleaned_data.get(nombre)
        if valor:
            texto = valor.strftime('%d/%m/%Y') if hasattr(valor, 'strftime') else dict(campo.choices).get(valor, valor)
            usados.append((campo.label, texto))
    return usados


@endpoint()
def reportes(request):
    """GET /api/reportes: los reportes que puede ver esta persona, con su filtro propio."""
    lista = [{'clave': k, 'titulo': r['titulo'], 'descripcion': r['descripcion'], 'cruza': r['cruza'],
              'icono': r['icono'], 'color': r['color'],
              'filtro': {'nombre': r['filtro'][0], 'etiqueta': r['filtro'][1],
                         'opciones': [{'value': v, 'label': l} for v, l in r['filtro'][2]]}}
             for k, r in REPORTES.items() if tiene_permiso(request.usuario, r['permiso'])]
    if not lista:
        return error('No tenés permiso para ver reportes.', 403)
    return JsonResponse({'reportes': lista})


@endpoint()
def reporte(request, clave):
    """GET /api/reportes/<clave>?desde=&hasta=&<filtro>=&pagina=: la grilla ya formateada (pesos,
    horas, porcentajes) con sus totales, el resumen por motivo y la nota."""
    rep, form, datos, respuesta = _reporte(request, clave)
    if respuesta:
        return respuesta
    columnas = [{'titulo': t, 'clave': c, 'tipo': tipo} for t, c, tipo in datos['columnas']]
    celda = lambda fila, c: (f'N° {fila.get("pedido")}' if c['clave'] == 'pedido'
                             else formato(fila.get(c['clave']), c['tipo']))
    pagina = Paginator(datos['filas'], 25).get_page(request.GET.get('pagina'))
    return JsonResponse({
        'titulo': rep['titulo'], 'cruza': rep['cruza'], 'columnas': columnas,
        'filas': [{'id_pedido': f.get('pedido'), 'celdas': [celda(f, c) for c in columnas]} for f in pagina],
        'totales': [str(datos['totales'].get(c['clave'], '')) if c['tipo'] == 'fechahora'
                    else formato(datos['totales'].get(c['clave']), c['tipo']) for c in columnas] if datos['filas'] else [],
        'resumen': [{'tipo': r['tipo'], 'motivo': r['motivo'], 'cantidad': r['cantidad'],
                     'porcentaje': formato(r['porcentaje'], 'porcentaje')} for r in datos['resumen']],
        'nota': datos['nota'], 'filtros_usados': _filtros_usados(form),
        'pagina': pagina.number, 'paginas': pagina.paginator.num_pages, 'total': pagina.paginator.count,
    })


@endpoint()
def reporte_pdf(request, clave):
    """GET /api/reportes/<clave>/pdf con los mismos filtros: el mismo PDF que la pantalla de Django."""
    rep, form, datos, respuesta = _reporte(request, clave)
    if respuesta:
        return respuesta
    contexto = {'usuario': request.usuario, 'reporte': rep, 'clave': clave, 'form': form, 'datos': datos,
                'filtros_usados': _filtros_usados(form), 'emitido': timezone.localtime()}
    return respuesta_pdf(request, 'reportes/reporte_pdf.html', contexto, rep['titulo'].replace(' ', '_') + '.pdf')


# ------------------------------------------------------------------ notificaciones (M3)
def _enlace_react(enlace):
    """Los enlaces se guardan con las rutas de Django («/pedidos/18/»); React usa «/pedidos/18»."""
    return enlace.rstrip('/') if enlace else None


def _notif(n):
    return {'id': n.id_notificacion, 'tipo': n.tipo, 'mensaje': n.mensaje, 'leida': n.leida,
            'fecha': timezone.localtime(n.fecha).strftime('%d/%m/%Y %H:%M'), 'enlace': _enlace_react(n.enlace),
            'perfil': n.destino_perfil.nom_rol, 'correo': n.correo}


@endpoint()
def notificaciones(request):
    """GET /api/notificaciones?ver=sin_leer|todas&pagina=: la bandeja de quien entró."""
    todas = alertas.de_usuario(request.usuario).select_related('destino_perfil')
    ver = request.GET.get('ver', 'sin_leer')
    lista = todas.filter(leida=False) if ver == 'sin_leer' else todas
    pagina = Paginator(lista, 20).get_page(request.GET.get('pagina'))
    return JsonResponse({'notificaciones': [_notif(n) for n in pagina], 'ver': ver,
                         'sin_leer': todas.filter(leida=False).count(), 'total': todas.count(),
                         'pagina': pagina.number, 'paginas': pagina.paginator.num_pages})


@endpoint()
def notificaciones_contar(request):
    """GET /api/notificaciones/contar: el número de la campanita."""
    return JsonResponse({'sin_leer': alertas.de_usuario(request.usuario).filter(leida=False).count()})


@endpoint(metodos=('POST',))
def notificacion_leer(request, id_notificacion):
    """POST /api/notificaciones/<id>/leer: la marca como leída (una ajena no existe para esta persona)."""
    notif = alertas.de_usuario(request.usuario).filter(pk=id_notificacion).first()
    if not notif:
        return error('Notificación inexistente.', 404)
    if not notif.leida:
        notif.leida, notif.fecha_lectura = True, timezone.now()
        notif.save(update_fields=['leida', 'fecha_lectura'])
    return JsonResponse({'ok': True, 'enlace': _enlace_react(notif.enlace)})


@endpoint(metodos=('POST',))
def notificaciones_leer_todas(request):
    n = alertas.de_usuario(request.usuario).filter(leida=False).update(leida=True, fecha_lectura=timezone.now())
    return JsonResponse({'ok': True, 'marcadas': n})


@endpoint('CFG_GESTIONAR', metodos=('GET', 'PUT'))
def configuracion(request):
    """GET /api/configuracion: los umbrales de las reglas. PUT {clave: valor, ...}: los guarda
    (cada cambio queda en la auditoría), con los mismos límites que la pantalla de Django."""
    parametros = list(Configuracion.objects.all())
    if request.method == 'PUT':
        datos, errores = leer_json(request), {}
        for p in parametros:
            valor = str(datos.get(p.clave, p.valor)).strip()
            if p.clave in LIMITES:
                minimo, maximo = LIMITES[p.clave]
                if not valor.isdigit() or not minimo <= int(valor) <= maximo:
                    errores[p.clave] = f'Tiene que ser un número entero de {minimo} a {maximo}.'
            elif valor and '@' not in valor:
                errores[p.clave] = 'Escribí un correo válido o dejalo vacío.'
            p.nuevo = valor
        if errores:
            return error('Revisá los valores marcados.', 400, errores)
        for p in parametros:
            if p.valor != p.nuevo:
                p.valor = p.nuevo
                p.save(update_fields=['valor'])
    return JsonResponse({'parametros': [{'clave': p.clave, 'valor': p.valor, 'descripcion': p.descripcion,
                                         'limites': LIMITES.get(p.clave)} for p in parametros]})


@endpoint('CFG_GESTIONAR', metodos=('POST',))
def evaluar_alertas(request):
    """POST /api/alertas/evaluar: corre ya la tarea programada (para la defensa)."""
    nuevas = alertas.evaluar_programadas()
    return JsonResponse({'total': sum(nuevas.values()), 'detalle': nuevas})


# ------------------------------------------------------------------ números del menú lateral
@endpoint()
def menu(request):
    """GET /api/menu: lo que muestran el menú lateral y la barra de arriba del personal (los mismos
    números que el context processor de Django): pedidos por confirmar, mudanzas en curso,
    materiales bajo el mínimo y notificaciones sin leer."""
    from pedidos.materiales import bajo_minimo
    from pedidos.reglas import filtro_por_venir
    from usuarios.models import Pedido
    u, datos = request.usuario, {}
    if tiene_permiso(u, 'PED_GESTIONAR'):
        datos['pendientes'] = Pedido.objects.filter(filtro_por_venir(), estado=Pedido.PENDIENTE).count()
        datos['en_curso'] = Pedido.objects.filter(estado=Pedido.CONFIRMADO, inicio_real__isnull=False,
                                                  fin_real__isnull=True).count()
    if tiene_permiso(u, 'MAT_GESTIONAR'):
        datos['materiales_bajos'] = bajo_minimo().count()
    datos['sin_leer'] = alertas.de_usuario(u).filter(leida=False).count()
    return JsonResponse(datos)
