"""ABM del catálogo de objetos: la lista de la que el cliente elige qué hay que llevar."""
from django.contrib import messages
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from usuarios.models import Objeto
from .forms import ObjetoForm
from .permisos import requiere_permiso


@requiere_permiso('OBJ_GESTIONAR')
def lista(request):
    objetos = Objeto.objects.annotate(usos=Count('inventarios')).order_by('-Activo', 'nom_objeto')
    return render(request, 'pedidos/objetos_lista.html', {'objetos': objetos})


@requiere_permiso('OBJ_GESTIONAR')
def crear(request):
    form = ObjetoForm(request.POST or None, initial={'Activo': True})
    if request.method == 'POST' and form.is_valid():
        objeto = form.save()
        messages.success(request, f'Objeto «{objeto}» agregado a la lista.')
        return redirect('objetos_lista')
    return render(request, 'pedidos/objeto_form.html', {'form': form, 'titulo': 'Nuevo objeto'})


@requiere_permiso('OBJ_GESTIONAR')
def editar(request, id_objeto):
    objeto = get_object_or_404(Objeto, pk=id_objeto)
    if objeto.es_otro:
        messages.error(request, '«Otro» es fijo: es la opción para lo que no está en la lista.')
        return redirect('objetos_lista')
    form = ObjetoForm(request.POST or None, instance=objeto)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Objeto «{objeto}» actualizado.')
        return redirect('objetos_lista')
    return render(request, 'pedidos/objeto_form.html', {'form': form, 'titulo': f'Editar «{objeto}»'})


@requiere_permiso('OBJ_GESTIONAR')
@require_POST
def baja(request, id_objeto):
    """Baja lógica: deja de ofrecerse, pero los pedidos que ya lo tienen lo conservan."""
    objeto = get_object_or_404(Objeto, pk=id_objeto)
    if objeto.es_otro:
        messages.error(request, '«Otro» no se puede dar de baja: es la opción para lo que no está en la lista.')
        return redirect('objetos_lista')
    objeto.Activo = False
    objeto.save(update_fields=['Activo'])
    messages.success(request, f'Objeto «{objeto}» dado de baja. Se reactiva editándolo.')
    return redirect('objetos_lista')
