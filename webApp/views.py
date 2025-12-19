from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages

from .forms import UserRegisterForm, ReservaForm
from .models import Reserva, HorarioAtencion, Servicio, Producto, Orden, OrdenItem, Usuario

from datetime import datetime, time, date, timedelta
from django.utils import timezone
from django.utils.timezone import now
import stripe
from django.conf import settings
from django.urls import reverse
from django.http import HttpResponse
from django.contrib.auth import update_session_auth_hash
from django.http import JsonResponse


def inicio(request):
    return render(request, 'web/inicio.html')

def tienda(request):
    cargar_productos_base() 
    productos = Producto.objects.all()
    return render(request, "web/tienda.html", {"productos": productos})

def servicios(request):

    cargar_servicios_base()

    data = Servicio.objects.all()

    return render(request, "web/servicios.html", {"servicios": data})

def cargar_horarios_base():
    """Carga los horarios por defecto si la tabla está vacía"""
    if HorarioAtencion.objects.exists():
        return

    bloques = []

    # Lunes a Viernes → 10:00 a 20:00
    for dia in range(0, 5):
        for h in range(10, 21):
            bloques.append(HorarioAtencion(dia_semana=dia, hora=time(h, 0)))

    # Sábado → 11:00 a 19:00
    for h in range(11, 20):
        bloques.append(HorarioAtencion(dia_semana=5, hora=time(h, 0)))

    # Domingo → cerrado

    HorarioAtencion.objects.bulk_create(bloques)

def cargar_servicios_base():
    # Evitar duplicados
    if Servicio.objects.exists():
        return

    servicios = [
        ("Corte de cabello mujer", 12000),
        ("Corte de cabello hombre", 8000),
        ("Tinte completo", 25000),
        ("Mechas / Balayage", 45000),
        ("Peinado para evento", 20000),
        ("Hidratación capilar", 12000),
        ("Manicure clásica", 7000),
        ("Manicure permanente (gel)", 10000),
        ("Pedicure clásica", 12000),
        ("Diseño de cejas", 5000),
        ("Tintura de cejas", 6000),
        ("Limpieza facial profunda", 15000),
        ("Lifting de pestañas", 15000),
        ("Depilación cejas", 4000),
        ("Depilación labio superior", 3000),
        ("Depilación axilas", 6000),
        ("Depilación piernas completas", 14000),
    ]

    data = []
    contador = 1

    for nombre, precio in servicios:
        data.append(
            Servicio(
                nombre=nombre,
                precio=precio,
                imagen=f"servicio{contador}.jpg"
            )
        )
        contador += 1

    Servicio.objects.bulk_create(data)

def cargar_productos_base():
    if Producto.objects.exists():
        return  # Evita duplicados

    productos = [
        ("DUO REPARADOR PREMIÈRE PARA TODO TIPO DE CABELLO DAÑADO", 75990, 5),
        ("SÉRUM REPARADOR FILLER FONDAMENTAL", 47990, 2),
        ("ACEITE HIDRATANTE L'HUILE CICAGLOSS RECARGABLE", 38990, 8),
        ("Kit de Maquillaje On-the-Glow Blush Mini Duo", 28800, 0),
        ("Kit de 7 Brochas para Cara y Ojos de Viaje - Nude", 31900, 10),
        ("Kit de Cuidado de Piel Revitalizing Supreme+", 143000, 4),
        ("Kit de Cuidado Capilar Reveal Clean Hair Spark Joy", 52500, 1),
        ("Kit de Brumas Faciales Mini Mist Collection", 35600, 9),
        ("Tónico Exfoliante Glycolic Acid 7% - 100 ml", 12400, 7),
        ("Set de Contenedores Rellenables para Viaje", 6700, 6),
    ]

    data = []

    for i, (nombre, precio, stock) in enumerate(productos, start=1):
        data.append(
            Producto(
                nombre=nombre,
                precio=precio,
                stock=stock,
                descripcion="",
                imagen=f"producto{i}.jpg"
            )
        )

    Producto.objects.bulk_create(data)

