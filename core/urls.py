from django.contrib import admin
from django.urls import path, include

from vehiculos import views as vehiculos_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', vehiculos_views.inicio, name='inicio'),
    path('vehiculos/', include('vehiculos.urls')),
]
