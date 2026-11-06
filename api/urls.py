from django.urls import path

from . import views, views_abm, views_admin, views_auditoria, views_portal, views_usuarios

# Contrato de la API (lo que consume frontend/src/services)
urlpatterns = [
    path('auth/login', views.login, name='api_login'),
    path('auth/registro', views.registro, name='api_registro'),
    path('auth/cambiar-clave', views.cambiar_clave, name='api_cambiar_clave'),
    path('auth/recuperar-clave', views.recuperar_clave, name='api_recuperar_clave'),
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
    # ABM
    path('vehiculos', views_abm.vehiculos, name='api_vehiculos'),
    path('vehiculos/<str:patente>', views_abm.vehiculo, name='api_vehiculo'),
    path('vehiculos/<str:patente>/baja', views_abm.baja_vehiculo, name='api_baja_vehiculo'),
    path('servicios', views_abm.servicios, name='api_servicios_abm'),
    path('servicios/<int:id_servicio>', views_abm.servicio, name='api_servicio'),
    path('servicios/<int:id_servicio>/baja', views_abm.baja_servicio, name='api_baja_servicio'),
    path('objetos', views_abm.objetos, name='api_objetos'),
    path('objetos/<int:id_objeto>', views_abm.objeto, name='api_objeto'),
    path('objetos/<int:id_objeto>/baja', views_abm.baja_objeto, name='api_baja_objeto'),
    path('usuarios', views_usuarios.usuarios, name='api_usuarios'),
    path('usuarios/nombre', views_usuarios.nombre_usuario, name='api_nombre_usuario'),
    path('usuarios/<int:dni>/correo', views_usuarios.correo, name='api_usuario_correo'),
    path('usuarios/<int:dni>/rol', views_usuarios.rol_de_usuario, name='api_usuario_rol'),
    path('usuarios/<int:dni>/baja', views_usuarios.baja_usuario, name='api_usuario_baja'),
    path('usuarios/<int:dni>/reactivar', views_usuarios.reactivar_usuario, name='api_usuario_reactivar'),
    path('usuarios/<int:dni>/clave', views_usuarios.clave, name='api_usuario_clave'),
    path('roles', views_usuarios.roles, name='api_roles'),
    path('roles/<int:id_rol>', views_usuarios.rol, name='api_rol'),
    path('auditoria', views_auditoria.auditoria, name='api_auditoria'),
    path('auditoria/opciones', views_auditoria.opciones, name='api_auditoria_opciones'),
    path('auditoria/pdf', views_auditoria.pdf, name='api_auditoria_pdf'),
    # portal del personal
    path('portal', views_portal.portal, name='api_portal'),
    path('portal/<int:id_pedido>/empezar', views_portal.empezar, name='api_empezar'),
    path('portal/<int:id_pedido>/terminar', views_portal.terminar, name='api_terminar'),
    path('portal/<int:id_pedido>/relevamiento', views_portal.relevamiento, name='api_relevamiento'),
]
