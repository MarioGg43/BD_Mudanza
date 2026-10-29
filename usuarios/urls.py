from django.urls import path
from . import roles, views, views_auditoria

urlpatterns = [
    path('panel/', views.admin_dashboard, name='admin_dashboard'),
    path('portal/', views.usuario_portal, name='usuario_portal'),
    path('sin-permisos/', views.sin_permisos, name='sin_permisos'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('cambiar-clave-obligatoria/', views.cambiar_clave_obligatoria, name='cambiar_clave_obligatoria'),
    path('olvide-clave/', views.olvide_clave_view, name='olvide_clave'),

    # Operaciones CRUD Usuarios (Hito 2)
    path('usuarios/alta/', views.alta_usuario, name='alta_usuario'),
    path('usuarios/<int:dni>/modificar-correo/', views.modificar_correo, name='modificar_correo'),
    path('usuarios/<int:dni>/baja/', views.baja_usuario, name='baja_usuario'),
    path('usuarios/<int:dni>/reactivar/', views.reactivar_usuario, name='reactivar_usuario'),
    path('usuarios/<int:dni>/restablecer-clave/', views.restablecer_clave, name='restablecer_clave'),
    path('usuarios/<int:dni>/cambiar-rol/', views.cambiar_rol, name='cambiar_rol'),
    path('usuarios/preview-username/', views.preview_username_view, name='preview_username'),

    path('auditoria/', views_auditoria.lista, name='auditoria_lista'),
    path('roles/', roles.lista, name='roles_lista'),
    path('roles/nuevo/', roles.crear, name='roles_crear'),
    path('roles/<int:id_rol>/editar/', roles.editar, name='roles_editar'),
    path('roles/<int:id_rol>/eliminar/', roles.eliminar, name='roles_eliminar'),


]

