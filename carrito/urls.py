
from django.urls import path
from . import views


urlpatterns = [
    path('agregar/<int:id_producto>/', views.agregar_producto, name="Add"),
    path('eliminar/<int:id_producto>/', views.eliminar_producto, name="Del"),
    path('restar/<int:id_producto>/', views.restar_producto, name="Sub"),
    path('limpiar/', views.limpiar_carrito, name="CLS"),
    path('carrito/', views.carrito, name="carrito"),
    path('datos/', views.datos_usuario_compra, name="datos_usuario_compra"),
    path('pago-exitoso/', views.pago_exitoso, name="pago_exitoso"),  # Cambiado a nombre consistente
    path('webpay/iniciar/', views.iniciar_pago_webpay, name='iniciar_pago_webpay'),
    path('webpay/respuesta/', views.webpay_respuesta, name='webpay_respuesta'),
]