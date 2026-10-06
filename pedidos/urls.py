from django.urls import path

from . import views

urlpatterns = [
    path('pedidos/', views.lista, name='pedidos_lista'),
    path('pedidos/nuevo/', views.nuevo, name='pedidos_nuevo'),
    path('pedidos/vehiculos-libres/', views.vehiculos_libres, name='pedidos_vehiculos_libres'),
    path('pedidos/<int:id_pedido>/', views.detalle, name='pedidos_detalle'),
    path('pedidos/<int:id_pedido>/confirmar/', views.confirmar, name='pedidos_confirmar'),
    path('pedidos/<int:id_pedido>/finalizar/', views.finalizar, name='pedidos_finalizar'),
    path('pedidos/<int:id_pedido>/anular/', views.anular, name='pedidos_anular'),
]
