"""
URL configuration for algoweb project.

El archivo define cómo se enrutan las URLs principales del proyecto hacia las aplicaciones.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static  # 👈 necesario para servir archivos estáticos y multimedia

urlpatterns = [
    # ======================================
    # 🧭 Panel de administración de Django
    # ======================================
    path('admin/', admin.site.urls),

    # ======================================
    # 💼 Rutas principales (de la app 'wallet')
    # ======================================
    path('', include('wallet.urls')),  # redirige todo hacia las URLs de la app wallet
]

# ======================================
# 🖼️ Archivos estáticos y multimedia (solo en modo DEBUG)
# ======================================
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
