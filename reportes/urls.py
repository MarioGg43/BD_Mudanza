from django.urls import path

from . import views

urlpatterns = [
    path('', views.indice, name='reportes_indice'),
    path('<str:clave>/', views.ver, name='reportes_ver'),
    path('<str:clave>/pdf/', views.pdf, name='reportes_pdf'),
]