def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if username == "admin" and password == "admin":
            return redirect('/admin/')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('inicio')

        messages.error(request, 'Contraseña o identificador de usuario incorrectos.')

    return render(request, 'web/login.html')

def registro(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            messages.success(request, f'Usuario {usuario.username} creado con éxito.')
            return redirect('login')
    else:
        form = UserRegisterForm()

    return render(request, 'web/registro.html', {'form': form})

@login_required
def user_logout(request):
    logout(request)
    return redirect("inicio")

@login_required
def reserva(request):
    cargar_servicios_base()
    servicios = Servicio.objects.all()
    return render(request, "web/reserva.html", {"servicios": servicios})

@login_required
def confirmar_reserva(request, servicio_id):
    servicio = get_object_or_404(Servicio, id=servicio_id)

    fecha = request.GET.get("fecha")
    hora = request.GET.get("hora")

    if not fecha or not hora:
        return redirect("horario", servicio_id)

    return render(request, "web/confirmar_reserva.html", {
        "servicio": servicio,
        "fecha": fecha,
        "hora": hora
    })

@login_required
def horario(request, servicio_id):
    cargar_horarios_base()
    servicio = get_object_or_404(Servicio, id=servicio_id)

    fecha_str = request.GET.get("fecha")
    horarios = []

    if fecha_str:
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()

        if fecha <= timezone.now().date():
            messages.error(request, "No puedes elegir una fecha pasada.")
        else:
            dia_semana = fecha.weekday()

            if dia_semana == 6:
                messages.error(request, "Cerrado los domingos.")
            else:
                bloques = HorarioAtencion.objects.filter(dia_semana=dia_semana)

                for b in bloques:
                    ocupado = Reserva.objects.filter(fecha=fecha, hora=b.hora).exists()

                    horarios.append({
                        "hora": b.hora.strftime("%H:%M"),
                        "estado": "Ocupado" if ocupado else "Disponible",
                        "disponible": not ocupado,
                    })

    return render(request, "web/horario.html", {
        "servicio": servicio,
        "fecha_seleccionada": fecha_str,
        "horarios": horarios
    })

stripe.api_key = settings.STRIPE_SECRET_KEY

@login_required
def pago_reserva(request, servicio_id):
    servicio = get_object_or_404(Servicio, id=servicio_id)

    if request.method != "POST":
        return redirect("servicios")

    fecha = request.POST.get("fecha")
    hora = request.POST.get("hora")

    stripe.api_key = settings.STRIPE_SECRET_KEY

    checkout_session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "clp",
                "unit_amount": int(servicio.precio),
                "product_data": {
                    "name": f"{servicio.nombre} – {fecha} {hora}",
                },
            },
            "quantity": 1,
        }],
        mode="payment",
        success_url=request.build_absolute_uri(
            reverse("pago_exitoso_reserva")
        ) + f"?servicio={servicio.id}&fecha={fecha}&hora={hora}",
        cancel_url=request.build_absolute_uri(
            reverse("horario", args=[servicio.id])
        ),
    )

    return redirect(checkout_session.url)

@login_required
def cancelar_reserva(request):
    messages.error(request, "El pago fue cancelado.")
    return redirect("reserva")

@login_required
def pago_exitoso_reserva(request):
    servicio_id = request.GET.get("servicio")
    fecha = request.GET.get("fecha")
    hora = request.GET.get("hora")

    # Validaciones básicas
    if not (servicio_id and fecha and hora):
        return HttpResponse("Faltan parámetros", status=400)

    # Recuperar servicio
    servicio = get_object_or_404(Servicio, id=servicio_id)

    # Guardar reserva en BD
    Reserva.objects.create(
        usuario=request.user,
        servicio=servicio,
        fecha=fecha,
        hora=hora,
    )

    # Marcar horario como ocupado
    try:
        dia_semana = datetime.strptime(fecha, "%Y-%m-%d").weekday()
        horario = HorarioAtencion.objects.get(
            dia_semana=dia_semana,
            hora=hora
        )
        horario.disponible = False
        horario.save()
    except HorarioAtencion.DoesNotExist:
        pass  # No existe horario para ese día, no pasa nada

    return render(request, "web/pago_exitoso_reserva.html", {
        "servicio": servicio,
        "fecha": fecha,
        "hora": hora
    })

