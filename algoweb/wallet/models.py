from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

# =========================
# USUARIO PERSONALIZADO
# =========================
class User(AbstractUser):
    ROLES = (
        ('admin', 'Administrador'),
        ('docente', 'Docente'),
        ('estudiante', 'Estudiante'),
    )
    role = models.CharField(max_length=20, choices=ROLES, default='estudiante')

    def __str__(self):
        return f"{self.username} ({self.role})"


# =========================
# WALLET
# =========================
class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    address = models.CharField(max_length=128, unique=True)
    private_key = models.TextField()

    def __str__(self):
        return f"Wallet de {self.user.username}"


# =========================
# ALUMNO
# =========================
class Alumno(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil_alumno')
    email = models.EmailField(unique=True)
    matricula = models.CharField(max_length=20, unique=True)
    wallet = models.ForeignKey(Wallet, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} ({self.matricula})"


# =========================
# TRANSACCIÓN
# =========================
class Transaccion(models.Model):
    TIPO_CHOICES = (
        ('admin_to_docente', 'Admin → Docente'),
        ('docente_to_alumno', 'Docente → Alumno'),
    )

    ESTADO_CHOICES = (
        ('pending', 'Pendiente'),
        ('confirmed', 'Confirmada'),
        ('failed', 'Fallida'),
    )

    sender = models.CharField(max_length=128)
    receiver = models.CharField(max_length=128)
    amount = models.DecimalField(max_digits=12, decimal_places=6)
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pending')
    txid = models.CharField(max_length=128, null=True, blank=True)
    confirmed_round = models.IntegerField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(default=timezone.now)
    detalle = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.amount} ALGOs ({self.estado})"


# =========================
# ACTIVIDAD
# =========================
class Actividad(models.Model):
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    recompensa_algos = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    docente = models.ForeignKey(User, on_delete=models.CASCADE, related_name='actividades_creadas')
    fecha_creacion = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.titulo} (por {self.docente.username})"


# =========================
# ACTIVIDAD ASIGNADA
# =========================
class ActividadAsignada(models.Model):
    actividad = models.ForeignKey(Actividad, on_delete=models.CASCADE, related_name='asignaciones')
    docente = models.ForeignKey(User, on_delete=models.CASCADE, related_name='actividades_asignadas')
    alumno = models.ForeignKey(User, on_delete=models.CASCADE, related_name='actividades_recibidas')
    fecha_asignacion = models.DateTimeField(default=timezone.now)
    monto_algos = models.DecimalField(max_digits=12, decimal_places=6, default=0)
    txid = models.CharField(max_length=128, null=True, blank=True)
    estado = models.CharField(
        max_length=20,
        choices=[
            ('pendiente', 'Pendiente'),
            ('en_progreso', 'En progreso'),
            ('completada', 'Completada')
        ],
        default='pendiente'
    )
    nota = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.actividad.titulo} → {self.alumno.username} ({self.estado})"
