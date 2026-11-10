"""Control de materiales: el catálogo con su stock, los movimientos y la carga de compras y ajustes.

El stock nunca se escribe a mano: cada cambio es un movimiento (ver pedidos/materiales.py).
"""
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from usuarios.models import Material, MovimientoMaterial
from . import materiales as reglas_mat
from .forms import MaterialForm, MovimientoMaterialForm
from .permisos import requiere_permiso


@requiere_permiso('MAT_GESTIONAR')
def lista(request):
    en_uso = reglas_mat.en_uso()
    todos = list(Material.objects.annotate(cant_servicios=Count('servicios', filter=Q(servicios__idServicio__Activo=True)))
                 .order_by('-Activo', 'nom_material'))
    for m in todos:
        m.en_uso = en_uso.get(m.pk, 0)
        m.porcentaje = min(100, round(m.stock_material * 100 / (m.stock_min_material * 2))) if m.stock_min_material else 100
    ver = request.GET.get('ver', '')
    materiales = [m for m in todos if m.Activo and m.bajo_minimo] if ver == 'bajo' else todos
    inicio_mes = timezone.localdate().replace(day=1)
    return render(request, 'pedidos/materiales_lista.html', {
        'materiales': materiales, 'ver': ver,
        'cant_activos': sum(1 for m in todos if m.Activo),
        'cant_bajo': sum(1 for m in todos if m.Activo and m.bajo_minimo),
        'cant_en_uso': sum(en_uso.values()),
        'movs_mes': MovimientoMaterial.objects.filter(fec_mov__date__gte=inicio_mes).count(),
        'ultimos': MovimientoMaterial.objects.select_related('idMaterial', 'idUsuario', 'idPedido').order_by('-fec_mov', '-pk')[:8],
    })


@requiere_permiso('MAT_GESTIONAR')
def crear(request):
    form = MaterialForm(request.POST or None, initial={'Activo': True, 'unidad_material': 'unidades'})
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            material = form.save()
            inicial = form.cleaned_data.get('stock_inicial') or 0
            if inicial:
                reglas_mat.registrar_ingreso(material, inicial, request.usuario, 'Stock inicial')
        messages.success(request, f'Material «{material}» agregado.')
        return redirect('materiales_detalle', id_material=material.pk)
    return render(request, 'pedidos/material_form.html', {'form': form, 'titulo': 'Nuevo material'})


@requiere_permiso('MAT_GESTIONAR')
def editar(request, id_material):
    material = get_object_or_404(Material, pk=id_material)
    form = MaterialForm(request.POST or None, instance=material)
    if request.method == 'POST' and form.is_valid():
        form.save()
        reglas_mat._revisar_minimos([material])  # si subió el mínimo, puede quedar por debajo
        messages.success(request, f'Material «{material}» actualizado.')
        return redirect('materiales_detalle', id_material=material.pk)
    return render(request, 'pedidos/material_form.html', {'form': form, 'material': material,
                                                          'titulo': f'Editar «{material}»'})


@requiere_permiso('MAT_GESTIONAR')
def detalle(request, id_material):
    """La ficha del material: stock, en qué servicios va y todos sus movimientos. Desde acá se
    carga una compra o un ajuste."""
    material = get_object_or_404(Material, pk=id_material)
    form = MovimientoMaterialForm(request.POST or None, initial={'tipo': request.GET.get('tipo', 'Ingreso')})
    if request.method == 'POST' and form.is_valid():
        d = form.cleaned_data
        try:
            if d['tipo'] == 'Ingreso':
                if d['cantidad'] <= 0:
                    raise reglas_mat.ErrorMaterial('En un ingreso la cantidad tiene que ser mayor a 0.')
                reglas_mat.registrar_ingreso(material, d['cantidad'], request.usuario, d['observacion'])
                messages.success(request, f'Ingresaron {d["cantidad"]} {material.unidad_material} de {material}.')
            else:
                reglas_mat.registrar_ajuste(material, d['cantidad'], request.usuario, d['observacion'])
                messages.success(request, f'Ajuste registrado: el stock de {material} quedó en {material.stock_material}.')
        except reglas_mat.ErrorMaterial as e:
            form.add_error(None, str(e))
        else:
            return redirect('materiales_detalle', id_material=material.pk)
    movimientos = Paginator(material.movimientos.select_related('idUsuario', 'idPedido').order_by('-fec_mov', '-pk'), 25)
    return render(request, 'pedidos/material_detalle.html', {
        'material': material, 'form': form,
        'en_uso': reglas_mat.en_uso().get(material.pk, 0),
        'servicios': material.servicios.select_related('idServicio').order_by('idServicio__Tipo_servicio'),
        'pagina': movimientos.get_page(request.GET.get('pagina')),
    })


@requiere_permiso('MAT_GESTIONAR')
@require_POST
def baja(request, id_material):
    """Baja lógica: deja de sugerirse en las mudanzas, pero su historial queda."""
    material = get_object_or_404(Material, pk=id_material)
    material.Activo = False
    material.save(update_fields=['Activo'])
    messages.success(request, f'Material «{material}» dado de baja. Ya no sale en las mudanzas; se reactiva editándolo.')
    return redirect('materiales_lista')
