from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST

from .models import Vehiculo
from .forms import VehiculoForm


def inicio(request):
    """Página de bienvenida del sistema."""
    return render(request, 'vehiculos/inicio.html')


def listaVehiculos(request):
    """Lista todos los vehículos."""
    vehiculos = Vehiculo.objects.all().order_by('patente')
    return render(request, 'vehiculos/lista_vehiculos.html', {'vehiculos': vehiculos})


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


def editarVehiculo(request, id_vehiculo):
    """Edita un vehículo existente."""
    vehiculo = get_object_or_404(Vehiculo, pk=id_vehiculo)

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


@require_POST
def eliminarVehiculo(request, id_vehiculo):
    """Elimina un vehículo. Solo acepta POST."""
    vehiculo = get_object_or_404(Vehiculo, pk=id_vehiculo)
    patente = vehiculo.patente
    vehiculo.delete()
    messages.success(request, f'El vehículo "{patente}" fue eliminado.')
    return redirect('lista_vehiculos')
