"""Los tres reportes consolidados del Parcial N° 2 (M2). Cada uno cruza dos o más procesos del
Hito 4 y devuelve lo mismo, así una sola pantalla y un solo PDF sirven para los tres:

    {'columnas': [(título, clave, tipo)], 'filas': [dict], 'totales': dict, 'resumen': [...]}

`tipo` dice cómo se muestra el valor: texto, entero, horas, minutos, porcentaje o pesos.

| Reporte                  | Procesos que cruza                                                      |
|--------------------------|-------------------------------------------------------------------------|
| Desempeño del personal   | Registración de pedidos + Asignación de personal + Empezamos/Terminamos |
| Uso e ingresos de la flota | Registración de pedidos + Anulación + Relevamiento (recargos)         |
| Cambios y cancelaciones  | Registración de pedidos + Reprogramación + Anulación                    |
"""
from collections import defaultdict
from decimal import Decimal

from django.utils import timezone

from usuarios.models import Pedido, PersonalPedido, Reprogramacion, Vehiculo

TARDE_MINUTOS = 15  # desde cuántos minutos tarde al «Empezamos» cuenta como llegada tarde


def _horas(delta):
    return delta.total_seconds() / 3600


# ------------------------------------------------------------------ 1. desempeño del personal
def desempeno_personal(desde, hasta, funcion=''):
    """Por empleado: cuántas mudanzas hizo, horas estimadas contra reales y puntualidad.
    Solo mudanzas finalizadas, con la hora real que marcó el chofer."""
    asignaciones = (PersonalPedido.objects
                    .filter(idPedido__estado=Pedido.FINALIZADO, idPedido__fecha_servicio__range=(desde, hasta))
                    .select_related('idUsuario', 'idPedido'))
    if funcion:
        asignaciones = asignaciones.filter(Funcion=funcion)

    grupos = defaultdict(lambda: {'mudanzas': 0, 'estimadas': 0.0, 'reales': 0.0, 'con_real': 0,
                                  'demoras': [], 'tarde': 0})
    for a in asignaciones:
        g = grupos[(a.idUsuario, a.Funcion)]
        p = a.idPedido
        g['mudanzas'] += 1
        if p.inicio_real and p.fin_real:
            g['con_real'] += 1
            g['estimadas'] += p.duracion_horas
            g['reales'] += _horas(p.fin_real - p.inicio_real)
            demora = (p.inicio_real - p.inicio).total_seconds() / 60
            g['demoras'].append(demora)
            g['tarde'] += demora > TARDE_MINUTOS

    filas = []
    for (u, f), g in grupos.items():
        filas.append({
            'empleado': f'{u.Apellido}, {u.Nombre}', 'funcion': dict(PersonalPedido.FUNCIONES)[f],
            'mudanzas': g['mudanzas'], 'estimadas': g['estimadas'], 'reales': g['reales'],
            'desvio': (g['reales'] / g['estimadas'] - 1) * 100 if g['estimadas'] else None,
            'demora': sum(g['demoras']) / len(g['demoras']) if g['demoras'] else None,
            'tarde': g['tarde'],
        })
    filas.sort(key=lambda f: (-f['mudanzas'], f['empleado']))

    estimadas, reales = sum(f['estimadas'] for f in filas), sum(f['reales'] for f in filas)
    todas = [d for g in grupos.values() for d in g['demoras']]
    totales = {
        'empleado': f'{len(filas)} persona{"s" if len(filas) != 1 else ""}', 'funcion': '',
        'mudanzas': sum(f['mudanzas'] for f in filas), 'estimadas': estimadas, 'reales': reales,
        'desvio': (reales / estimadas - 1) * 100 if estimadas else None,
        'demora': sum(todas) / len(todas) if todas else None, 'tarde': sum(f['tarde'] for f in filas),
    }
    return {
        'columnas': [('Empleado', 'empleado', 'texto'), ('Función', 'funcion', 'texto'),
                     ('Mudanzas', 'mudanzas', 'entero'), ('Horas estimadas', 'estimadas', 'horas'),
                     ('Horas reales', 'reales', 'horas'), ('Desvío', 'desvio', 'porcentaje'),
                     ('Demora al empezar', 'demora', 'minutos'), (f'Tarde (+{TARDE_MINUTOS} min)', 'tarde', 'entero')],
        'filas': filas, 'totales': totales, 'resumen': [],
        'nota': 'Desvío: cuánto más (o menos) duraron las mudanzas que lo estimado. Demora al empezar: '
                'minutos entre la hora pactada y el «Empezamos» del chofer. En el total, cada mudanza '
                'cuenta una vez por persona que trabajó en ella.',
    }


