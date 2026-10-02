from django.urls import path
from . import views

urlpatterns = [
    path('', views.listaVehiculos, name='lista_vehiculos'),
    path('crear/', views.createVehiculo, name='createVehiculo'),
    path('editar/<str:patente>/', views.editarVehiculo, name='editarVehiculo'),
    path('baja/<str:patente>/', views.bajaVehiculo, name='bajaVehiculo'),
]