@login_required
def compra(request):
    from django.contrib import messages

    # Crear carrito si no existe
    if "carrito" not in request.session:
        request.session["carrito"] = {}

    carrito = request.session["carrito"]

    # === AGREGAR PRODUCTO ===
    if "agregar" in request.GET:
        id_prod = str(request.GET.get("agregar"))

        try:
            p = Producto.objects.get(id=id_prod)
        except Producto.DoesNotExist:
            return redirect("compra")

        # No permitir agregar si no hay stock
        if p.stock <= 0:
            messages.error(request, "Este producto está agotado.")
            return redirect("compra")

        # Agregar al carrito
        if id_prod in carrito:
            # Verificar que no supere el stock disponible
            if carrito[id_prod] + 1 > p.stock:
                messages.error(request, "Ya agregaste la cantidad máxima disponible.")
                return redirect("compra")
            carrito[id_prod] += 1
        else:
            carrito[id_prod] = 1

        request.session.modified = True
        return redirect("compra")

    # === ELIMINAR PRODUCTO ===
    if "eliminar" in request.GET:
        id_prod = str(request.GET.get("eliminar"))
        if id_prod in carrito:
            del carrito[id_prod]
            request.session.modified = True
        return redirect("compra")

    # === PRODUCTOS ===
    productos = Producto.objects.all()

    # === DETALLE DEL CARRITO ===
    productos_carrito = []
    total = 0

    for id_prod, cantidad in carrito.items():
        try:
            p = Producto.objects.get(id=id_prod)
        except Producto.DoesNotExist:
            continue

        subtotal = p.precio * cantidad
        productos_carrito.append({
            "producto": p,
            "cantidad": cantidad,
            "subtotal": subtotal
        })
        total += subtotal

    # === CREAR ORDEN Y PASAR A PAGO ===
    if request.method == "POST" and productos_carrito:
        # NO VACÍES EL CARRITO AÚN
        return redirect("pago")

    return render(request, "web/compra.html", {
        "productos": productos,
        "productos_carrito": productos_carrito,
        "total": total,
    })

@login_required
def pago(request):
    stripe.api_key = settings.STRIPE_SECRET_KEY

    # Carrito de la sesión
    carrito = request.session.get("carrito", {})

    if not carrito:
        return render(request, "web/pago.html", {
            "carrito": None,
            "total": 0,
        })

    productos_carrito = []
    line_items = []
    total = 0

    # Convertir carrito en datos utilizables
    for id_prod, cantidad in carrito.items():
        producto = Producto.objects.get(id=id_prod)

        subtotal = producto.precio * cantidad
        total += subtotal

        productos_carrito.append({
            "producto": producto,
            "cantidad": cantidad,
            "subtotal": subtotal,
        })

        # Datos para Stripe Checkout
        line_items.append({
            "price_data": {
                "currency": "clp",
                "unit_amount": int(producto.precio),
                "product_data": {
                    "name": producto.nombre,
                },
            },
            "quantity": cantidad,
        })

    # Crear la sesión de pago en Stripe
    checkout_session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=line_items,
        mode='payment',
        success_url=request.build_absolute_uri(reverse("pago_exitoso")),
        cancel_url=request.build_absolute_uri(reverse("pago_cancelado")),
    )

    return render(request, "web/pago.html", {
        "productos_carrito": productos_carrito,
        "total": total,
        "checkout_session_id": checkout_session.id,
        "stripe_public_key": settings.STRIPE_PUBLIC_KEY,
    })

