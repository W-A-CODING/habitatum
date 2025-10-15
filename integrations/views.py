from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.urls import reverse

from .models import GoogleApiToken


@login_required(login_url='dashboard:login')
def integration_settings_view(request):
    """
    Vista de configuración de integraciones.
    
    Muestra el estado actual de las integraciones disponibles:
    - Google Calendar: Conectado o Desconectado
    - Botones para conectar o desconectar servicios
    - Información sobre los permisos requeridos
    - Instrucciones de configuración
    
    Verifica si existe un token de Google Calendar para el usuario actual.
    """
    # Verificar si el usuario tiene Google Calendar conectado
    try:
        google_token = GoogleApiToken.objects.get(user=request.user)
        google_conectado = True
    except GoogleApiToken.DoesNotExist:
        google_token = None
        google_conectado = False
    
    contexto = {
        'google_conectado': google_conectado,
        'google_token': google_token,
        'titulo_pagina': 'Configuración de Integraciones'
    }
    
    return render(request, 'admin/integration_settings.html', contexto)


@login_required(login_url='dashboard:login')
def google_authorize_view(request):
    """
    Vista que inicia el flujo de autorización OAuth2 con Google.
    
    Pasos del flujo OAuth2:
    1. Genera una URL de autorización de Google
    2. Redirige al usuario a Google para que autorice la aplicación
    3. Google redirige de vuelta a google_callback_view
    
    Permisos solicitados:
    - calendar.events: Crear y modificar eventos en Google Calendar
    
    NOTA: Requiere configuración previa de credenciales OAuth2 en Google Cloud Console.
    Para obtener credenciales:
    1. Ir a: https://console.cloud.google.com/
    2. Crear proyecto o seleccionar existente
    3. Habilitar Google Calendar API
    4. Crear credenciales OAuth 2.0
    5. Configurar URL de redirección: http://127.0.0.1:8000/integraciones/google/callback/
    6. Descargar archivo JSON y agregar credenciales a settings.py
    """
    try:
        from google_auth_oauthlib.flow import Flow
        import os
        
        # Verificar que las credenciales estén configuradas
        if not hasattr(settings, 'GOOGLE_OAUTH_CREDENTIALS'):
            messages.error(
                request,
                'Las credenciales de Google OAuth2 no están configuradas. '
                'Contacta al administrador del sistema.'
            )
            return redirect('integrations:settings')
        
        # Configurar el flujo OAuth2
        flow = Flow.from_client_config(
            settings.GOOGLE_OAUTH_CREDENTIALS,
            scopes=['https://www.googleapis.com/auth/calendar.events'],
            redirect_uri=request.build_absolute_uri(reverse('integrations:google_callback'))
        )
        
        # Generar URL de autorización
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        
        # Guardar el state en la sesión para verificar en el callback
        request.session['oauth_state'] = state
        
        # Redirigir a Google para autorización
        return redirect(authorization_url)
    
    except ImportError:
        messages.error(
            request,
            'Las librerías de Google OAuth2 no están instaladas. '
            'Ejecuta: pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client'
        )
        return redirect('integrations:settings')
    
    except Exception as e:
        messages.error(
            request,
            f'Error al iniciar la autorización de Google: {str(e)}'
        )
        return redirect('integrations:settings')


@login_required(login_url='dashboard:login')
def google_callback_view(request):
    """
    Vista de callback después de la autorización de Google.
    
    Google redirige aquí después de que el usuario autoriza la aplicación.
    
    Pasos:
    1. Verifica que el state coincida (seguridad)
    2. Intercambia el código de autorización por tokens de acceso
    3. Guarda los tokens en la base de datos (GoogleApiToken)
    4. Redirige a la configuración con mensaje de éxito
    
    Parámetros en la URL (enviados por Google):
    - code: Código de autorización temporal
    - state: Token de seguridad para verificar la petición
    - error: Si el usuario rechazó la autorización
    """
    try:
        from google_auth_oauthlib.flow import Flow
        from google.oauth2.credentials import Credentials
        
        # Verificar si hubo un error (usuario rechazó)
        if 'error' in request.GET:
            messages.warning(
                request,
                'Autorización cancelada. No se conectó Google Calendar.'
            )
            return redirect('integrations:settings')
        
        # Verificar que el state coincida
        state = request.session.get('oauth_state')
        if not state or state != request.GET.get('state'):
            messages.error(
                request,
                'Error de seguridad: State no coincide. Intenta de nuevo.'
            )
            return redirect('integrations:settings')
        
        # Configurar el flujo OAuth2 de nuevo
        flow = Flow.from_client_config(
            settings.GOOGLE_OAUTH_CREDENTIALS,
            scopes=['https://www.googleapis.com/auth/calendar.events'],
            redirect_uri=request.build_absolute_uri(reverse('integrations:google_callback')),
            state=state
        )
        
        # Intercambiar el código por tokens
        flow.fetch_token(authorization_response=request.build_absolute_uri())
        
        # Obtener las credenciales
        credentials = flow.credentials
        
        # Guardar o actualizar el token en la base de datos
        google_token, created = GoogleApiToken.objects.update_or_create(
            user=request.user,
            defaults={
                'token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'token_uri': credentials.token_uri,
                'client_id': credentials.client_id,
                'client_secret': credentials.client_secret,
                'scopes': ' '.join(credentials.scopes),
            }
        )
        
        # Limpiar el state de la sesión
        del request.session['oauth_state']
        
        if created:
            messages.success(
                request,
                '¡Google Calendar conectado exitosamente! Ahora las citas se crearán automáticamente en tu calendario.'
            )
        else:
            messages.success(
                request,
                '¡Conexión con Google Calendar actualizada exitosamente!'
            )
        
        return redirect('integrations:settings')
    
    except Exception as e:
        messages.error(
            request,
            f'Error al conectar con Google Calendar: {str(e)}'
        )
        return redirect('integrations:settings')


@login_required(login_url='dashboard:login')
def google_disconnect_view(request):
    """
    Vista para desconectar Google Calendar.
    
    Elimina los tokens almacenados de Google Calendar.
    Después de esto, las citas ya no se crearán en Google Calendar
    hasta que se vuelva a conectar.
    
    Requiere confirmación mediante POST para evitar desconexiones accidentales.
    """
    if request.method == 'POST':
        try:
            # Buscar y eliminar el token del usuario
            google_token = GoogleApiToken.objects.get(user=request.user)
            google_token.delete()
            
            messages.success(
                request,
                'Google Calendar desconectado exitosamente. Las nuevas citas ya no se sincronizarán.'
            )
        except GoogleApiToken.DoesNotExist:
            messages.warning(
                request,
                'No había ninguna conexión activa con Google Calendar.'
            )
        
        return redirect('integrations:settings')
    
    # Si no es POST, redirigir a configuración
    messages.error(
        request,
        'Método no permitido. Usa el botón de desconectar desde la configuración.'
    )
    return redirect('integrations:settings')