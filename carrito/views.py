from datetime import datetime, timedelta
import uuid
from venv import logger
from django.conf import settings
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponseRedirect
from gt_store.models import Product
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import  ProductoPedido
from .forms import PedidoForm
from usuarios.models import  PerfilUsuario
from transbank.webpay.webpay_plus.transaction import Transaction, WebpayOptions
from transbank.common.integration_type import IntegrationType

class Carrito:
    def __init__(self, request):
        self.request = request
        self.session = request.session
        carrito = self.session.get("carrito")
        if not carrito:
            self.session["carrito"] = {}
            self.carrito = self.session["carrito"]
        else:
            self.carrito = carrito

    def agregar(self, producto):
        id = str(producto.id_producto)
        if id not in self.carrito.keys():
            self.carrito[id] = {
                "producto_id": producto.id_producto,
                "imagen": producto.imagen.url,
                "nombre": producto.nombre_producto,
                "stock": producto.stock,
                "acumulado_transferencia": producto.precio_transferencia,
                "acumulado_normal": producto.precio_normal,
                "cantidad": 1,
            }
        else:
            self.carrito[id]["cantidad"] += 1
            self.carrito[id]["acumulado_transferencia"] += producto.precio_transferencia
            self.carrito[id]["acumulado_normal"] += producto.precio_normal

        self.guardar_carrito()

    def guardar_carrito(self):
        self.session["carrito"] = self.carrito
        self.session.modified = True

    def eliminar(self, producto):
        id = str(producto.id_producto)
        if id in self.carrito:
            del self.carrito[id]
            self.guardar_carrito()

    def restar(self, producto):
        id = str(producto.id_producto)
        if id in self.carrito.keys():
            self.carrito[id]["cantidad"] -= 1
            self.carrito[id]["acumulado_transferencia"] -= producto.precio_transferencia
            self.carrito[id]["acumulado_normal"] -= producto.precio_normal
            if self.carrito[id]["cantidad"] <= 0:
                self.eliminar(producto)
            self.guardar_carrito()

    def limpiar(self):
        self.session["carrito"] = {}
        self.session.modified = True

def tienda(request):
    productos = Product.objects.all()
    return render(request, "GatoTech/index.html", {'productos': productos})

def agregar_producto(request, id_producto):
    carrito = Carrito(request)
    producto = get_object_or_404(Product, id_producto=id_producto)
    carrito.agregar(producto)
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

def eliminar_producto(request, id_producto):
    carrito = Carrito(request)
    producto = get_object_or_404(Product, id_producto=id_producto)
    carrito.eliminar(producto)
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

def restar_producto(request, id_producto):
    carrito = Carrito(request)
    producto = get_object_or_404(Product, id_producto=id_producto)
    carrito.restar(producto)
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

def limpiar_carrito(request):
    carrito = Carrito(request)
    carrito.limpiar()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

def carrito(request):
    return render(request, 'carrito/carrito.html')

#Compra

def datos_usuario_compra(request):
    carrito = request.session.get('carrito', {})
    if not carrito:
        return redirect('carrito')

    if request.method == 'POST':
        form = PedidoForm(request.POST)
        if form.is_valid():
            # Guardar datos en sesión para usar después del pago
            request.session['datos_compra'] = form.cleaned_data
            return redirect('iniciar_pago_webpay')
    else:
        initial = {}
        if request.user.is_authenticated:
            try:
                # Usando email como campo de relación
                perfil = PerfilUsuario.objects.get(email=request.user.email)
                initial = {
                    'nombre_usuario': perfil.nombre,
                    'apellido_usuario': perfil.apellido,
                    'telefono_usuario': perfil.telefono,
                    'email_usuario': perfil.email,
                    'rut_usuario': perfil.rut
                }
            except PerfilUsuario.DoesNotExist:
                pass
        
        form = PedidoForm(initial=initial)

    return render(request, 'carrito/continuacion_compra.html', {
        'form': form,
        'total_normal': sum(item['acumulado_normal'] for item in carrito.values()),
        'total_transferencia': sum(item['acumulado_transferencia'] for item in carrito.values())
    })
