from django.urls import path

from . import views, views_admin

# Contrato de la API (lo que consume frontend/src/services)
urlpatterns = [
    path('auth/login', views.login, name='api_login'),
    path('auth/registro', views.registro, name='api_registro'),
    path('auth/yo', views.yo, name='api_yo'),
    path('publico', views.publico_info, name='api_publico'),
    path('catalogo', views.catalogo, name='api_catalogo'),
    path('vehiculos-libres', views.vehiculos_libres, name='api_vehiculos_libres'),
    path('pedidos', views.pedidos, name='api_pedidos'),
    path('pedidos/<int:id_pedido>', views.pedido, name='api_pedido'),
    path('pedidos/<int:id_pedido>/cancelar', views.cancelar, name='api_cancelar'),
    path('pedidos/<int:id_pedido>/comprobante', views.comprobante, name='api_comprobante'),
    # administrador
    path('admin/opciones', views_admin.opciones, name='api_admin_opciones'),
    path('pedidos/<int:id_pedido>/confirmar', views_admin.confirmar, name='api_confirmar'),
    path('pedidos/<int:id_pedido>/finalizar', views_admin.finalizar, name='api_finalizar'),
    path('pedidos/<int:id_pedido>/anular', views_admin.anular, name='api_anular'),
    path('pedidos/<int:id_pedido>/personal', views_admin.personal, name='api_personal'),
    path('pedidos/<int:id_pedido>/servicios', views_admin.servicios, name='api_servicios'),
    path('pedidos/<int:id_pedido>/reprogramar', views_admin.reprogramar, name='api_reprogramar'),
]
