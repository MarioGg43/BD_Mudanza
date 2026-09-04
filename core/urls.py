from django.contrib import admin
from django.urls import path, include

from flota import views as flota_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', flota_views.inicio, name='inicio'),
    path('vehiculos/', include('flota.urls')),
]
