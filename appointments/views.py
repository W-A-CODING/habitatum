from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone

from .models import Appointment
from .forms import NormalAppointmentForm, PriorityAppointmentForm
from properties.models import Property


def create_normal_appointment_view(request, property_id):
    """
    Vista para crear una cita normal.
    
    Una cita normal solo requiere:
    - Nombre del cliente
    - Email
    - Teléfono
    - Fecha deseada
    
    Proceso:
    1. Verifica que la propiedad exista y esté visible
    2. Muestra el formulario (GET) o procesa los datos (POST)
    3. Guarda la cita en la base de datos
    4. Envía email de notificación al administrador
    5. Crea evento en Google Calendar
    6. Redirige a página de confirmación
    """
    # Obtener la propiedad o mostrar 404
    propiedad = get_object_or_404(Property, pk=property_id, is_visible=True)
    
    if request.method == 'POST':
        # El usuario envió el formulario
        form = NormalAppointmentForm(request.POST)
        
        if form.is_valid():
            # Crear la cita pero no guardarla todavía (commit=False)
            cita = form.save(commit=False)
            
            # Asignar la propiedad a la cita
            cita.property = propiedad
            
            # Asegurarse de que el tipo de cita sea 'normal'
            cita.tipo_cita = 'normal'
            
            # Ahora sí guardar en la base de datos
            cita.save()
            
            # Enviar email de notificación al administrador
            try:
                enviar_notificacion_nueva_cita(cita)
            except Exception as e:
                print(f"Error al enviar email de notificación: {e}")
                # No detenemos el proceso si falla el email
            
            # Crear evento en Google Calendar
            try:
                crear_evento_google_calendar(cita)
            except Exception as e:
                print(f"Error al crear evento en Google Calendar: {e}")
                # No detenemos el proceso si falla Google Calendar
            
            # Mostrar mensaje de éxito
            messages.success(
                request,
                f'¡Cita agendada con éxito para {propiedad.nombre}!'
            )
            
            # Redirigir a página de confirmación
            return redirect('appointments:confirmation')
        
        else:
            # El formulario tiene errores
            messages.error(
                request,
                'Por favor corrige los errores en el formulario.'
            )
    
    else:
        # Mostrar formulario vacío (GET)
        form = NormalAppointmentForm()
    
    contexto = {
        'form': form,
        'propiedad': propiedad,
        'tipo_cita': 'normal',
        'titulo_pagina': f'Agendar Cita - {propiedad.nombre}'
    }
    
    return render(request, 'appointment_form.html', contexto)


def create_priority_appointment_view(request, property_id):
    """
    Vista para crear una cita prioritaria.
    
    Una cita prioritaria requiere datos adicionales:
    - Nombre del cliente
    - Email
    - Teléfono
    - Fecha deseada
    - Ingresos mensuales
    - Tipo de crédito deseado
    
    Este tipo de cita es para clientes que buscan asesoramiento crediticio
    personalizado. El administrador verá estos datos adicionales en el
    calendario para preparar mejor la cita.
    
    El proceso es el mismo que la cita normal, pero con más información.
    """
    # Obtener la propiedad o mostrar 404
    propiedad = get_object_or_404(Property, pk=property_id, is_visible=True)
    
    if request.method == 'POST':
        # El usuario envió el formulario
        form = PriorityAppointmentForm(request.POST)
        
        if form.is_valid():
            # Crear la cita pero no guardarla todavía
            cita = form.save(commit=False)
            
            # Asignar la propiedad a la cita
            cita.property = propiedad
            
            # Asegurarse de que el tipo de cita sea 'prioritaria'
            cita.tipo_cita = 'prioritaria'
            
            # Guardar en la base de datos
            cita.save()
            
            # Enviar email de notificación al administrador
            # En este caso el email incluirá los datos financieros
            try:
                enviar_notificacion_nueva_cita(cita)
            except Exception as e:
                print(f"Error al enviar email de notificación: {e}")
            
            # Crear evento en Google Calendar
            # El título del evento indicará que es cita prioritaria
            try:
                crear_evento_google_calendar(cita)
            except Exception as e:
                print(f"Error al crear evento en Google Calendar: {e}")
            
            # Mostrar mensaje de éxito personalizado para cita prioritaria
            messages.success(
                request,
                f'¡Cita prioritaria agendada con éxito! Nos pondremos en contacto contigo pronto para el asesoramiento crediticio.'
            )
            
            # Redirigir a página de confirmación
            return redirect('appointments:confirmation')
        
        else:
            # El formulario tiene errores
            messages.error(
                request,
                'Por favor corrige los errores en el formulario.'
            )
    
    else:
        # Mostrar formulario vacío (GET)
        form = PriorityAppointmentForm()
    
    contexto = {
        'form': form,
        'propiedad': propiedad,
        'tipo_cita': 'prioritaria',
        'titulo_pagina': f'Agendar Cita Prioritaria - {propiedad.nombre}'
    }
    
    return render(request, 'appointment_form.html', contexto)


