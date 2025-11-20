from django.contrib import admin
from .models import Appointment, AvailableDay


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    """
    Configuración del panel de administración de Django para el modelo Appointment.
    Permite gestionar las citas desde el admin nativo de Django.
    """
    list_display = ['nombre_cliente', 'property', 'fecha_cita', 'tipo_cita', 'get_capacidad_info']
    list_filter = ['tipo_cita', 'fecha_cita']
    search_fields = ['nombre_cliente', 'email_cliente', 'property__nombre']
    date_hierarchy = 'fecha_cita'
    readonly_fields = ['fecha_creacion', 'google_event_id']
    
    fieldsets = (
        ('Información del Cliente', {
            'fields': ('nombre_cliente', 'email_cliente', 'telefono_cliente')
        }),
        ('Detalles de la Cita', {
            'fields': ('property', 'fecha_cita', 'tipo_cita')
        }),
        ('Información Financiera (Citas Prioritarias)', {
            'fields': ('ingresos_mensuales', 'tipo_credito'),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('fecha_creacion', 'google_event_id'),
            'classes': ('collapse',)
        }),
    )
    
    def get_capacidad_info(self, obj):
        """
        Muestra información sobre la disponibilidad del día de la cita.
        
        Args:
            obj: Instancia del modelo Appointment
            
        Returns:
            str: Información de capacidad formateada
        """
        try:
            dia_disponible = AvailableDay.objects.get(
                fecha_disponible=obj.fecha_cita.date(),
                tipo_cita=obj.tipo_cita
            )
            capacidad_disponible = dia_disponible.obtener_capacidad_disponible()
            capacidad_maxima = dia_disponible.capacidad_maxima
            return f"{capacidad_disponible}/{capacidad_maxima} disponibles"
        except AvailableDay.DoesNotExist:
            return "⚠️ Día no configurado"
    
    get_capacidad_info.short_description = 'Capacidad del Día'


@admin.register(AvailableDay)
class AvailableDayAdmin(admin.ModelAdmin):
    """
    Configuración del panel de administración de Django para el modelo AvailableDay.
    Permite gestionar los días disponibles desde el admin nativo de Django.
    """
    list_display = ['fecha_disponible', 'tipo_cita', 'capacidad_maxima', 
                    'get_citas_agendadas', 'get_capacidad_disponible', 'get_estado']
    list_filter = ['tipo_cita', 'fecha_disponible']
    search_fields = ['notas_admin']
    date_hierarchy = 'fecha_disponible'
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion', 
                      'get_citas_agendadas_detail', 'get_estado_detail']
    
    fieldsets = (
        ('Configuración del Día', {
            'fields': ('fecha_disponible', 'tipo_cita', 'capacidad_maxima')
        }),
        ('Notas', {
            'fields': ('notas_admin',),
        }),
        ('Información de Estado', {
            'fields': ('get_citas_agendadas_detail', 'get_estado_detail'),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )
    
    def get_citas_agendadas(self, obj):
        """
        Muestra el número de citas agendadas para este día.
        
        Args:
            obj: Instancia del modelo AvailableDay
            
        Returns:
            int: Número de citas agendadas
        """
        return obj.obtener_citas_agendadas().count()
    
    get_citas_agendadas.short_description = 'Citas Agendadas'
    
    def get_capacidad_disponible(self, obj):
        """
        Muestra la capacidad disponible de este día.
        
        Args:
            obj: Instancia del modelo AvailableDay
            
        Returns:
            int: Espacios disponibles
        """
        return obj.obtener_capacidad_disponible()
    
    get_capacidad_disponible.short_description = 'Espacios Disponibles'
    
    def get_estado(self, obj):
        """
        Muestra el estado del día (disponible, lleno, pasado).
        
        Args:
            obj: Instancia del modelo AvailableDay
            
        Returns:
            str: Estado formateado con emoji
        """
        if obj.esta_en_el_pasado():
            return "⏰ Pasado"
        elif obj.esta_disponible():
            return "✅ Disponible"
        else:
            return "❌ Lleno"
    
    get_estado.short_description = 'Estado'
    
    def get_citas_agendadas_detail(self, obj):
        """
        Muestra información detallada sobre las citas agendadas.
        
        Args:
            obj: Instancia del modelo AvailableDay
            
        Returns:
            str: Información detallada en formato HTML
        """
        citas = obj.obtener_citas_agendadas()
        if not citas.exists():
            return "No hay citas agendadas"
        
        html = "<ul>"
        for cita in citas:
            html += f"<li>{cita.nombre_cliente} - {cita.property.nombre} - {cita.fecha_cita.strftime('%H:%M')}</li>"
        html += "</ul>"
        return html
    
    get_citas_agendadas_detail.short_description = 'Detalle de Citas'
    get_citas_agendadas_detail.allow_tags = True
    
    def get_estado_detail(self, obj):
        """
        Muestra información detallada del estado del día.
        
        Args:
            obj: Instancia del modelo AvailableDay
            
        Returns:
            str: Información de estado detallada
        """
        citas_count = obj.obtener_citas_agendadas().count()
        capacidad_disp = obj.obtener_capacidad_disponible()
        
        info = f"<strong>Capacidad máxima:</strong> {obj.capacidad_maxima}<br>"
        info += f"<strong>Citas agendadas:</strong> {citas_count}<br>"
        info += f"<strong>Espacios disponibles:</strong> {capacidad_disp}<br>"
        info += f"<strong>Estado:</strong> "
        
        if obj.esta_en_el_pasado():
            info += "⏰ Este día ya pasó"
        elif obj.esta_disponible():
            info += "✅ Disponible para nuevas citas"
        else:
            info += "❌ Capacidad máxima alcanzada"
        
        return info
    
    get_estado_detail.short_description = 'Estado Detallado'
    get_estado_detail.allow_tags = True
    
    actions = ['marcar_como_no_disponible', 'aumentar_capacidad']
    
    def marcar_como_no_disponible(self, request, queryset):
        """
        Acción personalizada para eliminar días disponibles seleccionados.
        
        Args:
            request: HttpRequest
            queryset: QuerySet de días seleccionados
        """
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f'{count} día(s) marcado(s) como no disponible(s).')
    
    marcar_como_no_disponible.short_description = "❌ Marcar como no disponible"
    
    def aumentar_capacidad(self, request, queryset):
        """
        Acción personalizada para aumentar la capacidad de días seleccionados.
        
        Args:
            request: HttpRequest
            queryset: QuerySet de días seleccionados
        """
        for dia in queryset:
            dia.capacidad_maxima += 1
            dia.save()
        self.message_user(request, f'Capacidad aumentada en {queryset.count()} día(s).')
    
    aumentar_capacidad.short_description = "➕ Aumentar capacidad en 1"
