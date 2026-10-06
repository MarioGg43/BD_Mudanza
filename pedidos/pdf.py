"""Arma PDFs descargables a partir de plantillas (xhtml2pdf)."""
import io

from django.contrib.staticfiles import finders
from django.http import HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa


def _recursos(uri, rel):
    """xhtml2pdf necesita la ruta del archivo para las imágenes estáticas (el logo)."""
    if uri.startswith('/static/'):
        return finders.find(uri[len('/static/'):]) or uri
    return uri


def respuesta_pdf(request, plantilla, contexto, nombre):
    html = render_to_string(plantilla, contexto, request=request)
    salida = io.BytesIO()
    if pisa.CreatePDF(html, dest=salida, link_callback=_recursos, encoding='utf-8').err:
        raise RuntimeError('No se pudo generar el PDF')
    respuesta = HttpResponse(salida.getvalue(), content_type='application/pdf')
    respuesta['Content-Disposition'] = f'attachment; filename="{nombre}"'
    return respuesta
