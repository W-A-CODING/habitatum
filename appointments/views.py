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
    Función auxiliar para enviar email al administrador
    cuando se crea una nueva cita.
    
    """
    print(f"\n{'='*50}")
    print(f"NUEVA CITA AGENDADA")
    print(f"{'='*50}")
    print(f"Cliente: {cita.nombre_cliente}")
    print(f"Email: {cita.email_cliente}")
    print(f"Teléfono: {cita.telefono_cliente}")
    print(f"Propiedad: {cita.property.nombre}")
    print(f"Fecha: {cita.fecha_cita}")
    print(f"Tipo: {cita.tipo_cita}")
    
    if cita.tipo_cita == 'prioritaria':
        print(f"\nDATOS FINANCIEROS:")
        print(f"Ingresos mensuales: ${cita.ingresos_mensuales:,.2f}")
        print(f"Tipo de crédito: {cita.get_tipo_credito_display()}")
    
    print(f"{'='*50}\n")
    



def crear_evento_google_calendar(cita):
    """
    Función auxiliar para crear un evento en Google Calendar
    cuando se agenda una cita.
    
    """
    print(f"\n{'='*50}")
    print(f"CREAR EVENTO EN GOOGLE CALENDAR")
    print(f"{'='*50}")
    print(f"Título: Cita - {cita.property.nombre}")
    print(f"Cliente: {cita.nombre_cliente}")
    print(f"Fecha: {cita.fecha_cita}")
    print(f"Ubicación: {cita.property.ubicacion}")
    print(f"{'='*50}\n")
   