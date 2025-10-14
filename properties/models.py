from django.db import models
from django.core.validators import MinValueValidator

class Property(models.Model):
    """Modelo que representa una propiedad inmobiliaria"""
    
    PROPERTY_TYPES = [
        ('casa', 'Casa'),
        ('departamento', 'Departamento'),
        ('terreno', 'Terreno'),
        ('local', 'Local Comercial'),
    ]
    
    # Campos básicos
    nombre = models.CharField(max_length=200, verbose_name="Nombre de la Propiedad")
    descripcion = models.TextField(verbose_name="Descripción")
    metros_cuadrados = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Metros Cuadrados (m²)"
    )
    tipo_inmueble = models.CharField(
        max_length=50, 
        choices=PROPERTY_TYPES,
        verbose_name="Tipo de Inmueble"
    )
    ubicacion = models.CharField(max_length=300, verbose_name="Ubicación")
    precio = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Precio"
    )
    imagen_principal = models.ImageField(
        upload_to='properties/',
        verbose_name="Imagen Principal"
    )
    is_visible = models.BooleanField(
        default=True,
        verbose_name="Visible en el sitio público"
    )
    
    # Metadatos
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Propiedad"
        verbose_name_plural = "Propiedades"
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"{self.nombre} - {self.ubicacion}"


class PropertyImage(models.Model):
    """Modelo para múltiples imágenes de una propiedad"""
    
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='imagenes',
        verbose_name="Propiedad"
    )
    imagen = models.ImageField(
        upload_to='properties/',
        verbose_name="Imagen"
    )
    orden = models.PositiveIntegerField(default=0, verbose_name="Orden de visualización")
    
    class Meta:
        verbose_name = "Imagen de Propiedad"
        verbose_name_plural = "Imágenes de Propiedades"
        ordering = ['orden']
    
    def __str__(self):
        return f"Imagen de {self.property.nombre}"
