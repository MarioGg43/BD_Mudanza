"""Cómo se muestra cada tipo de dato en los reportes (pantalla y PDF), con formato argentino."""
from decimal import Decimal

from django import template
from django.utils import timezone

register = template.Library()


def _numero(valor, decimales):
    texto = f'{valor:,.{decimales}f}'                         # 1,234,567.89
    return texto.replace(',', 'X').replace('.', ',').replace('X', '.')  # 1.234.567,89


@register.filter
def formato(valor, tipo):
    if valor is None or valor == '':
        return '—'
    if tipo == 'pesos':
        return '$' + _numero(Decimal(valor), 2)
    if tipo == 'entero':
        return _numero(int(valor), 0)
    if tipo == 'horas':
        return _numero(float(valor), 1) + ' h'
    if tipo == 'minutos':
        return _numero(float(valor), 0) + ' min'
    if tipo == 'porcentaje':
        return _numero(float(valor), 1) + ' %'
    if tipo == 'fechahora':
        return timezone.localtime(valor).strftime('%d/%m/%Y %H:%M') if hasattr(valor, 'tzinfo') else str(valor)
    return valor


@register.filter
def dato(fila, clave):
    """fila[clave] desde la plantilla (las columnas son dinámicas)."""
    return fila.get(clave) if hasattr(fila, 'get') else None


@register.filter
def es_numero(tipo):
    return tipo in ('pesos', 'entero', 'horas', 'minutos', 'porcentaje')
