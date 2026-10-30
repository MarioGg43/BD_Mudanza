from django.urls import path

from . import views, views_objetos, views_servicios

urlpatterns = [
    path('registro/', views.registro, name='registro_cliente'),
    path('pedidos/', views.lista, name='pedidos_lista'),
    path('pedidos/nuevo/', views.nuevo, name='pedidos_nuevo'),
    path('pedidos/descargar/', views.descargar, name='pedidos_descargar'),
    path('pedidos/vehiculos-libres/', views.vehiculos_libres, name='pedidos_vehiculos_libres'),
    path('pedidos/<int:id_pedido>/', views.detalle, name='pedidos_detalle'),
    path('pedidos/<int:id_pedido>/confirmar/', views.confirmar, name='pedidos_confirmar'),
    path('pedidos/<int:id_pedido>/finalizar/', views.finalizar, name='pedidos_finalizar'),
    path('pedidos/<int:id_pedido>/anular/', views.anular, name='pedidos_anular'),
    path('pedidos/<int:id_pedido>/asignar/', views.asignar, name='pedidos_asignar'),
    path('pedidos/<int:id_pedido>/reprogramar/', views.reprogramar, name='pedidos_reprogramar'),
    path('pedidos/<int:id_pedido>/empezar/', views.empezar, name='pedidos_empezar'),
    path('pedidos/<int:id_pedido>/terminar/', views.terminar, name='pedidos_terminar'),
    path('pedidos/<int:id_pedido>/comprobante/', views.comprobante, name='pedidos_comprobante'),
    path('pedidos/<int:id_pedido>/comprobante/pdf/', views.comprobante_pdf, name='pedidos_comprobante_pdf'),
    path('servicios/', views_servicios.lista, name='servicios_lista'),
    path('servicios/nuevo/', views_servicios.crear, name='servicios_crear'),
    path('servicios/<int:id_servicio>/editar/', views_servicios.editar, name='servicios_editar'),
    path('servicios/<int:id_servicio>/baja/', views_servicios.baja, name='servicios_baja'),
    path('objetos/', views_objetos.lista, name='objetos_lista'),
    path('objetos/nuevo/', views_objetos.crear, name='objetos_crear'),
    path('objetos/<int:id_objeto>/editar/', views_objetos.editar, name='objetos_editar'),
    path('objetos/<int:id_objeto>/baja/', views_objetos.baja, name='objetos_baja'),
]
