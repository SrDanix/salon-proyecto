"""
URL configuration for salonProyecto project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from webApp.views import inicio, user_login, registro, user_logout, servicios, tienda, reserva, compra, pago, pago_exitoso, pago_cancelado, horario, confirmar_reserva, pago_reserva, pago_exitoso_reserva, mi_perfil, editar_perfil, cambiar_contrasena, admin_productos, admin_producto_crear, admin_producto_editar, admin_producto_eliminar, admin_reservas, horarios_disponibles_json, admin_servicios, admin_servicio_crear, admin_servicio_editar, admin_servicio_eliminar

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', inicio, name='inicio'),
    path('login/', user_login, name='login'),
    path('registro/', registro, name='registro'),
    path('logout/', user_logout, name='user_logout'),
    path('servicios/', servicios, name='servicios'),
    path('tienda/', tienda, name='tienda'),
    path("reserva/", reserva, name="reserva"),
    path("compra/", compra, name="compra"),
    path('pago/', pago, name='pago'),
    path('pago/exitoso/', pago_exitoso, name='pago_exitoso'),
    path('pago/cancelado/', pago_cancelado, name='pago_cancelado'),
    path("horario/<int:servicio_id>/", horario, name="horario"),
    path("confirmar/<int:servicio_id>/", confirmar_reserva, name="confirmar_reserva"),
    path("pago-reserva/<int:servicio_id>/", pago_reserva, name="pago_reserva"),
    path("pago-exitoso-reserva/", pago_exitoso_reserva, name="pago_exitoso_reserva"),
    path("perfil/", mi_perfil, name="mi_perfil"),
    path("perfil/editar/", editar_perfil, name="editar_perfil"),
    path("cambiar-contrasena/", cambiar_contrasena, name="cambiar_contrasena"),
    path("admin-productos/", admin_productos, name="admin_productos"),
    path("admin-productos/crear/", admin_producto_crear, name="admin_producto_crear"),
    path("admin-productos/editar/<int:producto_id>/", admin_producto_editar, name="admin_producto_editar"),
    path("admin-productos/eliminar/<int:producto_id>/", admin_producto_eliminar, name="admin_producto_eliminar"),
    path("admin-reservas/", admin_reservas, name="admin_reservas"),
    path("admin-reservas/horarios-disponibles/", horarios_disponibles_json, name="horarios_disponibles_json"),
    path("admin-servicios/", admin_servicios, name="admin_servicios"),
    path("admin-servicios/crear/", admin_servicio_crear, name="admin_servicio_crear"),
    path("admin-servicios/editar/<int:servicio_id>/", admin_servicio_editar, name="admin_servicio_editar"),
    path("admin-servicios/eliminar/<int:servicio_id>/", admin_servicio_eliminar, name="admin_servicio_eliminar"),
]
