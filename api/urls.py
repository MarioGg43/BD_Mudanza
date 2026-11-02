from django.urls import path

from . import views

# Contrato de la API (lo que consume frontend/src/services)
urlpatterns = [
    path('auth/login', views.login, name='api_login'),
    path('auth/registro', views.registro, name='api_registro'),
    path('auth/yo', views.yo, name='api_yo'),
    path('catalogo', views.catalogo, name='api_catalogo'),
    path('vehiculos-libres', views.vehiculos_libres, name='api_vehiculos_libres'),
    path('pedidos', views.pedidos, name='api_pedidos'),
    path('pedidos/<int:id_pedido>', views.pedido, name='api_pedido'),
    path('pedidos/<int:id_pedido>/cancelar', views.cancelar, name='api_cancelar'),
    path('pedidos/<int:id_pedido>/comprobante', views.comprobante, name='api_comprobante'),
]
