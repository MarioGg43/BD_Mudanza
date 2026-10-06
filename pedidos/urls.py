from django.urls import path

from . import views

urlpatterns = [
    path('pedidos/', views.lista, name='pedidos_lista'),
    path('pedidos/nuevo/', views.nuevo, name='pedidos_nuevo'),
    path('pedidos/vehiculos-libres/', views.vehiculos_libres, name='pedidos_vehiculos_libres'),
    path('pedidos/<int:id_pedido>/', views.detalle, name='pedidos_detalle'),
]
