from django.contrib import admin
from django.urls import path, include

from reportes.tablero import tablero
from vehiculos import views as vehiculos_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', vehiculos_views.inicio, name='inicio'),
    path('api/', include('api.urls')),       # API REST para el frontend en React (frontend/)
    path('vehiculos/', include('vehiculos.urls')),
    path('', include('pedidos.urls')),       # Hito 3: pedidos, registro de clientes y servicios
    path('', include('usuarios.urls')),      # login, panel, portal y CRUD de usuarios
    path('tablero/', tablero, name='tablero'),     # inicio del administrador
    path('reportes/', include('reportes.urls')),  # Parcial N° 2 (M2): reportes consolidados
    path('notificaciones/', include('notificaciones.urls')),  # Parcial N° 2 (M3): alertas
]