def appointment_confirmation_view(request):
    """
    Vista de confirmación después de agendar una cita.
    
    Muestra un mensaje de agradecimiento y los próximos pasos:
    - Confirmación de que la cita fue agendada
    - Recordatorio de que recibirán un email de confirmación
    - Botón para volver a la galería de propiedades
    - Botón para volver a la página principal
    """
    contexto = {
        'titulo_pagina': 'Cita Agendada'
    }
    
    return render(request, 'confirmation.html', contexto)


# ========================================
# FUNCIONES AUXILIARES
# ========================================

def enviar_notificacion_nueva_cita(cita):
    """
    Envía un email de notificación al administrador cuando se crea una nueva cita.
    
    Esta función:
    1. Renderiza un template HTML con los datos de la cita
    2. Envía el email al administrador configurado en settings
    3. Maneja errores de envío de forma segura
    
    Parámetros:
        cita: Objeto Appointment con los datos de la cita
        
    Retorna:
        bool: True si se envió correctamente, False en caso contrario
    """
    from django.core.mail import send_mail
    from django.template.loader import render_to_string
    from django.conf import settings
    
    try:
        # Preparar asunto del email
        tipo_cita_texto = "Prioritaria" if cita.tipo_cita == 'prioritaria' else "Normal"
        asunto = f"🏠 Nueva Cita {tipo_cita_texto} - {cita.nombre_cliente}"
        
        # Renderizar template HTML
        contexto_email = {
            'cita': cita,
            'propiedad': cita.property,
        }
        
        mensaje_html = render_to_string('email/new_appointment_email.html', contexto_email)
        
        # Crear versión de texto plano
        mensaje_texto = f"""
Nueva cita agendada en Habitatum

Tipo: Cita {tipo_cita_texto}
Cliente: {cita.nombre_cliente}
Email: {cita.email_cliente}
Teléfono: {cita.telefono_cliente}
Fecha: {cita.fecha_cita.strftime('%d/%m/%Y a las %H:%M')} hrs

Propiedad: {cita.property.nombre}
Ubicación: {cita.property.ubicacion}
"""
        
        if cita.tipo_cita == 'prioritaria':
            mensaje_texto += f"""
Información Financiera:
- Ingresos mensuales: ${cita.ingresos_mensuales:,.2f} MXN
- Tipo de crédito: {cita.get_tipo_credito_display()}
"""
        
        # Enviar email
        resultado = send_mail(
            subject=asunto,
            message=mensaje_texto,
            html_message=mensaje_html,
            from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@habitatum.com',
            recipient_list=[settings.ADMIN_EMAIL if hasattr(settings, 'ADMIN_EMAIL') else 'admin@habitatum.com'],
            fail_silently=False,
        )
        
        print(f"✅ Email de notificación enviado correctamente")
        return True
        
    except Exception as error:
        print(f"❌ Error al enviar email de notificación: {error}")
        return False


def crear_evento_google_calendar(cita):
    """
    Crea un evento en Google Calendar para la cita agendada.
    
    Esta función:
    1. Importa el servicio de Google Calendar
    2. Intenta crear el evento con todos los detalles
    3. Maneja errores de forma segura sin interrumpir el flujo
    
    Parámetros:
        cita: Objeto Appointment con los datos de la cita
        
    Retorna:
        str: ID del evento creado, o None si falla
    """
    try:
        # Importar el servicio de Google Calendar
        from integrations.services.google_calendar_service import crear_evento_en_google_calendar
        
        # Crear evento en Google Calendar
        id_evento = crear_evento_en_google_calendar(cita)
        
        if id_evento:
            print(f"✅ Evento creado en Google Calendar con ID: {id_evento}")
            return id_evento
        else:
            print(f"⚠️ No se pudo crear el evento en Google Calendar (posiblemente no hay tokens configurados)")
            return None
            
    except Exception as error:
        print(f"❌ Error al crear evento en Google Calendar: {error}")
        return None
