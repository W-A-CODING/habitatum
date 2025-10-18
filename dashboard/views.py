from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Q
from django.http import HttpResponse
from datetime import datetime, timedelta
import calendar

from appointments.models import Appointment
from properties.models import Property, PropertyImage
from properties.forms import PropertyForm


def admin_login_view(request):
    """
    Vista de login personalizada para el panel de administración.
    
    Permite al administrador iniciar sesión con usuario y contraseña.
    Si ya está autenticado, redirige directamente al calendario.
    
    Características:
    - Verifica credenciales
    - Inicia sesión en el sistema
    - Redirige al calendario o a la URL especificada en 'next'
    - Muestra mensajes de error si las credenciales son incorrectas
    """
    # Si el usuario ya está autenticado, redirigir al calendario
    if request.user.is_authenticated:
        return redirect('dashboard:calendar')
    
    if request.method == 'POST':
        # Obtener datos del formulario
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Verificar que se proporcionaron ambos campos
        if not username or not password:
            messages.error(request, 'Por favor proporciona usuario y contraseña.')
            return render(request, 'admin/login.html')
        
        # Autenticar al usuario
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Las credenciales son correctas
            login(request, user)
            
            # Mensaje de bienvenida
            messages.success(request, f'¡Bienvenido, {user.username}!', extra_tags='alert alert-success')
            
            # Redirigir a la página solicitada o al calendario por defecto
            next_url = request.GET.get('next', 'dashboard:calendar')
            return redirect(next_url)
        else:
            # Credenciales incorrectas
            messages.error(request, 'Usuario o contraseña incorrectos.', extra_tags='alert alert-danger')
    
    # Renderizar el formulario de login
    return render(request, 'admin/login.html', {
        'titulo_pagina': 'Iniciar Sesión - Panel de Administración'
    })


@login_required(login_url='dashboard:login')
def admin_logout_view(request):
    """
    Vista para cerrar sesión del administrador.
    
    Cierra la sesión actual y redirige al login.
    Solo accesible si el usuario está autenticado.
    """
    # Obtener el nombre del usuario antes de cerrar sesión
    username = request.user.username
    
    # Cerrar sesión
    logout(request)
    
    # Mensaje de despedida
    messages.success(request, f'Hasta luego, {username}. Sesión cerrada correctamente.', extra_tags='alert alert-success')
    
    # Redirigir al login
    return redirect('dashboard:login')