# ------------------------------------------------------------------ 2. uso e ingresos de la flota
def uso_flota(desde, hasta, tipo=''):
    """Por vehículo: mudanzas hechas y anuladas, horas de uso, ingresos y recargos del relevamiento."""
    pedidos = Pedido.objects.filter(fecha_servicio__range=(desde, hasta), estado__in=[Pedido.FINALIZADO, Pedido.ANULADO])
    vehiculos = Vehiculo.objects.order_by('patente')
    if tipo:
        vehiculos = vehiculos.filter(tipo_vehiculo=tipo)
        pedidos = pedidos.filter(patente_vehiculo__tipo_vehiculo=tipo)

    grupos = defaultdict(lambda: {'hechas': 0, 'anuladas': 0, 'horas': 0.0, 'ingresos': Decimal(0), 'recargos': Decimal(0)})
    for p in pedidos:
        g = grupos[p.patente_vehiculo_id]
        if p.estado == Pedido.ANULADO:
            g['anuladas'] += 1
            continue
        g['hechas'] += 1
        g['horas'] += _horas(p.fin_real - p.inicio_real) if p.inicio_real and p.fin_real else p.duracion_horas
        g['ingresos'] += p.total
        g['recargos'] += p.recargo or 0

    total_ingresos = sum((g['ingresos'] for g in grupos.values()), Decimal(0))
    filas = []
    for v in vehiculos:
        g = grupos.get(v.patente)
        if not g:
            continue
        filas.append({
            'patente': v.patente, 'vehiculo': f'{v.tipo_vehiculo} · {v.marca_modelo}',
            'hechas': g['hechas'], 'anuladas': g['anuladas'], 'horas': g['horas'],
            'ingresos': g['ingresos'], 'recargos': g['recargos'],
            'ticket': g['ingresos'] / g['hechas'] if g['hechas'] else None,
            'participacion': float(g['ingresos'] / total_ingresos * 100) if total_ingresos else None,
        })
    filas.sort(key=lambda f: -f['ingresos'])
    hechas = sum(f['hechas'] for f in filas)
    totales = {
        'patente': f'{len(filas)} vehículo{"s" if len(filas) != 1 else ""}', 'vehiculo': '',
        'hechas': hechas, 'anuladas': sum(f['anuladas'] for f in filas), 'horas': sum(f['horas'] for f in filas),
        'ingresos': total_ingresos, 'recargos': sum((f['recargos'] for f in filas), Decimal(0)),
        'ticket': total_ingresos / hechas if hechas else None, 'participacion': 100.0 if filas else None,
    }
    return {
        'columnas': [('Patente', 'patente', 'texto'), ('Vehículo', 'vehiculo', 'texto'),
                     ('Hechas', 'hechas', 'entero'), ('Anuladas', 'anuladas', 'entero'), ('Horas de uso', 'horas', 'horas'),
                     ('Ingresos', 'ingresos', 'pesos'), ('Recargos', 'recargos', 'pesos'),
                     ('Ticket promedio', 'ticket', 'pesos'), ('% de ingresos', 'participacion', 'porcentaje')],
        'filas': filas, 'totales': totales, 'resumen': [],
        'nota': 'Ingresos: total de las mudanzas finalizadas (servicios, adicionales y recargos del relevamiento). '
                'Horas de uso: las reales que marcó el chofer o, si no hay, las estimadas.',
    }


# ------------------------------------------------------------------ 3. cambios y cancelaciones
def cambios_y_cancelaciones(desde, hasta, tipo=''):
    """Cada reprogramación y cada anulación del período (por la fecha en que se hizo), con su
    motivo y quién la hizo, y un resumen por motivo."""
    eventos = []
    if tipo in ('', 'Reprogramación'):
        for r in (Reprogramacion.objects.filter(fecha_registro__date__range=(desde, hasta))
                  .select_related('idPedido__idUsuario', 'usuario')):
            eventos.append({
                'fecha': timezone.localtime(r.fecha_registro), 'tipo': 'Reprogramación', 'pedido': r.idPedido_id,
                'cliente': f'{r.idPedido.idUsuario.Apellido}, {r.idPedido.idUsuario.Nombre}',
                'cambio': f'{r.fecha_anterior:%d/%m} {r.hora_anterior:%H:%M} → {r.fecha_nueva:%d/%m} {r.hora_nueva:%H:%M}',
                'motivo': r.motivo, 'quien': f'{r.usuario.Apellido}, {r.usuario.Nombre}'})
    if tipo in ('', 'Anulación'):
        for p in (Pedido.objects.filter(estado=Pedido.ANULADO, fecha_anulacion__date__range=(desde, hasta))
                  .select_related('idUsuario', 'usuario_anulacion')):
            u = p.usuario_anulacion
            eventos.append({
                'fecha': timezone.localtime(p.fecha_anulacion), 'tipo': 'Anulación', 'pedido': p.id_pedido,
                'cliente': f'{p.idUsuario.Apellido}, {p.idUsuario.Nombre}',
                'cambio': f'Mudanza del {p.fecha_servicio:%d/%m/%Y}', 'motivo': p.motivo_anulacion or '—',
                'quien': (('el cliente' if u.pk == p.idUsuario_id else f'{u.Apellido}, {u.Nombre}') if u else '—')})
    eventos.sort(key=lambda e: e['fecha'], reverse=True)

    por_motivo = defaultdict(int)
    for e in eventos:
        por_motivo[(e['tipo'], e['motivo'])] += 1
    resumen = [{'tipo': t, 'motivo': m, 'cantidad': n, 'porcentaje': n / len(eventos) * 100}
               for (t, m), n in sorted(por_motivo.items(), key=lambda x: -x[1])]
    reprog = sum(e['tipo'] == 'Reprogramación' for e in eventos)
    totales = {'fecha': f'{len(eventos)} cambio{"s" if len(eventos) != 1 else ""}',
               'tipo': f'{reprog} reprog. · {len(eventos) - reprog} anul.',
               'pedido': '', 'cliente': '', 'cambio': '', 'motivo': '', 'quien': ''}
    return {
        'columnas': [('Fecha', 'fecha', 'fechahora'), ('Tipo', 'tipo', 'texto'), ('Pedido', 'pedido', 'texto'),
                     ('Cliente', 'cliente', 'texto'), ('Cambio', 'cambio', 'texto'), ('Motivo', 'motivo', 'texto'),
                     ('Lo hizo', 'quien', 'texto')],
        'filas': eventos, 'totales': totales, 'resumen': resumen,
        'nota': 'Las reprogramaciones se cuentan por la fecha en que se hicieron; las anulaciones, por la fecha de anulación.',
    }