@login_required
def pago_cancelado(request):
    # No borramos el carrito, solo volvemos a compra
    return redirect("compra")

@login_required
def pago_exitoso(request):

    carrito = request.session.get("carrito", {})

    if not carrito:
        return render(request, "web/pago_exitoso.html")

    # 1) Crear la Orden
    orden = Orden.objects.create(usuario=request.user, total=0)

    total_final = 0

    # 2) Restar stock + crear OrdenItem
    for id_prod, cantidad in carrito.items():
        try:
            producto = Producto.objects.get(id=id_prod)

            # Descontar stock
            producto.stock = max(producto.stock - cantidad, 0)
            producto.save()

            # Crear item de la orden
            item = OrdenItem.objects.create(
                orden=orden,
                producto=producto,
                cantidad=cantidad,
                subtotal=producto.precio * cantidad
            )

            total_final += item.subtotal

        except Producto.DoesNotExist:
            continue

    # 3) Guardar total final
    orden.total = total_final
    orden.save()

    # 4) Vaciar carrito
    request.session["carrito"] = {}
    request.session.modified = True

    return render(request, "web/pago_exitoso.html")

@login_required
def mi_perfil(request):
    usuario = request.user

    # Todas las órdenes del usuario
    compras = Orden.objects.filter(usuario=usuario).order_by("-fecha")

    # Todos los productos comprados por el usuario
    items = OrdenItem.objects.filter(orden__usuario=usuario)

    # Última reserva del usuario (si existe)
    reserva = Reserva.objects.filter(usuario=usuario).order_by("-fecha").first()

    return render(request, "web/miperfil.html", {
        "usuario": usuario,
        "compras": compras,
        "items": items,
        "reserva": reserva,
    })

@login_required
def editar_perfil(request):
    if request.method == "POST":
        user = request.user
        user.username = request.POST.get("username")
        user.telefono = request.POST.get("telefono")
        user.email = request.POST.get("email")
        user.save()
        return redirect("mi_perfil")

    return render(request, "web/editar_perfil.html")

@login_required
def cambiar_contrasena(request):
    if request.method == "POST":
        actual = request.POST.get("actual")
        nueva = request.POST.get("nueva")
        repetir = request.POST.get("repetir")

        # Verificar contraseña actual
        if not request.user.check_password(actual):
            messages.error(request, "La contraseña actual no es correcta.")
            return redirect("cambiar_contrasena")

        # Validar que coincidan
        if nueva != repetir:
            messages.error(request, "Las contraseñas no coinciden.")
            return redirect("cambiar_contrasena")

        # Cambiar contraseña
        request.user.set_password(nueva)
        request.user.save()

        # Mantener sesión activa
        update_session_auth_hash(request, request.user)

        messages.success(request, "Tu contraseña ha sido cambiada exitosamente.")
        return redirect("mi_perfil")

    return render(request, "web/cambiar_contrasena.html")

@staff_member_required
def admin_productos(request):
    productos = Producto.objects.all().order_by("id")
    compras = Orden.objects.all().order_by("-fecha")
    return render(request, "web/admin_productos.html", {
        "productos": productos,
        "compras": compras,
    })

@staff_member_required
def admin_producto_crear(request):
    if request.method == "POST":
        nombre = request.POST.get("nombre")
        descripcion = request.POST.get("descripcion")
        precio = request.POST.get("precio")
        stock = request.POST.get("stock")
        imagen = request.POST.get("imagen")  # opcional o texto

        Producto.objects.create(
            nombre=nombre,
            descripcion=descripcion,
            precio=precio,
            stock=stock,
            imagen=imagen
        )
        return redirect("admin_productos")

    return render(request, "web/admin_producto_form.html", {
        "modo": "crear"
    })

@staff_member_required
def admin_producto_editar(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)

    if request.method == "POST":
        producto.nombre = request.POST.get("nombre")
        producto.descripcion = request.POST.get("descripcion")
        producto.precio = request.POST.get("precio")
        producto.stock = request.POST.get("stock")
        producto.imagen = request.POST.get("imagen")
        producto.save()
        return redirect("admin_productos")

    return render(request, "web/admin_producto_form.html", {
        "modo": "editar",
        "producto": producto
    })

