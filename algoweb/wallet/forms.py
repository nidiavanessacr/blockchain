from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Actividad

# === 🧍‍♀️ Formulario de registro de usuarios ===
class RegistroUsuarioForm(UserCreationForm):
    role = forms.ChoiceField(choices=User.ROLES, label="Tipo de usuario")

    class Meta:
        model = User
        fields = ['username', 'email', 'role', 'password1', 'password2']


# === 🧩 Formulario para crear actividades (Administrador) ===
class ActividadForm(forms.ModelForm):
    class Meta:
        model = Actividad
        fields = ['titulo', 'descripcion', 'recompensa_algos']
        labels = {
            'titulo': 'Título de la Actividad',
            'descripcion': 'Descripción',
            'recompensa_algos': 'Recompensa (ALGOs)',
        }
        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Ej. Investigación sobre Blockchain'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 4, 
                'placeholder': 'Describe brevemente la actividad...'
            }),
            'recompensa_algos': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': '0', 
                'step': '0.01'
            }),
        }
