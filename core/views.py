from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

from properties.models import Property
from .forms import CreditAdviceForm


def home_view(request):
    """
    Vista de la página principal.
    Muestra un carousel con las propiedades destacadas (visibles).
    Se muestran las 6 propiedades más recientes.
    """
    # Obtener las propiedades visibles, ordenadas por fecha de creación (más recientes primero)
    propiedades_destacadas = Property.objects.filter(
        is_visible=True
    ).order_by('-fecha_creacion')[:6]
    
    contexto = {
        'propiedades': propiedades_destacadas,
        'titulo_pagina': 'Bienvenido a Habitatum'
    }
    
    return render(request, 'home.html', contexto)


def services_view(request):
    """
    Vista de la página de servicios.
    Muestra los tres servicios principales que ofrece Habitatum:
    1. Venta de propiedades
    2. Asesoramiento crediticio
    3. Apoyo en venta de propiedades de terceros
    
    Incluye un formulario para solicitar asesoría crediticia.
    """
    # Crear instancia vacía del formulario de asesoría
    formulario_asesoria = CreditAdviceForm()
    
    contexto = {
        'form': formulario_asesoria,
        'titulo_pagina': 'Nuestros Servicios'
    }
    
    return render(request, 'services.html', contexto)


def credit_advice_view(request):
    """
    Vista que procesa el formulario de solicitud de asesoría crediticia.
    Solo acepta peticiones POST desde el formulario de servicios.
    
    Proceso:
    1. Valida los datos del formulario
    2. Envía un email al administrador con la información
    3. Muestra un mensaje de éxito al usuario
    4. Redirige de vuelta a la página de servicios
    """
    # Verificar que sea una petición POST
    if request.method != 'POST':
        # Si no es POST, redirigir a servicios
        return redirect('core:services')
    
    # Crear formulario con los datos recibidos
    form = CreditAdviceForm(request.POST)
    
    # Validar el formulario
    if form.is_valid():
        # Extraer datos limpios del formulario
        nombre = form.cleaned_data['nombre']
        email = form.cleaned_data['email']
        telefono = form.cleaned_data['telefono']
        ingresos_mensuales = form.cleaned_data['ingresos_mensuales']
        tipo_credito = form.cleaned_data['tipo_credito']
        mensaje = form.cleaned_data.get('mensaje', '')
        
        # Preparar el asunto del email
        asunto = f'Nueva solicitud de asesoría crediticia - {nombre}'
        
        # Crear el cuerpo del mensaje en texto plano
        cuerpo_mensaje = f"""
        Nueva solicitud de asesoría crediticia recibida:
        
        Nombre: {nombre}
        Email: {email}
        Teléfono: {telefono}
        Ingresos Mensuales: ${ingresos_mensuales:,.2f} MXN
        Tipo de Crédito: {tipo_credito}
        
        Mensaje adicional:
        {mensaje if mensaje else 'No proporcionó mensaje adicional'}
        
        ---
        Este correo fue enviado automáticamente desde el sitio web de Habitatum.
        """
        
        try:
            # Enviar el email al administrador
            send_mail(
                subject=asunto,
                message=cuerpo_mensaje,
                from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@habitatum.com',
                recipient_list=[settings.ADMIN_EMAIL if hasattr(settings, 'ADMIN_EMAIL') else 'admin@habitatum.com'],
                fail_silently=False,
            )
            
            # Mostrar mensaje de éxito
            messages.success(
                request,
                '¡Solicitud enviada con éxito! Nos pondremos en contacto contigo pronto.'
            )
            
        except Exception as e:
            # Si hay error al enviar el email, mostrar mensaje de error
            messages.error(
                request,
                'Hubo un problema al enviar tu solicitud. Por favor, intenta de nuevo o contáctanos directamente.'
            )
            print(f"Error al enviar email de asesoría: {e}")
    
    else:
        # Si el formulario no es válido, mostrar los errores
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f"{field}: {error}")
    
    # Redirigir de vuelta a la página de servicios
    return redirect('core:services')
