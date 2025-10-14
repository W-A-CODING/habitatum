from django.contrib import admin
from .models import Appointment

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['nombre_cliente', 'property', 'fecha_cita', 'tipo_cita']
    list_filter = ['tipo_cita', 'fecha_cita']
    search_fields = ['nombre_cliente', 'email_cliente', 'property__nombre']
    date_hierarchy = 'fecha_cita'
