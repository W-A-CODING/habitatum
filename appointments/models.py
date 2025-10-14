from django.db import models
from django.core.validators import MinValueValidator
from properties.models import Property

class Appointment(models.Model):
    """Modelo para gestionar citas de visitas a propiedades"""
    
    APPOINTMENT_TYPES = [
        ('normal', 'Cita Normal'),
        ('prioritaria', 'Cita Prioritaria'),
    ]
    
    CREDIT_TYPES = [
        ('infonavit', 'Infonavit'),
        ('fovissste', 'Fovissste'),
        ('bancario', 'Crédito Bancario'),
        ('contado', 'Contado'),
    ]
    
    # Relación con la propiedad
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='citas',
        verbose_name="Propiedad"
    )
    
    # Datos del cliente
    nombre_cliente = models.CharField(max_length=200, verbose_name="Nombre del Cliente")
    email_cliente = models.EmailField(verbose_name="Email del Cliente")
    telefono_cliente = models.CharField(max_length=20, verbose_name="Teléfono")
    
    # Datos de la cita
    fecha_cita = models.DateTimeField(verbose_name="Fecha y Hora de la Cita")
    tipo_cita = models.CharField(
        max_length=20,
        choices=APPOINTMENT_TYPES,
        default='normal',
        verbose_name="Tipo de Cita"
    )
    
    # Campos específicos para citas prioritarias
    ingresos_mensuales = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name="Ingresos Mensuales"
    )
    tipo_credito = models.CharField(
        max_length=20,
        choices=CREDIT_TYPES,
        null=True,
        blank=True,
        verbose_name="Tipo de Crédito"
    )
    
    # Metadatos
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    google_event_id = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        verbose_name="ID del Evento en Google Calendar"
    )
    
    class Meta:
        verbose_name = "Cita"
        verbose_name_plural = "Citas"
        ordering = ['fecha_cita']
    
    def __str__(self):
        return f"Cita de {self.nombre_cliente} - {self.property.nombre} - {self.fecha_cita}"