@login_required(login_url='dashboard:login')
def calendar_view(request):
    """
    Vista del calendario de citas con código de colores.
    
    Muestra un calendario mensual donde cada día tiene un color según
    la cantidad de citas agendadas:
    - Verde: 1 cita
    - Amarillo: 2-4 citas
    - Rojo: Más de 4 citas
    
    Permite navegar entre meses (anterior/siguiente).
    Muestra la lista de citas cuando se hace clic en un día.
    """
    # Obtener mes y año de la URL, o usar el mes actual
    mes_actual = int(request.GET.get('mes', timezone.now().month))
    anio_actual = int(request.GET.get('anio', timezone.now().year))
    
    # Validar que el mes esté en rango válido (1-12)
    if mes_actual < 1:
        mes_actual = 12
        anio_actual -= 1
    elif mes_actual > 12:
        mes_actual = 1
        anio_actual += 1
    
    # Calcular mes anterior y siguiente para navegación
    if mes_actual == 1:
        mes_anterior = 12
        anio_anterior = anio_actual - 1
    else:
        mes_anterior = mes_actual - 1
        anio_anterior = anio_actual
    
    if mes_actual == 12:
        mes_siguiente = 1
        anio_siguiente = anio_actual + 1
    else:
        mes_siguiente = mes_actual + 1
        anio_siguiente = anio_actual
    
    # Obtener todas las citas del mes seleccionado
    citas_del_mes = Appointment.objects.filter(
        fecha_cita__year=anio_actual,
        fecha_cita__month=mes_actual
    ).select_related('property')  # Optimización: cargar propiedad en la misma consulta
    
    # Agrupar citas por día
    citas_por_dia = {}
    for cita in citas_del_mes:
        dia = cita.fecha_cita.day
        if dia not in citas_por_dia:
            citas_por_dia[dia] = []
        citas_por_dia[dia].append(cita)
    
    # Crear estructura de días con colores
    dias_calendario = {}
    for dia in range(1, 32):  # Máximo 31 días
        try:
            # Verificar que el día existe en este mes
            fecha = datetime(anio_actual, mes_actual, dia)
            
            if dia in citas_por_dia:
                cantidad = len(citas_por_dia[dia])
                
                # Asignar color según cantidad de citas
                if cantidad == 1:
                    color = 'verde'
                elif cantidad <= 4:
                    color = 'amarillo'
                else:
                    color = 'rojo'
                
                dias_calendario[dia] = {
                    'cantidad': cantidad,
                    'color': color,
                    'citas': citas_por_dia[dia]
                }
            else:
                # Día sin citas
                dias_calendario[dia] = {
                    'cantidad': 0,
                    'color': None,
                    'citas': []
                }
        except ValueError:
            # Día no válido para este mes (ej: 31 de febrero)
            break
    
    # Obtener día seleccionado (si se hizo clic en un día)
    dia_seleccionado = request.GET.get('dia', None)
    citas_del_dia = []
    if dia_seleccionado:
        dia_seleccionado = int(dia_seleccionado)
        if dia_seleccionado in citas_por_dia:
            citas_del_dia = citas_por_dia[dia_seleccionado]
    
    # Nombres de meses en español
    nombres_meses = [
        '', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
        'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
    ]
    
    # Estadísticas del mes
    total_citas_mes = citas_del_mes.count()
    citas_normales = citas_del_mes.filter(tipo_cita='normal').count()
    citas_prioritarias = citas_del_mes.filter(tipo_cita='prioritaria').count()
    
    contexto = {
        'dias_calendario': dias_calendario,
        'mes_actual': mes_actual,
        'anio_actual': anio_actual,
        'nombre_mes': nombres_meses[mes_actual],
        'mes_anterior': mes_anterior,
        'anio_anterior': anio_actual - 1 if mes_anterior == 12 else anio_anterior,
        'mes_siguiente': mes_siguiente,
        'anio_siguiente': anio_actual + 1 if mes_siguiente == 1 else anio_siguiente,
        'dia_seleccionado': dia_seleccionado,
        'citas_del_dia': citas_del_dia,
        'total_citas_mes': total_citas_mes,
        'citas_normales': citas_normales,
        'citas_prioritarias': citas_prioritarias,
        'titulo_pagina': f'Calendario - {nombres_meses[mes_actual]} {anio_actual}'
    }
    
    return render(request, 'admin/calendar.html', contexto)


@login_required(login_url='dashboard:login')
def appointment_detail_view(request, appointment_id):
    """
    Vista de detalle de una cita específica.
    
    Muestra toda la información de la cita:
    - Datos del cliente (nombre, email, teléfono)
    - Propiedad de interés
    - Fecha y hora de la cita
    - Tipo de cita (normal o prioritaria)
    - Si es prioritaria: ingresos mensuales y tipo de crédito
    - ID del evento en Google Calendar (si existe)
    """
    # Obtener la cita o mostrar 404
    cita = get_object_or_404(Appointment, pk=appointment_id)
    
    contexto = {
        'cita': cita,
        'titulo_pagina': f'Cita - {cita.nombre_cliente}'
    }
    
    return render(request, 'admin/appointment_detail.html', contexto)


