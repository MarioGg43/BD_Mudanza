"""Pantallas de los reportes consolidados (Parcial N° 2, M2): índice, cada reporte con filtros,
grilla paginada y totales al pie, y su PDF. Los cálculos están en consultas.py."""
from datetime import date
from urllib.parse import urlencode

from django import forms
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import redirect, render
from django.utils import timezone

from pedidos.forms import con_bootstrap, filtro_fecha
from pedidos.pdf import respuesta_pdf
from usuarios.models import PersonalPedido, Vehiculo
from usuarios.permisos import get_usuario_actual, tiene_permiso

from . import consultas

POR_PAGINA = 15

# Cada reporte: título, para qué sirve, quién lo ve, cómo se calcula y su filtro propio del dominio.
REPORTES = {
    'personal': {
        'titulo': 'Desempeño del personal', 'icono': 'bi-people',
        'descripcion': 'Mudanzas hechas por cada chofer y ayudante, horas reales contra las estimadas y puntualidad.',
        'cruza': 'Pedidos + asignación de personal + «Empezamos / Terminamos» del chofer',
        'permiso': 'REP_CONSULTAR', 'calcular': consultas.desempeno_personal,
        'filtro': ('funcion', 'Función', [('', 'Todas')] + PersonalPedido.FUNCIONES),
    },
    'flota': {
        'titulo': 'Uso e ingresos de la flota', 'icono': 'bi-truck',
        'descripcion': 'Mudanzas, horas de uso, ingresos y recargos de cada vehículo. Tiene montos: solo con permiso.',
        'cruza': 'Pedidos + anulaciones + recargos del relevamiento',
        'permiso': 'REP_FINANZAS', 'calcular': consultas.uso_flota,
        'filtro': ('tipo', 'Tipo de vehículo', [('', 'Todos')] + [(t, t) for t in Vehiculo.TIPOS]),
    },
    'cambios': {
        'titulo': 'Cambios y cancelaciones', 'icono': 'bi-arrow-repeat',
        'descripcion': 'Cada reprogramación y anulación del período con su motivo y quién la hizo, y el resumen por motivo.',
        'cruza': 'Pedidos + reprogramaciones + anulaciones',
        'permiso': 'REP_CONSULTAR', 'calcular': consultas.cambios_y_cancelaciones,
        'filtro': ('tipo', 'Tipo de cambio', [('', 'Todos'), ('Reprogramación', 'Reprogramaciones'),
                                               ('Anulación', 'Anulaciones')]),
    },
}


class FiltroReporteForm(forms.Form):
    """Rango de fechas (obligatorio por consigna) más el filtro propio de cada reporte."""
    desde = forms.DateField(label='Desde', widget=filtro_fecha())
    hasta = forms.DateField(label='Hasta', widget=filtro_fecha(no_antes_de='id_desde'))

    def __init__(self, *args, filtro, **kwargs):
        super().__init__(*args, **kwargs)
        nombre, etiqueta, opciones = filtro
        self.fields[nombre] = forms.ChoiceField(label=etiqueta, choices=opciones, required=False)
        self.extra = nombre
        con_bootstrap(self)

    def clean(self):
        d = super().clean()
        if d.get('desde') and d.get('hasta') and d['desde'] > d['hasta']:
            self.add_error('hasta', 'La fecha «Hasta» no puede ser anterior a «Desde».')
        return d


def _por_defecto():
    """Si no se eligió nada: desde el 1 de enero hasta hoy."""
    hoy = timezone.localdate()
    return {'desde': date(hoy.year, 1, 1), 'hasta': hoy}


def _preparar(request, clave):
    """El usuario con permiso, el reporte, el formulario y los datos calculados (o una respuesta)."""
    usuario = get_usuario_actual(request)
    if not usuario:
        return None, redirect('login')
    reporte = REPORTES.get(clave)
    if not reporte:
        raise Http404('Reporte inexistente')
    if not tiene_permiso(usuario, reporte['permiso']):
        return None, render(request, 'sin_permiso_accion.html', status=403)
    datos_get = request.GET.copy()
    for k, v in _por_defecto().items():
        datos_get.setdefault(k, v.isoformat())
    form = FiltroReporteForm(datos_get, filtro=reporte['filtro'])
    datos = None
    if form.is_valid():
        d = form.cleaned_data
        datos = reporte['calcular'](d['desde'], d['hasta'], d.get(form.extra) or '')
    return {'usuario': usuario, 'reporte': reporte, 'clave': clave, 'form': form, 'datos': datos}, None


def _filtros_usados(form):
    """[(etiqueta, valor)] para mostrar en el PDF y arriba de la grilla."""
    if not form.is_valid():
        return []
    usados = []
    for nombre, campo in form.fields.items():
        valor = form.cleaned_data.get(nombre)
        if valor:
            texto = valor.strftime('%d/%m/%Y') if hasattr(valor, 'strftime') else dict(campo.choices).get(valor, valor)
            usados.append((campo.label, texto))
    return usados


def indice(request):
    usuario = get_usuario_actual(request)
    if not usuario:
        return redirect('login')
    disponibles = [{'clave': k, **r} for k, r in REPORTES.items() if tiene_permiso(usuario, r['permiso'])]
    if not disponibles:
        return render(request, 'sin_permiso_accion.html', status=403)
    return render(request, 'reportes/indice.html', {'reportes': disponibles})


def ver(request, clave):
    contexto, respuesta = _preparar(request, clave)
    if respuesta:
        return respuesta
    datos = contexto['datos']
    pagina = Paginator(datos['filas'] if datos else [], POR_PAGINA).get_page(request.GET.get('pagina'))
    sin_pagina = {k: v for k, v in request.GET.items() if k != 'pagina'}
    contexto.update(pagina=pagina, filtros_usados=_filtros_usados(contexto['form']),
                    consulta=urlencode(sin_pagina))
    return render(request, 'reportes/reporte.html', contexto)


def pdf(request, clave):
    contexto, respuesta = _preparar(request, clave)
    if respuesta:
        return respuesta
    if not contexto['datos']:
        return redirect(f"{request.path.rsplit('pdf/', 1)[0]}?{request.GET.urlencode()}")
    contexto.update(filtros_usados=_filtros_usados(contexto['form']), emitido=timezone.localtime())
    nombre = contexto['reporte']['titulo'].replace(' ', '_') + '.pdf'
    return respuesta_pdf(request, 'reportes/reporte_pdf.html', contexto, nombre)
