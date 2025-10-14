from django.urls import path
from . import views

app_name = 'integrations'

urlpatterns = [
    # Página de configuración de integraciones
    path('configuracion/', views.integration_settings_view, name='settings'),
    
    # Iniciar flujo OAuth2 con Google Calendar
    path('google/autorizar/', views.google_authorize_view, name='google_authorize'),
    
    # Callback de OAuth2 (Google redirige aquí después de autorizar)
    path('google/callback/', views.google_callback_view, name='google_callback'),
    
    # Desconectar cuenta de Google Calendar
    path('google/desconectar/', views.google_disconnect_view, name='google_disconnect'),
]