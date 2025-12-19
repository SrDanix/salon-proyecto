import re
from django.core.exceptions import ValidationError

def validar_telefono(value):
    if not value.isdigit():
        raise ValidationError("El teléfono solo debe contener números")
    if len(value) < 8 or len(value) > 12:
        raise ValidationError("El teléfono debe tener entre 8 y 12 dígitos")

def validar_password_segura(value):
    if len(value) < 8:
        raise ValidationError("La contraseña debe tener al menos 8 caracteres")
    if not re.search(r"[A-Z]", value):
        raise ValidationError("Debe contener una mayúscula")
    if not re.search(r"[0-9]", value):
        raise ValidationError("Debe contener un número")
