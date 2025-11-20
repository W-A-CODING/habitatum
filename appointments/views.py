from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from datetime import date

from .models import Appointment, AvailableDay
from .forms import NormalAppointmentForm, PriorityAppointmentForm
from properties.models import Property


def verificar_disponibilidad_dia(fecha_cita, tipo_cita):
    """
    Verifica si un día específico está disponible para agendar citas del tipo especificado.
    
    Args:
        fecha_cita: datetime object con la fecha de la cita
        tipo_cita: str - 'normal' o 'prioritaria'
        
    Returns:
        tuple: (bool, str) - (disponible, mensaje_error)
    """
    # Convertir a date si es datetime
    if isinstance(fecha_cita, timezone.datetime):
        fecha = fecha_cita.date()
    else:
        fecha = fecha_cita
    
    # Verificar que no sea un día pasado
    if fecha < timezone.now().date():
        return False, "No puedes agendar citas en días pasados."
    
    # Buscar si el día está configurado como disponible
    try:
        dia_disponible = AvailableDay.objects.get(
            fecha_disponible=fecha,
            tipo_cita=tipo_cita
        )
        
        # Verificar si todavía hay capacidad
        if not dia_disponible.esta_disponible():
            citas_count = dia_disponible.obtener_citas_agendadas().count()
            return False, f"Este día ya tiene {citas_count} citas agendadas y ha alcanzado su capacidad máxima de {dia_disponible.capacidad_maxima}. Por favor selecciona otro día."
        
        return True, "Día disponible"
        
    except AvailableDay.DoesNotExist:
        tipo_texto = "citas normales" if tipo_cita == 'normal' else "citas prioritarias"
        return False, f"Este día no está disponible para {tipo_texto}. Por favor selecciona otro día del calendario."


def obtener_fechas_disponibles_mes(anio, mes, tipo_cita):
    """
    Obtiene todas las fechas disponibles de un mes específico para un tipo de cita.
    
    Args:
        anio: int - año
        mes: int - mes (1-12)
        tipo_cita: str - 'normal' o 'prioritaria'
        
    Returns:
        list: Lista de fechas disponibles (date objects)
    """
    dias_disponibles = AvailableDay.objects.filter(
        fecha_disponible__year=anio,
        fecha_disponible__month=mes,
        tipo_cita=tipo_cita,
        fecha_disponible__gte=timezone.now().date()  # Solo días futuros
    )
    
    # Filtrar solo los que tienen capacidad
    fechas = []
    for dia in dias_disponibles:
        if dia.esta_disponible():
            fechas.append(dia.fecha_disponible)
    
    return fechas


def obtener_fechas_disponibles_para_template(anio, mes, tipo_cita):
    """
    Prepara las fechas disponibles en un formato útil para el template.
    
    Args:
        anio: int - año
        mes: int - mes
        tipo_cita: str - 'normal' o 'prioritaria'
        
    Returns:
        dict: Diccionario con información de fechas disponibles
    """
    fechas = obtener_fechas_disponibles_mes(anio, mes, tipo_cita)
    
    # Convertir a lista de strings en formato ISO para uso en JavaScript
    fechas_iso = [fecha.isoformat() for fecha in fechas]
    
    return {
        'mes': mes,
        'anio': anio,
        'fechas': fechas,
        'fechas_iso': fechas_iso,
        'total': len(fechas)
    }


