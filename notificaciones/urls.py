from django.urls import path

from . import views

urlpatterns = [
    path('', views.bandeja, name='notificaciones_bandeja'),
    path('<int:id_notificacion>/', views.abrir, name='notificaciones_abrir'),
    path('leer-todas/', views.leer_todas, name='notificaciones_leer_todas'),
    path('configuracion/', views.configuracion, name='notificaciones_configuracion'),
    path('evaluar/', views.evaluar_ahora, name='notificaciones_evaluar'),
]
