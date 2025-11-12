from django.urls import path
from . import views

urlpatterns = [
    # ======================================
    # 🔐 Autenticación
    # ======================================
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('registro/', views.registro_view, name='registro'),

    # ======================================
    # 🧭 Dashboards según rol
    # ======================================
    path('dashboard/admin/', views.dashboard_admin, name='dashboard_admin'),
    path('dashboard/docente/', views.dashboard_docente, name='dashboard_docente'),
    path('dashboard/estudiante/', views.dashboard_estudiante, name='dashboard_estudiante'),

    # ======================================
    # 🏠 Sección principal
    # ======================================
    path('index/', views.index, name='index'),
    path('info/', views.info, name='info'),

    # ======================================
    # 💼 Wallet y transacciones
    # ======================================
    path('mi_wallet/', views.mi_wallet, name='mi_wallet'),
    path('registrar_wallet/', views.registrar_wallet, name='registrar_wallet'),
    path('get_balance/', views.get_balance, name='get_balance'),
    path('transacciones/', views.transacciones, name='transacciones'),
    path('envio/', views.envio, name='envio'),

    # ======================================
    # 👨‍🏫 Gestión de alumnos
    # ======================================
    path('alumnos/', views.alumnos, name='alumnos'),
    path('agregar_alumno/', views.agregar_alumno, name='agregar_alumno'),

    # ======================================
    # 🧾 Actividades (Administrador)
    # ======================================
    path('crear_actividad/', views.crear_actividad, name='crear_actividad'),

    # ======================================
    # 💸 Transferencias de ALGOs
    # ======================================
    # Admin → Docente
    path('admin/enviar_algos/', views.enviar_algos_admin, name='enviar_algos_admin'),
    
    # ⚠️ Eliminado: Docente → Estudiante (ya se hace en asignar_actividad)
    # path('docente/enviar_algos/', views.enviar_algos_docente, name='enviar_algos_docente'),

    # ======================================
    # 📘 Asignar actividades (Docente → Estudiantes)
    # ======================================
    path('asignar_actividad/', views.asignar_actividad, name='asignar_actividad'),

    # ======================================
    # 📊 Historial de transacciones
    # ======================================
    # ⚠️ Asegúrate de que esta vista exista, o coméntala temporalmente
    # path('historial-transacciones/', views.historial_transacciones, name='historial_transacciones'),
]
