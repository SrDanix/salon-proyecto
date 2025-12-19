from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from datetime import date, time
from django.conf import settings

# ===========================
#    USER CUSTOM MANAGER
# ===========================

class UsuarioManager(BaseUserManager):
    def create_user(self, username, email, telefono, password=None):
        if not email:
            raise ValueError("El usuario debe tener un email")

        email = self.normalize_email(email)
        user = self.model(username=username, email=email, telefono=telefono)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, telefono, password):
        user = self.create_user(username, email, telefono, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class Usuario(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=20)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UsuarioManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'telefono']

    def __str__(self):
        return self.username


# ===========================
#     SISTEMA DE RESERVAS
# ===========================

class Servicio(models.Model):
    nombre = models.CharField(max_length=100)
    precio = models.IntegerField()
    imagen = models.CharField(max_length=100) 

    def __str__(self):
        return self.nombre


class HorarioAtencion(models.Model):
    DIA_CHOICES = [
        (0, "Lunes"),
        (1, "Martes"),
        (2, "Miércoles"),
        (3, "Jueves"),
        (4, "Viernes"),
        (5, "Sábado"),
        (6, "Domingo"),
    ]

    dia_semana = models.IntegerField(choices=DIA_CHOICES)
    hora = models.TimeField()
    disponible = models.BooleanField(default=True)

    def __str__(self):
        dias = dict(self.DIA_CHOICES)
        return f"{dias[self.dia_semana]} - {self.hora}"


class Reserva(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)   # ← CORREGIDO
    servicio = models.ForeignKey(Servicio, on_delete=models.CASCADE)
    fecha = models.DateField()
    hora = models.TimeField()

    class Meta:
        unique_together = ("fecha", "hora")

    def __str__(self):
        return f"{self.usuario.username} - {self.servicio.nombre} - {self.fecha} {self.hora}"

class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    precio = models.IntegerField()
    imagen = models.CharField(max_length=100)
    stock = models.IntegerField()

    def __str__(self):
        return self.nombre

class Orden(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.IntegerField(default=0)

class OrdenItem(models.Model):
    orden = models.ForeignKey(Orden, on_delete=models.CASCADE, related_name="items")
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.IntegerField()
    subtotal = models.IntegerField()

    def save(self, *args, **kwargs):
        self.subtotal = self.producto.precio * self.cantidad
        super().save(*args, **kwargs)
