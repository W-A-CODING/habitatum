"""
Utilidades helper para manejar el flujo OAuth2 de Google.

Proporciona funciones auxiliares para facilitar la autenticación
y manejo de tokens de Google Calendar.
"""

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from django.conf import settings
from django.urls import reverse


def crear_flujo_oauth_google(request):
    """
    Crea un objeto Flow para iniciar el proceso de autorización OAuth2 con Google.
    
    Parámetros:
        request: Objeto HttpRequest de Django para construir URL de callback
        
    Retorna:
        Flow: Objeto Flow configurado para OAuth2
    """
    # URL de redirección después de la autorización
    url_callback = request.build_absolute_uri(reverse('integrations:google_callback'))
    
    # Crear el flujo OAuth2
    flujo_oauth = Flow.from_client_config(
        settings.GOOGLE_OAUTH_CREDENTIALS,
        scopes=['https://www.googleapis.com/auth/calendar.events'],
        redirect_uri=url_callback
    )
    
    return flujo_oauth


def obtener_url_autorizacion_google(flujo_oauth):
    """
    Genera la URL de autorización de Google OAuth2.
    
    Parámetros:
        flujo_oauth: Objeto Flow configurado
        
    Retorna:
        tuple: (url_autorizacion, state) - URL para redirigir y token de estado
    """
    url_autorizacion, estado = flujo_oauth.authorization_url(
        access_type='offline',  # Permite refresh token
        include_granted_scopes='true',
        prompt='consent'  # Fuerza mostrar pantalla de consentimiento
    )
    
    return url_autorizacion, estado


def intercambiar_codigo_por_tokens(flujo_oauth, url_respuesta_completa):
    """
    Intercambia el código de autorización por tokens de acceso.
    
    Parámetros:
        flujo_oauth: Objeto Flow configurado
        url_respuesta_completa: URL completa de respuesta con el código
        
    Retorna:
        Credentials: Credenciales de Google OAuth2 con los tokens
    """
    flujo_oauth.fetch_token(authorization_response=url_respuesta_completa)
    credenciales = flujo_oauth.credentials
    return credenciales


def verificar_credenciales_validas(credenciales):
    """
    Verifica si las credenciales de Google son válidas y no han expirado.
    
    Parámetros:
        credenciales: Objeto Credentials de Google
        
    Retorna:
        bool: True si las credenciales son válidas, False en caso contrario
    """
    if not credenciales:
        return False
    
    if not credenciales.valid:
        if credenciales.expired and credenciales.refresh_token:
            # Intentar refrescar el token
            try:
                from google.auth.transport.requests import Request
                credenciales.refresh(Request())
                return True
            except Exception as error:
                print(f"❌ Error al refrescar token: {error}")
                return False
        return False
    
    return True


def formatear_scopes_para_db(lista_scopes):
    """
    Convierte una lista de scopes en string para guardar en la base de datos.
    
    Parámetros:
        lista_scopes: Lista de strings con los scopes
        
    Retorna:
        str: String con scopes separados por espacios
    """
    return ' '.join(lista_scopes)


def parsear_scopes_desde_db(texto_scopes):
    """
    Convierte un string de scopes de la base de datos en lista.
    
    Parámetros:
        texto_scopes: String con scopes separados por espacios
        
    Retorna:
        list: Lista de scopes
    """
    return texto_scopes.split()