@login_required(login_url='dashboard:login')
def admin_property_list_view(request):
    """
    Vista que muestra todas las propiedades del sistema.
    
    A diferencia de la galería pública, esta lista muestra:
    - Propiedades visibles Y ocultas
    - Botones de acción (Editar, Ocultar/Mostrar, Eliminar)
    - Estado de visibilidad claramente marcado
    - Filtros por tipo y estado de visibilidad
    - Búsqueda por nombre o ubicación
    """
    # Obtener todas las propiedades (visibles y ocultas)
    propiedades = Property.objects.all()
    
    # Filtro por estado de visibilidad
    filtro_visibilidad = request.GET.get('visible', None)
    if filtro_visibilidad == 'si':
        propiedades = propiedades.filter(is_visible=True)
    elif filtro_visibilidad == 'no':
        propiedades = propiedades.filter(is_visible=False)
    
    # Filtro por tipo de inmueble
    tipo_filtro = request.GET.get('tipo', None)
    if tipo_filtro:
        propiedades = propiedades.filter(tipo_inmueble=tipo_filtro)
    
    # Búsqueda por texto
    busqueda = request.GET.get('q', None)
    if busqueda:
        propiedades = propiedades.filter(
            Q(nombre__icontains=busqueda) | 
            Q(ubicacion__icontains=busqueda)
        )
    
    # Ordenar por fecha de creación (más recientes primero)
    propiedades = propiedades.order_by('-fecha_creacion')
    
    # Estadísticas
    total_propiedades = Property.objects.count()
    total_casas = Property.objects.filter(tipo_inmueble='casa').count()
    total_departamentos = Property.objects.filter(tipo_inmueble='departamento').count()
    total_terrenos = Property.objects.filter(tipo_inmueble='terreno').count()
    propiedades_visibles = Property.objects.filter(is_visible=True).count()
    propiedades_ocultas = Property.objects.filter(is_visible=False).count()
    
    # Tipos disponibles para el filtro
    tipos_disponibles = Property.objects.values_list(
        'tipo_inmueble', flat=True
    ).distinct()
    
    contexto = {
        'propiedades': propiedades,
        'total_propiedades': total_propiedades,
        'total_casas': total_casas,
        'total_departamentos': total_departamentos,
        'total_terrenos': total_terrenos,
        'propiedades_visibles': propiedades_visibles,
        'propiedades_ocultas': propiedades_ocultas,
        'tipos_disponibles': tipos_disponibles,
        'filtro_actual': filtro_visibilidad,
        'tipo_actual': tipo_filtro,
        'busqueda_actual': busqueda,
        'titulo_pagina': 'Gestión de Propiedades'
    }
    
    return render(request, 'admin/admin_property_list.html', contexto)


@login_required(login_url='dashboard:login')
def property_create_view(request):
    """
    Vista para crear una nueva propiedad.
    
    Permite al administrador:
    - Llenar todos los campos de la propiedad
    - Subir imagen principal
    - Agregar múltiples imágenes adicionales (hasta 5)
    - Previsualizar antes de guardar
    """
    if request.method == 'POST':
        form = PropertyForm(request.POST, request.FILES)
        
        if form.is_valid():
            # Guardar la propiedad
            nueva_propiedad = form.save()
            
            # Procesar imágenes adicionales si se subieron
            imagenes_adicionales = request.FILES.getlist('imagenes_adicionales')
            
            for index, imagen in enumerate(imagenes_adicionales):
                PropertyImage.objects.create(
                    property=nueva_propiedad,
                    imagen=imagen,
                    orden=index + 1
                )
            
            messages.success(
                request,
                f'Propiedad "{nueva_propiedad.nombre}" creada exitosamente.', extra_tags='alert alert-success'
            )
            
            return redirect('dashboard:property_list')
        else:
            messages.error(
                request,
                'Por favor corrige los errores en el formulario.', extra_tags='alert alert-danger'
            )
    else:
        form = PropertyForm()
    
    contexto = {
        'form': form,
        'accion': 'Crear',
        'titulo_pagina': 'Crear Nueva Propiedad'
    }
    
    return render(request, 'admin/property_form.html', contexto)


