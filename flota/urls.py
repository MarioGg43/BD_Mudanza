from django.urls import path
from . import views

urlpatterns = [
    path('', views.listaVehiculos, name='lista_vehiculos'),
    path('crear/', views.createVehiculo, name='createVehiculo'),
    path('editar/<int:id_vehiculo>/', views.editarVehiculo, name='editarVehiculo'),
    path('eliminar/<int:id_vehiculo>/', views.eliminarVehiculo, name='eliminarVehiculo'),
]
