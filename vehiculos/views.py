from functools import wraps

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.views.decorators.http import require_POST

from usuarios.models import Vehiculo
from usuarios.views import get_usuario_actual
from .forms import VehiculoForm


def solo_admin_pagina(vista):
    """Igual que solo_admin del panel, pero para pantallas: sin sesión manda
    al login y si el rol no es Administrador responde 403."""
    @wraps(vista)
    def envoltura(request, *args, **kwargs):
        actual = get_usuario_actual(request)
        if not actual:
            return redirect('login')
        if actual.idRol.nom_rol.lower() != 'administrador':
            return HttpResponseForbidden('Se requiere el rol Administrador.')
        return vista(request, *args, **kwargs)
    return envoltura


def inicio(request):
    """Página de bienvenida del sistema."""
    return render(request, 'vehiculos/inicio.html')


@solo_admin_pagina
def listaVehiculos(request):
    """Lista todos los vehículos."""
    vehiculos = Vehiculo.objects.select_related('chofer_asignado').order_by('patente')
    return render(request, 'vehiculos/lista_vehiculos.html', {'vehiculos': vehiculos})


@solo_admin_pagina
def createVehiculo(request):
    if request.method == 'POST':
        form = VehiculoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Vehículo registrado con éxito!')
            return redirect('lista_vehiculos')
        else:
            messages.error(request, 'Por favor, revise los errores.')
    else:
        form = VehiculoForm()

    return render(request, 'vehiculos/create_vehiculo.html', {'form': form})


@solo_admin_pagina
def editarVehiculo(request, patente):
    """Edita un vehículo existente. La patente es la clave y no se modifica."""
    vehiculo = get_object_or_404(Vehiculo, pk=patente)

    if request.method == 'POST':
        form = VehiculoForm(request.POST, instance=vehiculo)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Vehículo actualizado con éxito!')
            return redirect('lista_vehiculos')
        else:
            messages.error(request, 'Por favor, revise los errores.')
    else:
        form = VehiculoForm(instance=vehiculo)

    return render(request, 'vehiculos/edit_vehiculo.html', {'form': form, 'vehiculo': vehiculo})


@solo_admin_pagina
@require_POST
def bajaVehiculo(request, patente):
    """Baja lógica: el vehículo queda 'Fuera de Servicio' y conserva su historial
    (PEDIDOS lo referencia, por eso no se borra). Se reactiva editando el estado."""
    vehiculo = get_object_or_404(Vehiculo, pk=patente)
    vehiculo.estado = 'Fuera de Servicio'
    vehiculo.save(update_fields=['estado'])
    messages.success(request, f'El vehículo "{vehiculo.patente}" quedó fuera de servicio.')
    return redirect('lista_vehiculos')
