from django.urls import path
from . import views

urlpatterns = [
    path('panel/', views.admin_dashboard, name='admin_dashboard'),
    path('portal/', views.usuario_portal, name='usuario_portal'),
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

]

