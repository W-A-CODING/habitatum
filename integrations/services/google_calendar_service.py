"""
Servicio para gestionar la integración con Google Calendar API.

Este módulo proporciona funciones para crear, actualizar y eliminar
eventos en Google Calendar de forma segura y eficiente.
"""

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from django.conf import settings
from datetime import datetime, timedelta
import pytz

from ..models import GoogleApiToken


def obtener_credenciales_google(usuario):
    """
    Obtiene las credenciales OAuth2 de Google Calendar para un usuario específico.
    
    Parámetros:
        usuario: Objeto User de Django del administrador
        
    Retorna:
        Credentials: Objeto de credenciales de Google OAuth2, o None si no existen
        
    Excepciones:
        GoogleApiToken.DoesNotExist: Si el usuario no tiene tokens configurados
    """
    try:
        token_google = GoogleApiToken.objects.get(user=usuario)
        
        # Crear credenciales desde los datos almacenados
        credenciales = Credentials(
            token=token_google.token,
            refresh_token=token_google.refresh_token,
            token_uri=token_google.token_uri,
            client_id=token_google.client_id,
            client_secret=token_google.client_secret,
            scopes=token_google.scopes.split()
        )
        
        return credenciales
        
    except GoogleApiToken.DoesNotExist:
        print(f"No se encontraron credenciales de Google para el usuario: {usuario.username}")
        return None


def crear_evento_en_google_calendar(cita, usuario_admin=None):
    """
    Crea un evento en Google Calendar basado en una cita de Habitatum.
    
    Este método:
    1. Obtiene las credenciales OAuth2 del administrador
    2. Construye el servicio de Google Calendar API
    3. Crea un evento con todos los detalles de la cita
    4. Guarda el ID del evento en la base de datos
    
    Parámetros:
        cita: Objeto Appointment con los datos de la cita
        usuario_admin: Usuario administrador (opcional, usa el primero si no se especifica)
        
    Retorna:
        str: ID del evento creado en Google Calendar, o None si falla
        
    Excepciones:
        HttpError: Si hay problemas con la API de Google
    """
    try:
        # Si no se especifica usuario, usar el primer usuario con tokens
        if usuario_admin is None:
            primer_token = GoogleApiToken.objects.first()
            if not primer_token:
                print("❌ No hay tokens de Google Calendar configurados")
                return None
            usuario_admin = primer_token.user
        
        # Obtener credenciales
        credenciales = obtener_credenciales_google(usuario_admin)
        if not credenciales:
            print("❌ No se pudieron obtener las credenciales de Google")
            return None
        
        # Construir el servicio de Google Calendar
        servicio_calendar = build('calendar', 'v3', credentials=credenciales)
        
        # Preparar los datos del evento
        titulo_evento = construir_titulo_evento(cita)
        descripcion_evento = construir_descripcion_evento(cita)
        ubicacion_evento = cita.property.ubicacion
        
        # Configurar zona horaria de México
        zona_horaria_mexico = pytz.timezone('America/Mexico_City')
        
        # Fecha y hora de inicio
        fecha_hora_inicio = cita.fecha_cita
        if fecha_hora_inicio.tzinfo is None:
            fecha_hora_inicio = zona_horaria_mexico.localize(fecha_hora_inicio)
        
        # Duración del evento según tipo de cita
        if cita.tipo_cita == 'prioritaria':
            duracion_minutos = 90  # Citas prioritarias: 90 minutos
        else:
            duracion_minutos = 45  # Citas normales: 45 minutos
        
        fecha_hora_fin = fecha_hora_inicio + timedelta(minutes=duracion_minutos)
        
        # Construir el cuerpo del evento
        cuerpo_evento = {
            'summary': titulo_evento,
            'description': descripcion_evento,
            'location': ubicacion_evento,
            'start': {
                'dateTime': fecha_hora_inicio.isoformat(),
                'timeZone': 'America/Mexico_City',
            },
            'end': {
                'dateTime': fecha_hora_fin.isoformat(),
                'timeZone': 'America/Mexico_City',
            },
            'attendees': [
                {'email': cita.email_cliente},
            ],
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},  # 1 día antes
                    {'method': 'popup', 'minutes': 60},       # 1 hora antes
                ],
            },
            'colorId': '11' if cita.tipo_cita == 'prioritaria' else '9',  # Rojo para prioritarias, Azul para normales
        }
        
        # Crear el evento en Google Calendar
        evento_creado = servicio_calendar.events().insert(
            calendarId='primary',
            body=cuerpo_evento
        ).execute()
        
        # Guardar el ID del evento en la base de datos
        id_evento_google = evento_creado.get('id')
        cita.google_event_id = id_evento_google
        cita.save()
        
        print(f"✅ Evento creado en Google Calendar: {evento_creado.get('htmlLink')}")
        return id_evento_google
        
    except HttpError as error_http:
        print(f"❌ Error HTTP al crear evento en Google Calendar: {error_http}")
        return None
        
    except Exception as error_general:
        print(f"❌ Error general al crear evento en Google Calendar: {error_general}")
        return None


def construir_titulo_evento(cita):
    """
    Construye el título del evento para Google Calendar.
    
    Parámetros:
        cita: Objeto Appointment
        
    Retorna:
        str: Título formateado del evento
    """
    tipo_emoji = "💼" if cita.tipo_cita == 'prioritaria' else "📅"
    titulo = f"{tipo_emoji} Cita - {cita.nombre_cliente} - {cita.property.nombre}"
    return titulo


