from django.contrib import admin
from django.urls import path, include

from vehiculos import views as vehiculos_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', vehiculos_views.inicio, name='inicio'),
    path('vehiculos/', include('vehiculos.urls')),
    path('', include('usuarios.urls')),      # login, panel, portal y CRUD de usuarios
]