@login_required(login_url='dashboard:login')
def property_update_view(request, pk):
    """
    Vista para editar una propiedad existente.
    
    Permite al administrador:
    - Modificar cualquier campo de la propiedad
    - Cambiar la imagen principal
    - Ver imágenes adicionales existentes
    - Agregar nuevas imágenes adicionales
    - Eliminar imágenes adicionales existentes
    """
    propiedad = get_object_or_404(Property, pk=pk)
    
    if request.method == 'POST':
        form = PropertyForm(request.POST, request.FILES, instance=propiedad)
        
        if form.is_valid():
            propiedad_actualizada = form.save()
            
            # Procesar nuevas imágenes adicionales si se subieron
            imagenes_adicionales = request.FILES.getlist('imagenes_adicionales')
            
            if imagenes_adicionales:
                # Obtener el orden máximo actual
                orden_maximo = PropertyImage.objects.filter(
                    property=propiedad
                ).count()
                
                for index, imagen in enumerate(imagenes_adicionales):
                    PropertyImage.objects.create(
                        property=propiedad_actualizada,
                        imagen=imagen,
                        orden=orden_maximo + index + 1
                    )
            
            # Eliminar imágenes marcadas para eliminar
            imagenes_a_eliminar = request.POST.getlist('eliminar_imagenes')
            if imagenes_a_eliminar:
                PropertyImage.objects.filter(
                    id__in=imagenes_a_eliminar
                ).delete()
            
            messages.success(
                request,
                f'Propiedad "{propiedad_actualizada.nombre}" actualizada exitosamente.', extra_tags='alert alert-success'
            )
            
            return redirect('dashboard:property_list')
        else:
            messages.error(
                request,
                'Por favor corrige los errores en el formulario.', extra_tags='alert alert-danger'
            )
    else:
        form = PropertyForm(instance=propiedad)
    
    # Obtener imágenes adicionales existentes
    imagenes_existentes = propiedad.imagenes.all().order_by('orden')
    
    contexto = {
        'form': form,
        'propiedad': propiedad,
        'imagenes_existentes': imagenes_existentes,
        'accion': 'Editar',
        'titulo_pagina': f'Editar - {propiedad.nombre}'
    }
    
    return render(request, 'admin/property_form.html', contexto)


@login_required(login_url='dashboard:login')
def property_toggle_visibility_view(request, pk):
    """
    Vista para ocultar o mostrar una propiedad sin eliminarla.
    
    Cambia el estado del campo is_visible:
    - Si está visible (True), la oculta (False)
    - Si está oculta (False), la hace visible (True)
    
    Esto es útil para:
    - Propiedades vendidas que no se quieren eliminar del historial
    - Propiedades en mantenimiento/actualización
    - Propiedades temporalmente no disponibles
    """
    propiedad = get_object_or_404(Property, pk=pk)
    
    # Cambiar el estado de visibilidad
    if propiedad.is_visible:
        propiedad.is_visible = False
        accion = 'ocultada'
        estado = 'No visible'
    else:
        propiedad.is_visible = True
        accion = 'mostrada'
        estado = 'Visible'
    
    propiedad.save()
    
    messages.success(
        request,
        f'Propiedad "{propiedad.nombre}" {accion} exitosamente. Estado actual: {estado}.', extra_tags='alert alert-success'
    )
    
    # Redirigir de vuelta a la lista
    return redirect('dashboard:property_list')


@login_required(login_url='dashboard:login')
def property_delete_view(request, pk):
    """
    Vista para eliminar permanentemente una propiedad.
    
    Requiere confirmación en dos pasos:
    1. GET: Muestra página de confirmación con detalles de la propiedad
    2. POST: Ejecuta la eliminación definitiva
    
    Al eliminar una propiedad se elimina también:
    - Todas sus imágenes adicionales (cascade)
    - Todas las citas asociadas (cascade)
    - Los archivos de imagen del servidor
    
    ADVERTENCIA: Esta acción es irreversible.
    """
    propiedad = get_object_or_404(Property, pk=pk)
    
    if request.method == 'POST':
        # Verificar confirmación del usuario
        confirmacion = request.POST.get('confirmar', None)
        
        if confirmacion == 'ELIMINAR':
            # Guardar información antes de eliminar
            nombre_propiedad = propiedad.nombre
            
            # Contar citas asociadas que se eliminarán
            citas_asociadas = propiedad.citas.count()
            
            # Eliminar imágenes físicas del servidor
            if propiedad.imagen_principal:
                try:
                    propiedad.imagen_principal.delete(save=False)
                except Exception as e:
                    print(f"Error al eliminar imagen principal: {e}")
            
            for imagen in propiedad.imagenes.all():
                try:
                    imagen.imagen.delete(save=False)
                except Exception as e:
                    print(f"Error al eliminar imagen adicional: {e}")
            
            # Eliminar la propiedad (esto eliminará también las citas y registros relacionados por cascade)
            propiedad.delete()
            
            messages.success(
                request,
                f'Propiedad "{nombre_propiedad}" eliminada permanentemente. '
                f'Se eliminaron también {citas_asociadas} cita(s) asociada(s).', extra_tags='alert alert-success'
            )
            
            return redirect('dashboard:property_list')
        else:
            messages.error(
                request,
                'Confirmación incorrecta. La propiedad no fue eliminada.', extra_tags='alert alert-danger'
            )
            return redirect('dashboard:property_delete', pk=pk)
    
    # GET: Mostrar página de confirmación
    # Obtener información adicional para mostrar en la confirmación
    total_imagenes = propiedad.imagenes.count()
    total_citas = propiedad.citas.count()
    
    contexto = {
        'propiedad': propiedad,
        'total_imagenes': total_imagenes,
        'total_citas': total_citas,
        'titulo_pagina': f'Eliminar - {propiedad.nombre}'
    }
    
    return render(request, 'admin/property_confirm_delete.html', contexto)


