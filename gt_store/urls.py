from django.urls import path
from . import views

urlpatterns = [
        path('home/', views.index, name='home'),
        path('Equipamiento/', views.general_pc, name='general_pc'),
        path('Repuestos/', views.general_gabinete, name='general_gabinete'), 
        path('Insumos/', views.general_notebooks, name='general_notebooks'),
        path('productos/<int:id_producto>/', views.detalle_producto, name='detalle_producto'),
        path('filtrar_mouse/', views.filtrar_mouse, name='filtrar_mouse'),
        path('filtrar_teclado/', views.filtrar_teclado, name='filtrar_teclado'),
        path('filtrar_monitor/', views.filtrar_monitor, name='filtrar_monitor'),
        path('filtrar_audifonos/', views.filtrar_audifonos, name='filtrar_audifonos'),
        path('filtrar_pcs/', views.filtrar_pcs, name='filtrar_pcs'),
        path('filtrar_notebooks/', views.filtrar_notebooks, name='filtrar_notebooks'),
        path('filtrar_procesadores/', views.filtrar_procesadores, name='filtrar_procesadores'),
        path('filtrar_placas_madre/', views.filtrar_placas_madre, name='filtrar_placas_madre'),
        path('filtrar_tarjetas_video/', views.filtrar_tarjetas_video, name='filtrar_tarjetas_video'),
        path('filtrar_almacenamiento/', views.filtrar_almacenamiento, name='filtrar_almacenamiento'),
        path('filtrar_fuente_poder/', views.filtrar_fuente_poder, name='filtrar_fuente_poder'),
        path('filtrar_ram/', views.filtrar_ram, name='filtrar_ram'),
        path('filtrar_gabinete/', views.filtrar_gabinete, name='filtrar_gabinete'),
] 

