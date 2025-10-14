"""
Configuración de URLs principal del proyecto Habitatum.
Conecta todas las aplicaciones y maneja archivos media en desarrollo.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Panel de administración de Django (por defecto)
    path('admin/', admin.site.urls),
    
    # URLs públicas (home, servicios)
    path('', include('core.urls')),
    
    # Galería de propiedades y detalles
    path('propiedades/', include('properties.urls')),
    
    # Agendar citas
    path('citas/', include('appointments.urls')),
    
    # Panel de administración personalizado
    path('panel/', include('dashboard.urls')),
    
    # Integraciones (Google Calendar)
    path('integraciones/', include('integrations.urls')),
]

# Servir archivos media en desarrollo (imágenes subidas)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
