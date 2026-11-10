"""ABM de servicios: la tabla maestra que el pedido necesita y no se hizo en hitos anteriores."""
from django.contrib import messages
from django.db import transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from usuarios.models import Servicio
from .forms import MaterialesServicioFormSet, ServicioForm
from .permisos import requiere_permiso


@requiere_permiso('SRV_GESTIONAR')
def lista(request):
    servicios = (Servicio.objects.prefetch_related('recursos__idMaterial')
                 .annotate(cant_pedidos=Count('detalles__idPedido', distinct=True))
                 .order_by('-Activo', '-Categoria', 'Tipo_servicio'))
    return render(request, 'pedidos/servicios_lista.html', {'servicios': servicios})


def _formulario(request, servicio, titulo):
    """El servicio y, debajo, sus materiales con la cantidad que se sugiere llevar por mudanza."""
    datos = request.POST if request.method == 'POST' else None
    form = ServicioForm(datos, instance=servicio, initial=None if servicio.pk else {'Activo': True})
    materiales = MaterialesServicioFormSet(datos, instance=servicio, prefix='materiales')
    if datos is not None and form.is_valid() and materiales.is_valid():
        with transaction.atomic():
            servicio = form.save()
            materiales.instance = servicio
            materiales.save()
        messages.success(request, f'Servicio «{servicio.Tipo_servicio}» guardado.')
        return redirect('servicios_lista')
    return render(request, 'pedidos/servicio_form.html', {'form': form, 'materiales': materiales, 'titulo': titulo})


@requiere_permiso('SRV_GESTIONAR')
def crear(request):
    return _formulario(request, Servicio(), 'Nuevo servicio')


@requiere_permiso('SRV_GESTIONAR')
def editar(request, id_servicio):
    servicio = get_object_or_404(Servicio, pk=id_servicio)
    return _formulario(request, servicio, f'Editar «{servicio.Tipo_servicio}»')


@requiere_permiso('SRV_GESTIONAR')
@require_POST
def baja(request, id_servicio):
    """Baja lógica: deja de ofrecerse, pero los pedidos que ya lo tienen lo conservan."""
    servicio = get_object_or_404(Servicio, pk=id_servicio)
    servicio.Activo = False
    servicio.save(update_fields=['Activo'])
    messages.success(request, f'Servicio «{servicio.Tipo_servicio}» dado de baja. Se reactiva editándolo.')
    return redirect('servicios_lista')
