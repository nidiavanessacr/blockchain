from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import User, Wallet, Alumno, Transaccion, ActividadAsignada
from algosdk.v2client import algod

# =========================
# CONFIGURACIÓN ALGOD
# =========================
ALGOD_CLIENT = algod.AlgodClient("", "https://testnet-api.algonode.cloud")


# =========================
# USUARIO PERSONALIZADO
# =========================
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Rol en el sistema', {'fields': ('role',)}),
    )
    list_display = ('username', 'email', 'role', 'is_active', 'is_staff')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('username', 'email')


# =========================
# WALLET ADMIN
# =========================
@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'address', 'mostrar_balance')
    search_fields = ('user__username', 'address')
    readonly_fields = ('address', 'private_key')

    def mostrar_balance(self, obj):
        """Consulta el balance en tiempo real desde la red TestNet."""
        try:
            account_info = ALGOD_CLIENT.account_info(obj.address)
            balance = account_info.get('amount', 0) / 1_000_000
            return f"{balance:.6f} ALGOs"
        except Exception:
            return "Error/No disponible"

    mostrar_balance.short_description = "Balance"


# =========================
# ALUMNO ADMIN
# =========================
@admin.register(Alumno)
class AlumnoAdmin(admin.ModelAdmin):
    list_display = ('user', 'email', 'matricula', 'wallet')
    search_fields = ('user__username', 'email', 'matricula')
    list_filter = ('user',)
    ordering = ('matricula',)


# =========================
# TRANSACCIÓN ADMIN
# =========================
@admin.register(Transaccion)
class TransaccionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'txid_coloreado',
        'sender',
        'receiver',
        'amount',
        'tipo',
        'estado_coloreado',
        'confirmed_round',
        'fecha_creacion'
    )
    list_filter = ('tipo', 'estado', 'fecha_creacion')
    search_fields = ('txid', 'sender', 'receiver', 'detalle')
    readonly_fields = ('fecha_creacion', 'confirmed_round', 'txid')
    ordering = ('-fecha_creacion',)

    def txid_coloreado(self, obj):
        """Muestra el TxID abreviado con color y link opcional al explorador."""
        if not obj.txid:
            return "-"
        url = f"https://testnet.explorer.perawallet.app/tx/{obj.txid}"
        return format_html(
            '<a href="{}" target="_blank" style="color:#007bff;text-decoration:none;">{}...</a>',
            url,
            obj.txid[:10]
        )
    txid_coloreado.short_description = "TxID"

    def estado_coloreado(self, obj):
        """Muestra el estado con color visual."""
        colores = {
            'pending': 'orange',
            'confirmed': 'green',
            'failed': 'red'
        }
        color = colores.get(obj.estado, 'gray')
        return format_html('<span style="color:{};font-weight:bold;">{}</span>', color, obj.estado)
    estado_coloreado.short_description = "Estado"


# =========================
# ACTIVIDAD ASIGNADA ADMIN
# =========================
@admin.register(ActividadAsignada)
class ActividadAsignadaAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'actividad',
        'docente',
        'alumno',
        'monto_algos',
        'estado',
        'fecha_asignacion',
        'txid_coloreado'
    )
    list_filter = ('estado', 'docente', 'fecha_asignacion')
    search_fields = ('actividad__titulo', 'alumno__user__username', 'docente__username', 'txid')
    ordering = ('-fecha_asignacion',)
    readonly_fields = ('fecha_asignacion', 'txid', 'docente', 'alumno', 'actividad', 'monto_algos', 'estado')

    def txid_coloreado(self, obj):
        """Abrevia y linkea el TXID si existe."""
        if not obj.txid:
            return "-"
        url = f"https://testnet.algoexplorer.io/tx/{obj.txid}"
        return format_html(
            '<a href="{}" target="_blank" style="color:#007bff;text-decoration:none;">{}...</a>',
            url,
            obj.txid[:10]
        )
    txid_coloreado.short_description = "TxID"