def construir_descripcion_evento(cita):
    """
    Construye la descripción detallada del evento para Google Calendar.
    
    Parámetros:
        cita: Objeto Appointment
        
    Retorna:
        str: Descripción formateada del evento en HTML
    """
    tipo_cita_texto = "Cita Prioritaria (con Asesoría Crediticia)" if cita.tipo_cita == 'prioritaria' else "Cita Normal"
    
    descripcion = f"""
<b>🏠 CITA HABITATUM</b>

<b>Tipo:</b> {tipo_cita_texto}

<b>📋 INFORMACIÓN DEL CLIENTE</b>
- Nombre: {cita.nombre_cliente}
- Email: {cita.email_cliente}
- Teléfono: {cita.telefono_cliente}

<b>🏘️ PROPIEDAD</b>
- Nombre: {cita.property.nombre}
- Ubicación: {cita.property.ubicacion}
- Tipo: {cita.property.get_tipo_inmueble_display()}
- Superficie: {cita.property.metros_cuadrados} m²
- Precio: ${cita.property.precio:,.2f} MXN
"""
    
    # Agregar información financiera para citas prioritarias
    if cita.tipo_cita == 'prioritaria':
        descripcion += f"""
<b>💰 INFORMACIÓN FINANCIERA</b>
- Ingresos mensuales: ${cita.ingresos_mensuales:,.2f} MXN
- Tipo de crédito: {cita.get_tipo_credito_display()}

<b>📌 NOTA:</b> Esta es una cita prioritaria que incluye asesoría crediticia.
Prepara información sobre opciones de {cita.get_tipo_credito_display().lower()} antes de la reunión.
"""
    
    descripcion += """
---
<i>Evento creado automáticamente por Habitatum</i>
"""
    
    return descripcion


def actualizar_evento_google_calendar(cita):
    """
    Actualiza un evento existente en Google Calendar.
    
    Parámetros:
        cita: Objeto Appointment con google_event_id válido
        
    Retorna:
        bool: True si se actualizó correctamente, False en caso contrario
    """
    if not cita.google_event_id:
        print("⚠️ La cita no tiene un evento asociado en Google Calendar")
        return False
    
    try:
        # Obtener credenciales
        primer_token = GoogleApiToken.objects.first()
        if not primer_token:
            return False
        
        credenciales = obtener_credenciales_google(primer_token.user)
        if not credenciales:
            return False
        
        # Construir servicio
        servicio_calendar = build('calendar', 'v3', credentials=credenciales)
        
        # Obtener evento existente
        evento_existente = servicio_calendar.events().get(
            calendarId='primary',
            eventId=cita.google_event_id
        ).execute()
        
        # Actualizar campos
        evento_existente['summary'] = construir_titulo_evento(cita)
        evento_existente['description'] = construir_descripcion_evento(cita)
        evento_existente['location'] = cita.property.ubicacion
        
        # Actualizar fecha si cambió
        zona_horaria_mexico = pytz.timezone('America/Mexico_City')
        fecha_hora_inicio = cita.fecha_cita
        if fecha_hora_inicio.tzinfo is None:
            fecha_hora_inicio = zona_horaria_mexico.localize(fecha_hora_inicio)
        
        duracion_minutos = 90 if cita.tipo_cita == 'prioritaria' else 45
        fecha_hora_fin = fecha_hora_inicio + timedelta(minutes=duracion_minutos)
        
        evento_existente['start'] = {
            'dateTime': fecha_hora_inicio.isoformat(),
            'timeZone': 'America/Mexico_City',
        }
        evento_existente['end'] = {
            'dateTime': fecha_hora_fin.isoformat(),
            'timeZone': 'America/Mexico_City',
        }
        
        # Actualizar evento
        evento_actualizado = servicio_calendar.events().update(
            calendarId='primary',
            eventId=cita.google_event_id,
            body=evento_existente
        ).execute()
        
        print(f"✅ Evento actualizado en Google Calendar: {evento_actualizado.get('htmlLink')}")
        return True
        
    except HttpError as error:
        print(f"❌ Error al actualizar evento en Google Calendar: {error}")
        return False


def eliminar_evento_google_calendar(cita):
    """
    Elimina un evento de Google Calendar.
    
    Parámetros:
        cita: Objeto Appointment con google_event_id válido
        
    Retorna:
        bool: True si se eliminó correctamente, False en caso contrario
    """
    if not cita.google_event_id:
        print("⚠️ La cita no tiene un evento asociado en Google Calendar")
        return False
    
    try:
        # Obtener credenciales
        primer_token = GoogleApiToken.objects.first()
        if not primer_token:
            return False
        
        credenciales = obtener_credenciales_google(primer_token.user)
        if not credenciales:
            return False
        
        # Construir servicio
        servicio_calendar = build('calendar', 'v3', credentials=credenciales)
        
        # Eliminar evento
        servicio_calendar.events().delete(
            calendarId='primary',
            eventId=cita.google_event_id
        ).execute()
        
        print(f"✅ Evento eliminado de Google Calendar: {cita.google_event_id}")
        
        # Limpiar el ID del evento en la base de datos
        cita.google_event_id = None
        cita.save()
        
        return True
        
    except HttpError as error:
        print(f"❌ Error al eliminar evento de Google Calendar: {error}")
        return False