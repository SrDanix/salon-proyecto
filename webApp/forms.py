from django import forms
from .models import Usuario, Reserva, Servicio
from django.contrib.auth import get_user_model
from .validators import validar_password_segura, validar_telefono
import datetime


Usuario = get_user_model()

# ==========================
#     FORM LOGIN
# ==========================
class LoginForm(forms.Form):
    username = forms.CharField(label="Usuario")
    password = forms.CharField(widget=forms.PasswordInput, label="Contraseña")


# ==========================
#   FORM REGISTRO
# ==========================
class UserRegisterForm(forms.ModelForm):
    password1 = forms.CharField(
        widget=forms.PasswordInput,
        validators=[validar_password_segura],
        label="Contraseña"
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput,
        label="Confirmar contraseña"
    )

    class Meta:
        model = Usuario
        fields = ["username", "email", "telefono"]

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if Usuario.objects.filter(username=username).exists():
            raise forms.ValidationError("El usuario ya existe")
        return username

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if Usuario.objects.filter(email=email).exists():
            raise forms.ValidationError("El correo ya está registrado")
        return email

    def clean_telefono(self):
        telefono = self.cleaned_data.get("telefono")
        validar_telefono(telefono)
        return telefono

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password1")
        p2 = cleaned_data.get("password2")

        if p1 and p2 and p1 != p2:
            self.add_error("password2", "Las contraseñas no coinciden")

        return cleaned_data

    def save(self, commit=True):
        user = Usuario(
            username=self.cleaned_data["username"],
            email=self.cleaned_data["email"],
            telefono=self.cleaned_data["telefono"]
        )
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


# =====================================
#        FORMULARIO DE RESERVA
# =====================================

class ReservaForm(forms.ModelForm):

    # Este campo NO está en Meta porque lo capturamos manualmente
    hora = forms.TimeField(
        required=False,
        widget=forms.HiddenInput()
    )

    class Meta:
        model = Reserva
        fields = ["servicio", "fecha"]
        widgets = {
            "fecha": forms.DateInput(attrs={"type": "date"})
        }