def create_normal_appointment_view(request, property_id):
    """
    Vista para crear una cita normal CON VALIDACIÓN DE DISPONIBILIDAD.
    
    Ahora verifica que:
    1. El día seleccionado esté marcado como disponible por el admin
    2. Todavía haya capacidad en ese día
    3. No sea un día del pasado
    """
    # Obtener la propiedad o mostrar 404
    propiedad = get_object_or_404(Property, pk=property_id, is_visible=True)
    
    if request.method == 'POST':
        # El usuario envió el formulario
        form = NormalAppointmentForm(request.POST)
        
        if form.is_valid():
            # Obtener la fecha seleccionada
            fecha_cita = form.cleaned_data['fecha_cita']
            
            # VALIDACIÓN CRÍTICA: Verificar disponibilidad
            disponible, mensaje_error = verificar_disponibilidad_dia(fecha_cita, 'normal')
            
            if not disponible:
                messages.error(request, mensaje_error)
                # Recargar el formulario con el error
                contexto = {
                    'form': form,
                    'propiedad': propiedad,
                    'tipo_cita': 'normal',
                    'titulo_pagina': f'Agendar Cita - {propiedad.nombre}',
                    'fechas_disponibles': obtener_fechas_disponibles_para_template(timezone.now().year, timezone.now().month, 'normal')
                }
                return render(request, 'appointment_form.html', contexto)
            
            # Si llegamos aquí, el día está disponible
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
            
            # Crear evento en Google Calendar
            try:
                crear_evento_google_calendar(cita)
            except Exception as e:
                print(f"Error al crear evento en Google Calendar: {e}")
            
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
    
    # Obtener fechas disponibles para el calendario
    fechas_disponibles = obtener_fechas_disponibles_para_template(
        timezone.now().year, 
        timezone.now().month, 
        'normal'
    )
    
    contexto = {
        'form': form,
        'propiedad': propiedad,
        'tipo_cita': 'normal',
        'titulo_pagina': f'Agendar Cita - {propiedad.nombre}',
        'fechas_disponibles': fechas_disponibles
    }
    
    return render(request, 'appointment_form.html', contexto)


def create_priority_appointment_view(request, property_id):
    """
    Vista para crear una cita prioritaria CON VALIDACIÓN DE DISPONIBILIDAD.
    
    Ahora verifica que:
    1. El día seleccionado esté marcado como disponible por el admin
    2. Todavía haya capacidad en ese día
    3. No sea un día del pasado
    """
    # Obtener la propiedad o mostrar 404
    propiedad = get_object_or_404(Property, pk=property_id, is_visible=True)
    
    if request.method == 'POST':
        # El usuario envió el formulario
        form = PriorityAppointmentForm(request.POST)
        
        if form.is_valid():
            # Obtener la fecha seleccionada
            fecha_cita = form.cleaned_data['fecha_cita']
            
            # VALIDACIÓN CRÍTICA: Verificar disponibilidad
            disponible, mensaje_error = verificar_disponibilidad_dia(fecha_cita, 'prioritaria')
            
            if not disponible:
                messages.error(request, mensaje_error)
                # Recargar el formulario con el error
                contexto = {
                    'form': form,
                    'propiedad': propiedad,
                    'tipo_cita': 'prioritaria',
                    'titulo_pagina': f'Agendar Cita Prioritaria - {propiedad.nombre}',
                    'fechas_disponibles': obtener_fechas_disponibles_para_template(timezone.now().year, timezone.now().month, 'prioritaria')
                }
                return render(request, 'appointment_form.html', contexto)
            
            # Si llegamos aquí, el día está disponible
            # Crear la cita pero no guardarla todavía
            cita = form.save(commit=False)
            
            # Asignar la propiedad a la cita
            cita.property = propiedad
            
            # Asegurarse de que el tipo de cita sea 'prioritaria'
            cita.tipo_cita = 'prioritaria'
            
            # Guardar en la base de datos
            cita.save()
            
            # Enviar email de notificación al administrador
            try:
                enviar_notificacion_nueva_cita(cita)
            except Exception as e:
                print(f"Error al enviar email de notificación: {e}")
            
            # Crear evento en Google Calendar
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
    
    # Obtener fechas disponibles para el calendario
    fechas_disponibles = obtener_fechas_disponibles_para_template(
        timezone.now().year, 
        timezone.now().month, 
        'prioritaria'
    )
    
    contexto = {
        'form': form,
        'propiedad': propiedad,
        'tipo_cita': 'prioritaria',
        'titulo_pagina': f'Agendar Cita Prioritaria - {propiedad.nombre}',
        'fechas_disponibles': fechas_disponibles
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
