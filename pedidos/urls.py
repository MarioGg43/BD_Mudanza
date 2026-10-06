from django.urls import path

from . import views

urlpatterns = [
    path('pedidos/', views.lista, name='pedidos_lista'),
    path('pedidos/<int:id_pedido>/', views.detalle, name='pedidos_detalle'),
]