@staff_member_required
def admin_producto_eliminar(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    producto.delete()
    return redirect("admin_productos")

@staff_member_required
def admin_reservas(request):
    hoy = date.today()

    # Reservas futuras
    reservas = Reserva.objects.filter(fecha__gte=hoy).order_by("fecha", "hora")

    usuarios = Usuario.objects.all()
    servicios = Servicio.objects.all()

    # Crear reserva manual
    if request.method == "POST":
        Reserva.objects.create(
            usuario_id=request.POST.get("usuario"),
            servicio_id=request.POST.get("servicio"),
            fecha=request.POST.get("fecha"),
            hora=request.POST.get("hora")
        )
        return redirect("admin_reservas")

    # Mostrar próximos 6 días hábiles
    dias = []
    dias_a_mostrar = 6
    contador = 0
    suma = 0

    while contador < dias_a_mostrar:
        fecha_actual = hoy + timedelta(days=suma)
        suma += 1

        if fecha_actual.weekday() == 6:  # domingo
            continue

        dia_semana = fecha_actual.weekday()
        horarios = HorarioAtencion.objects.filter(dia_semana=dia_semana)

        horas_lista = []
        for h in horarios:
            bloqueado = Reserva.objects.filter(fecha=fecha_actual, hora=h.hora).exists()
            horas_lista.append({
                "hora": h.hora.strftime("%H:%M"),
                "bloqueado": bloqueado
            })

        dias.append({"fecha": fecha_actual, "horas": horas_lista})
        contador += 1

    return render(request, "web/admin_reservas.html", {
        "reservas": reservas,
        "usuarios": usuarios,
        "servicios": servicios,
        "fecha_hoy": hoy,
        "dias": dias
    })

@staff_member_required
def horarios_disponibles_json(request):
    fecha_str = request.GET.get("fecha")

    if not fecha_str:
        return JsonResponse([])

    fecha = date.fromisoformat(fecha_str)

    # Sin domingos
    if fecha.weekday() == 6:
        return JsonResponse([])

    dia_semana = fecha.weekday()

    horarios = HorarioAtencion.objects.filter(dia_semana=dia_semana)
    reservas = Reserva.objects.filter(fecha=fecha)
    horas_reservadas = [r.hora for r in reservas]

    disponibles = [
        h.hora.strftime("%H:%M")
        for h in horarios
        if h.hora not in horas_reservadas
    ]

    return JsonResponse(disponibles, safe=False)

@staff_member_required
def admin_servicios(request):
    servicios = Servicio.objects.all().order_by("id")
    return render(request, "web/admin_servicios.html", {
        "servicios": servicios,
    })

@staff_member_required
def admin_servicio_crear(request):
    if request.method == "POST":
        nombre = request.POST.get("nombre")
        precio = request.POST.get("precio")
        imagen = request.POST.get("imagen")

        Servicio.objects.create(
            nombre=nombre,
            precio=precio,
            imagen=imagen
        )
        return redirect("admin_servicios")

    return render(request, "web/admin_servicio_form.html", {
        "modo": "crear"
    })

@staff_member_required
def admin_servicio_editar(request, servicio_id):
    servicio = get_object_or_404(Servicio, id=servicio_id)

    if request.method == "POST":
        servicio.nombre = request.POST.get("nombre")
        servicio.precio = request.POST.get("precio")
        servicio.imagen = request.POST.get("imagen")
        servicio.save()
        return redirect("admin_servicios")

    return render(request, "web/admin_servicio_form.html", {
        "modo": "editar",
        "servicio": servicio
    })

@staff_member_required
def admin_servicio_eliminar(request, servicio_id):
    servicio = get_object_or_404(Servicio, id=servicio_id)
    servicio.delete()
    return redirect("admin_servicios")
