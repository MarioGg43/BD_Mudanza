"""ABM de servicios: la tabla maestra que el pedido necesita y no se hizo en hitos anteriores."""
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from usuarios.models import Servicio
from .forms import ServicioForm
from .permisos import requiere_permiso


@requiere_permiso('SRV_GESTIONAR')
def lista(request):
    servicios = Servicio.objects.prefetch_related('recursos').order_by('-Activo', 'Tipo_servicio')
    return render(request, 'pedidos/servicios_lista.html', {'servicios': servicios})


@requiere_permiso('SRV_GESTIONAR')
def crear(request):
    form = ServicioForm(request.POST or None, initial={'Activo': True})
    if request.method == 'POST' and form.is_valid():
        servicio = form.save()
        messages.success(request, f'Servicio «{servicio.Tipo_servicio}» creado.')
        return redirect('servicios_lista')
    return render(request, 'pedidos/servicio_form.html', {'form': form, 'titulo': 'Nuevo servicio'})


@requiere_permiso('SRV_GESTIONAR')
def editar(request, id_servicio):
    servicio = get_object_or_404(Servicio, pk=id_servicio)
    form = ServicioForm(request.POST or None, instance=servicio)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Servicio «{servicio.Tipo_servicio}» actualizado.')
        return redirect('servicios_lista')
    return render(request, 'pedidos/servicio_form.html', {'form': form, 'titulo': f'Editar «{servicio.Tipo_servicio}»'})


@requiere_permiso('SRV_GESTIONAR')
@require_POST
def baja(request, id_servicio):
    """Baja lógica: deja de ofrecerse, pero los pedidos que ya lo tienen lo conservan."""
    servicio = get_object_or_404(Servicio, pk=id_servicio)
    servicio.Activo = False
    servicio.save(update_fields=['Activo'])
    messages.success(request, f'Servicio «{servicio.Tipo_servicio}» dado de baja. Se reactiva editándolo.')
    return redirect('servicios_lista')
