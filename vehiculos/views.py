from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST

from pedidos.reglas import tiene_pedidos_activos
from usuarios.models import Servicio, Vehiculo
from usuarios.permisos import get_usuario_actual, pantalla_inicio, requiere_permiso
from .forms import VehiculoForm


def inicio(request):
    """Portada para visitantes. Con sesión iniciada, cada uno va a su pantalla
    (el cliente a sus pedidos, el administrador al panel, el personal al portal)."""
    actual = get_usuario_actual(request)
    if actual:
        return pantalla_inicio(actual)
    servicios = Servicio.objects.filter(Activo=True).prefetch_related('recursos').order_by('Precio_base')
    return render(request, 'vehiculos/inicio.html', {'servicios': servicios})


@requiere_permiso('VEH_GESTIONAR')
def listaVehiculos(request):
    """Lista todos los vehículos."""
    vehiculos = Vehiculo.objects.select_related('chofer_asignado').order_by('patente')
    return render(request, 'vehiculos/lista_vehiculos.html', {'vehiculos': vehiculos})


@requiere_permiso('VEH_GESTIONAR')
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


@requiere_permiso('VEH_GESTIONAR')
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


@requiere_permiso('VEH_GESTIONAR')
@require_POST
def bajaVehiculo(request, patente):
    """Baja lógica: el vehículo queda 'Fuera de Servicio' y conserva su historial
    (PEDIDOS lo referencia, por eso no se borra). Se reactiva editando el estado."""
    vehiculo = get_object_or_404(Vehiculo, pk=patente)
    if tiene_pedidos_activos(patente_vehiculo=vehiculo):
        messages.error(request, f'El vehículo "{vehiculo.patente}" tiene pedidos pendientes o confirmados. '
                                'Anulalos o reasignalos antes de darlo de baja.')
        return redirect('lista_vehiculos')
    vehiculo.estado = 'Fuera de Servicio'
    vehiculo.save(update_fields=['estado'])
    messages.success(request, f'El vehículo "{vehiculo.patente}" quedó fuera de servicio.')
    return redirect('lista_vehiculos')
