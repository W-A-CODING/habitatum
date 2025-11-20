from django.db import models
from django.core.validators import MinValueValidator
from properties.models import Property

class AvailableDay(models.Model):
    """
    Modelo para gestionar los días disponibles para agendar citas.
    Permite al administrador seleccionar qué días están disponibles 
    para cada tipo de cita (normal o prioritaria).
    """
    
    APPOINTMENT_TYPE_CHOICES = [
        ('normal', 'Cita Normal'),
        ('prioritaria', 'Cita Prioritaria'),
    ]
    
    # Fecha del día disponible
    fecha_disponible = models.DateField(
        verbose_name="Fecha Disponible",
        help_text="Día en el que se pueden agendar citas"
    )
    
    # Tipo de cita permitida en este día
    tipo_cita = models.CharField(
        max_length=20,
        choices=APPOINTMENT_TYPE_CHOICES,
        verbose_name="Tipo de Cita"
    )
    
    # Control de capacidad
    capacidad_maxima = models.PositiveIntegerField(
        default=3,
        validators=[MinValueValidator(1)],
        verbose_name="Capacidad Máxima",
        help_text="Número máximo de citas permitidas en este día"
    )
    
    # Notas del administrador
    notas_admin = models.TextField(
        blank=True,
        verbose_name="Notas del Administrador",
        help_text="Notas internas sobre la disponibilidad de este día"
    )
    
    # Metadatos
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Día Disponible"
        verbose_name_plural = "Días Disponibles"
        ordering = ['fecha_disponible', 'tipo_cita']
        # Evitar duplicados: una fecha no puede tener el mismo tipo dos veces
        unique_together = [['fecha_disponible', 'tipo_cita']]
        indexes = [
            models.Index(fields=['fecha_disponible', 'tipo_cita']),
        ]
    
    def __str__(self):
        return f"{self.fecha_disponible.strftime('%d/%m/%Y')} - {self.get_tipo_cita_display()}"
    
    def obtener_citas_agendadas(self):
        """
        Retorna las citas ya agendadas para esta fecha y tipo.
        
        Returns:
            QuerySet: Citas que coinciden con la fecha y tipo de este día disponible
        """
        return Appointment.objects.filter(
            fecha_cita__date=self.fecha_disponible,
            tipo_cita=self.tipo_cita
        )
    
    def obtener_capacidad_disponible(self):
        """
        Calcula cuántas citas más se pueden agendar en este día.
        
        Returns:
            int: Número de espacios disponibles
        """
        citas_agendadas = self.obtener_citas_agendadas().count()
        return max(0, self.capacidad_maxima - citas_agendadas)
    
    def esta_disponible(self):
        """
        Verifica si todavía hay espacio disponible para más citas.
        
        Returns:
            bool: True si hay espacio disponible, False si está lleno
        """
        return self.obtener_capacidad_disponible() > 0
    
    def esta_en_el_pasado(self):
        """
        Verifica si esta fecha ya pasó.
        
        Returns:
            bool: True si la fecha es anterior a hoy
        """
        from django.utils import timezone
        return self.fecha_disponible < timezone.now().date()


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
