"""Tablero de inicio del administrador: lo que pasa hoy, los indicadores del mes contra el mes
anterior y cuatro gráficos (Chart.js) con los datos de la base. Todo sale de las mismas tablas
que los reportes; acá solo se resume."""
from collections import Counter
from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Sum
from django.shortcuts import render
from django.utils import timezone

from pedidos.reglas import filtro_por_venir
from usuarios.models import Pedido, Vehiculo
from usuarios.permisos import requiere_permiso

PERIODOS = {'7': 'Últimos 7 días', '30': 'Últimos 30 días', '90': 'Últimos 90 días'}
DIAS_CORTOS = ['lun', 'mar', 'mié', 'jue', 'vie', 'sáb', 'dom']
# mismo orden de colores que la analítica (paleta validada para daltonismo)
SERIES = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300']


def _variacion(actual, anterior):
    """Cuánto cambió contra el mes anterior, en %, o None si antes no había nada."""
    if not anterior:
        return None
    return float((Decimal(actual) - Decimal(anterior)) / Decimal(anterior) * 100)


def _mes(desde, hasta):
    """Lo que pasó entre esas fechas (inclusive): mudanzas, facturación y cancelaciones."""
    pedidos = Pedido.objects.filter(fecha_servicio__range=(desde, hasta))
    finalizados = pedidos.filter(estado=Pedido.FINALIZADO)
    facturacion = finalizados.aggregate(t=Sum('total'))['t'] or Decimal(0)
    hechas = finalizados.count()
    anulados = Pedido.objects.filter(estado=Pedido.ANULADO, fecha_anulacion__date__range=(desde, hasta)).count()
    return {'mudanzas': pedidos.exclude(estado=Pedido.ANULADO).count(), 'facturacion': facturacion,
            'ticket': facturacion / hechas if hechas else Decimal(0), 'anulados': anulados,
            'total': pedidos.count()}


@requiere_permiso('PED_GESTIONAR')
def tablero(request):
    ahora = timezone.localtime()
    hoy = ahora.date()
    clave = request.GET.get('periodo', '30')
    dias = int(clave) if clave in PERIODOS else 30
    desde = hoy - timedelta(days=dias - 1)

    # ---- hoy
    activos_hoy = Pedido.objects.filter(fecha_servicio=hoy, estado__in=Pedido.ACTIVOS)
    en_curso = Pedido.objects.filter(estado=Pedido.CONFIRMADO, inicio_real__isnull=False, fin_real__isnull=True).count()
    por_confirmar = Pedido.objects.filter(filtro_por_venir(), estado=Pedido.PENDIENTE).count()
    disponibles = Vehiculo.objects.filter(estado='Disponible').count()

    # ---- el mes contra el mismo tramo del mes anterior (del 1 al mismo día)
    inicio_mes = hoy.replace(day=1)
    fin_anterior = inicio_mes - timedelta(days=1)
    inicio_anterior = fin_anterior.replace(day=1)
    tope_anterior = inicio_anterior + timedelta(days=min(hoy.day, fin_anterior.day) - 1)
    mes, anterior = _mes(inicio_mes, hoy), _mes(inicio_anterior, tope_anterior)
    cancelacion = mes['anulados'] / mes['total'] * 100 if mes['total'] else 0
    cancelacion_ant = anterior['anulados'] / anterior['total'] * 100 if anterior['total'] else 0

    # ---- gráficos del período elegido (más los próximos 7 días en el primero)
    pedidos = list(Pedido.objects.filter(fecha_servicio__range=(desde, hoy + timedelta(days=7)))
                   .exclude(estado=Pedido.ANULADO).prefetch_related('detalles__idServicio'))
    dias_lista = [desde + timedelta(days=i) for i in range(dias + 7)]
    # hasta hoy: las finalizadas y las que todavía nadie finalizó (así se ve cuando se cierra una)
    finalizadas = Counter(p.fecha_servicio for p in pedidos if p.fecha_servicio <= hoy and p.estado == Pedido.FINALIZADO)
    sin_finalizar = Counter(p.fecha_servicio for p in pedidos if p.fecha_servicio <= hoy and p.estado != Pedido.FINALIZADO)
    programadas = Counter(p.fecha_servicio for p in pedidos if p.fecha_servicio > hoy)
    del_periodo = [p for p in pedidos if p.fecha_servicio <= hoy]

    servicios = Counter()
    for p in del_periodo:
        principal = next((d.idServicio.Tipo_servicio for d in p.detalles.all() if d.idServicio.Categoria == 'Principal'), 'Sin servicio')
        servicios[principal] += 1
    por_servicio = sorted(servicios.items(), key=lambda x: (-x[1], x[0]))
    horas = Counter(p.hora_servicio.hour for p in del_periodo)
    rango_horas = list(range(min(horas, default=7), max(horas, default=18) + 1))
    uso = Counter()
    for p in del_periodo:
        if p.estado == Pedido.FINALIZADO and p.inicio_real and p.fin_real:
            uso[p.patente_vehiculo_id] += (p.fin_real - p.inicio_real).total_seconds() / 3600
        elif p.estado in (Pedido.FINALIZADO, Pedido.CONFIRMADO):
            uso[p.patente_vehiculo_id] += p.duracion_horas
    vehiculos = sorted(uso.items(), key=lambda x: -x[1])[:6]

    graficos = {
        'dias': {
            'etiquetas': [f'{DIAS_CORTOS[d.weekday()]} {d:%d/%m}' for d in dias_lista],
            'finalizadas': [finalizadas.get(d, 0) for d in dias_lista],
            'sin_finalizar': [sin_finalizar.get(d, 0) for d in dias_lista],
            'programadas': [programadas.get(d, 0) for d in dias_lista],
        },
        'servicios': {'etiquetas': [s for s, _ in por_servicio], 'valores': [n for _, n in por_servicio],
                      'colores': [SERIES[i % len(SERIES)] for i in range(len(por_servicio))]},
        'horas': {'etiquetas': [f'{h:02d} h' for h in rango_horas], 'valores': [horas.get(h, 0) for h in rango_horas]},
        'vehiculos': {'etiquetas': [v for v, _ in vehiculos], 'valores': [round(h, 1) for _, h in vehiculos]},
    }
    proximas = (Pedido.objects.filter(filtro_por_venir()).select_related('idUsuario', 'patente_vehiculo')
                .prefetch_related('personal__idUsuario').order_by('fecha_servicio', 'hora_servicio')[:6])

    saludo = 'Buenos días' if ahora.hour < 12 else 'Buenas tardes' if ahora.hour < 20 else 'Buenas noches'
    return render(request, 'reportes/tablero.html', {
        'saludo': saludo, 'hoy': hoy, 'mudanzas_hoy': activos_hoy.count(), 'en_curso': en_curso,
        'por_confirmar': por_confirmar, 'disponibles': disponibles, 'flota': Vehiculo.objects.count(),
        'mes': mes, 'cancelacion': cancelacion,
        'var_mudanzas': _variacion(mes['mudanzas'], anterior['mudanzas']),
        'var_facturacion': _variacion(mes['facturacion'], anterior['facturacion']),
        'var_ticket': _variacion(mes['ticket'], anterior['ticket']),
        'var_cancelacion': cancelacion - cancelacion_ant if anterior['total'] else None,
        'periodo': str(dias), 'periodos': PERIODOS, 'graficos': graficos, 'proximas': proximas,
        'total_periodo': len(del_periodo),
    })