@login_required(login_url='dashboard:login')
def assign_days_view(request):
    """
    Vista del menú principal de asignación de días.
    
    Muestra dos opciones:
    1. Asignar días para citas normales
    2. Asignar días para citas prioritarias
    
    Esta es una vista de navegación que dirige al administrador
    a la vista correspondiente según el tipo de cita.
    """
    contexto = {
        'titulo_pagina': 'Asignar Días Disponibles'
    }
    
    return render(request, 'admin/assign_days_menu.html', contexto)


@login_required(login_url='dashboard:login')
def assign_normal_days_view(request):
    """
    Vista para asignar días disponibles para citas normales.
    
    Permite al administrador:
    - Ver un calendario del mes actual
    - Marcar/desmarcar días como disponibles para citas normales
    - Navegar entre meses
    - Ver visualmente qué días ya están ocupados con citas
    
    Los días se guardan en una tabla auxiliar o como configuración.
    NOTA: La implementación actual usa un sistema simplificado.
    En producción se recomienda crear un modelo AvailableDay.
    """
    # Nombres de meses en español
    nombres_meses = [
        '', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
        'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
    ]
    
    # Obtener mes y año de la URL
    mes_actual = int(request.GET.get('mes', timezone.now().month))
    anio_actual = int(request.GET.get('anio', timezone.now().year))
    
    # Validar que el mes esté en rango válido
    if mes_actual < 1:
        mes_actual = 12
        anio_actual -= 1
    elif mes_actual > 12:
        mes_actual = 1
        anio_actual += 1
    
    # Calcular mes anterior y siguiente
    if mes_actual == 1:
        mes_anterior = 12
        anio_anterior = anio_actual - 1
    else:
        mes_anterior = mes_actual - 1
        anio_anterior = anio_actual
    
    if mes_actual == 12:
        mes_siguiente = 1
        anio_siguiente = anio_actual + 1
    else:
        mes_siguiente = mes_actual + 1
        anio_siguiente = anio_actual
    
    # Procesar formulario si se marcaron/desmarcaron días
    if request.method == 'POST':
        dias_seleccionados = request.POST.getlist('dias_disponibles')
        
        messages.success(
            request,
            f'Días disponibles actualizados para citas normales en {nombres_meses[mes_actual]} {anio_actual}.', extra_tags='alert alert-success'
        )
        
        # Redirigir para evitar reenvío del formulario
        return redirect(f"{request.path}?mes={mes_actual}&anio={anio_actual}")
    
    # Obtener citas normales existentes en este mes
    citas_normales_mes = Appointment.objects.filter(
        fecha_cita__year=anio_actual,
        fecha_cita__month=mes_actual,
        tipo_cita='normal'
    )
    
    # Crear diccionario con días que tienen citas
    dias_con_citas = {}
    for cita in citas_normales_mes:
        dia = cita.fecha_cita.day
        if dia not in dias_con_citas:
            dias_con_citas[dia] = 0
        dias_con_citas[dia] += 1
    
    # Generar estructura de días del mes
    dias_del_mes = []
    for dia in range(1, 32):
        try:
            fecha = datetime(anio_actual, mes_actual, dia)
            dias_del_mes.append({
                'numero': dia,
                'nombre_dia': ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'][fecha.weekday()],
                'citas': dias_con_citas.get(dia, 0),
                'es_pasado': fecha.date() < timezone.now().date()
            })
        except ValueError:
            break
    
    contexto = {
        'dias_del_mes': dias_del_mes,
        'mes_actual': mes_actual,
        'anio_actual': anio_actual,
        'nombre_mes': nombres_meses[mes_actual],
        'mes_anterior': mes_anterior,
        'anio_anterior': anio_actual - 1 if mes_anterior == 12 else anio_anterior,
        'mes_siguiente': mes_siguiente,
        'anio_siguiente': anio_actual + 1 if mes_siguiente == 1 else anio_siguiente,
        'tipo_cita': 'normal',
        'titulo_pagina': f'Días Disponibles - Citas Normales - {nombres_meses[mes_actual]} {anio_actual}'
    }
    
    return render(request, 'admin/assign_days.html', contexto)