#Pedido realizado
def pago_exitoso (request):
    return render(request, 'carrito/resultado.html')


def iniciar_pago_webpay(request):
    carrito = request.session.get('carrito', {})
    if not carrito:
        messages.error(request, "No hay productos en el carrito")
        return redirect('carrito')

    total = sum(float(item['acumulado_normal']) for item in carrito.values())
    
    total = int(round(total))
    
    if total <= 0:
        messages.error(request, "El monto total debe ser mayor a cero")
        return redirect('datos_usuario_compra')

    tx = Transaction(WebpayOptions(
        commerce_code=settings.TRANSBANK["commerce_code"],
        api_key=settings.TRANSBANK["api_key"],
        integration_type=IntegrationType.TEST
    ))

    buy_order = str(int(datetime.now().timestamp()))[:26]
    session_id = request.session.session_key or "sess_" + str(uuid.uuid4())[:8]
    return_url = request.build_absolute_uri('/carrito/webpay/respuesta/')

    try:
        response = tx.create(buy_order=buy_order, session_id=session_id, amount=total, return_url=return_url)
        token = getattr(response, 'token', response.get('token'))
        url = getattr(response, 'url', response.get('url'))

        if not token or not url:
            raise ValueError("Respuesta de WebPay incompleta")

        request.session['webpay_data'] = {
            'token': token,
            'buy_order': buy_order,
            'amount': total,
            'session_id': session_id
        }
        
        # Guardar también los datos del carrito para después del pago
        request.session['carrito_para_pago'] = carrito
        
        return redirect(f"{url}?token_ws={token}")

    except Exception as e:
        logger.error(f"Error al iniciar pago WebPay: {str(e)}", exc_info=True)
        messages.error(request, f"Error al iniciar el pago: {str(e)}")
        return redirect('datos_usuario_compra')

# Procesa la respuesta de WebPay después del pago

def webpay_respuesta(request):
    token = request.GET.get("token_ws")
    if not token:
        return render(request, "carrito/resultado.html", {"error": "Token no proporcionado"})

    try:
        tx = Transaction(WebpayOptions(
            commerce_code=settings.TRANSBANK["commerce_code"],
            api_key=settings.TRANSBANK["api_key"],
            integration_type=IntegrationType.TEST
        ))
        
        commit_response = tx.commit(token)
        
        if commit_response.response_code == 0:
            # Pago exitoso
            datos_compra = request.session.get('datos_compra', {})
            carrito = request.session.get('carrito_para_pago', {})
            
            # Crear pedido
            form = PedidoForm(datos_compra)
            if form.is_valid():
                pedido = form.save(commit=False)
                pedido.total_normal = sum(float(item['acumulado_normal']) for item in carrito.values())
                pedido.total_transferencia = sum(float(item['acumulado_transferencia']) for item in carrito.values())
                pedido.save()

                for item in carrito.values():
                    producto = Product.objects.get(id_producto=item['producto_id'])
                    ProductoPedido.objects.create(
                        pedido=pedido,
                        producto=producto,
                        cantidad=item['cantidad'],
                        precio=item['acumulado_normal']
                    )
                    producto.stock -= item['cantidad']
                    producto.save()

            # Limpiar sesiones
            for key in ['carrito', 'carrito_para_pago', 'datos_compra', 'webpay_data']:
                if key in request.session:
                    del request.session[key]
            
            return redirect('pago_exitoso')
        else:
            error_msg = f"Transbank rechazó el pago. Código: {commit_response.response_code}"
            return render(request, "carrito/resultado.html", {"error": error_msg})
            
    except Exception as e:
        logger.error(f"Error en webpay_respuesta: {str(e)}")
        return render(request, "carrito/resultado.html", {"error": "Error al procesar el pago"})