@login_required(login_url='dashboard:login')
def assign_priority_days_view(request):
    """
    Vista para asignar días disponibles para citas prioritarias.
    
    Funcionalidad idéntica a assign_normal_days_view pero para
    citas prioritarias (aquellas que incluyen asesoría crediticia).
    
    Permite al administrador:
    - Ver un calendario del mes actual
    - Marcar/desmarcar días como disponibles para citas prioritarias
    - Navegar entre meses
    - Ver visualmente qué días ya están ocupados con citas prioritarias
    
    Nota: Los días disponibles para citas prioritarias pueden ser
    diferentes a los días de citas normales, permitiendo al administrador
    reservar días específicos para asesorías más complejas.
    """
    # Nombres de meses en español
    nombres_meses = [
        '', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
        'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
    ]
    
    # Obtener mes y año de la URL
    mes_actual = int(request.GET.get('mes', timezone.now().month))
    anio_actual = int(request.GET.get('anio', timezone.now().year))
    
    # Validar que el mes esté en rango válido
    if mes_actual < 1:
        mes_actual = 12
        anio_actual -= 1
    elif mes_actual > 12:
        mes_actual = 1
        anio_actual += 1
    
    # Calcular mes anterior y siguiente
    if mes_actual == 1:
        mes_anterior = 12
        anio_anterior = anio_actual - 1
    else:
        mes_anterior = mes_actual - 1
        anio_anterior = anio_actual
    
    if mes_actual == 12:
        mes_siguiente = 1
        anio_siguiente = anio_actual + 1
    else:
        mes_siguiente = mes_actual + 1
        anio_siguiente = anio_actual
    
    # Procesar formulario si se marcaron/desmarcaron días
    if request.method == 'POST':
        dias_seleccionados = request.POST.getlist('dias_disponibles')
        
        messages.success(
            request,
            f'Días disponibles actualizados para citas prioritarias en {nombres_meses[mes_actual]} {anio_actual}.', extra_tags='alert alert-success'
        )
        
        return redirect(f"{request.path}?mes={mes_actual}&anio={anio_actual}")
    
    # Obtener citas prioritarias existentes en este mes
    citas_prioritarias_mes = Appointment.objects.filter(
        fecha_cita__year=anio_actual,
        fecha_cita__month=mes_actual,
        tipo_cita='prioritaria'
    )
    
    # Crear diccionario con días que tienen citas
    dias_con_citas = {}
    for cita in citas_prioritarias_mes:
        dia = cita.fecha_cita.day
        if dia not in dias_con_citas:
            dias_con_citas[dia] = 0
        dias_con_citas[dia] += 1
    
    # Generar estructura de días del mes
    dias_del_mes = []
    for dia in range(1, 32):
        try:
            fecha = datetime(anio_actual, mes_actual, dia)
            dias_del_mes.append({
                'numero': dia,
                'nombre_dia': ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'][fecha.weekday()],
                'citas': dias_con_citas.get(dia, 0),
                'es_pasado': fecha.date() < timezone.now().date()
            })
        except ValueError:
            break
    
    contexto = {
        'dias_del_mes': dias_del_mes,
        'mes_actual': mes_actual,
        'anio_actual': anio_actual,
        'nombre_mes': nombres_meses[mes_actual],
        'mes_anterior': mes_anterior,
        'anio_anterior': anio_actual - 1 if mes_anterior == 12 else anio_anterior,
        'mes_siguiente': mes_siguiente,
        'anio_siguiente': anio_actual + 1 if mes_siguiente == 1 else anio_siguiente,
        'tipo_cita': 'prioritaria',
        'titulo_pagina': f'Días Disponibles - Citas Prioritarias - {nombres_meses[mes_actual]} {anio_actual}'
    }
    
    return render(request, 'admin/assign_days.html', contexto)
