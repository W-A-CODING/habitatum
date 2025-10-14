from django import forms
from .models import Property, PropertyImage

class PropertyForm(forms.ModelForm):
    """
    Formulario para crear y editar propiedades desde el panel de administración.
    Incluye todos los campos necesarios para registrar una nueva propiedad.
    """
    
    class Meta:
        model = Property
        fields = [
            'nombre',
            'descripcion',
            'metros_cuadrados',
            'tipo_inmueble',
            'ubicacion',
            'precio',
            'imagen_principal',
            'is_visible',
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Casa en Lomas de Angelópolis'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Describe las características principales de la propiedad...'
            }),
            'metros_cuadrados': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 120.50',
                'step': '0.01'
            }),
            'tipo_inmueble': forms.Select(attrs={
                'class': 'form-control'
            }),
            'ubicacion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Col. Lomas de Angelópolis, Puebla'
            }),
            'precio': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 2500000',
                'step': '0.01'
            }),
            'imagen_principal': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'is_visible': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'nombre': 'Nombre de la Propiedad',
            'descripcion': 'Descripción',
            'metros_cuadrados': 'Metros Cuadrados (m²)',
            'tipo_inmueble': 'Tipo de Inmueble',
            'ubicacion': 'Ubicación',
            'precio': 'Precio (MXN)',
            'imagen_principal': 'Imagen Principal',
            'is_visible': 'Visible en el sitio público',
        }
    
    def clean_precio(self):
        """
        Valida que el precio sea mayor a cero.
        """
        precio = self.cleaned_data.get('precio')
        if precio <= 0:
            raise forms.ValidationError('El precio debe ser mayor a cero.')
        return precio
    
    def clean_metros_cuadrados(self):
        """
        Valida que los metros cuadrados sean mayores a cero.
        """
        metros = self.cleaned_data.get('metros_cuadrados')
        if metros <= 0:
            raise forms.ValidationError('Los metros cuadrados deben ser mayores a cero.')
        return metros


class PropertyImageForm(forms.ModelForm):
    """
    Formulario para añadir imágenes adicionales a una propiedad.
    Se usa en conjunto con PropertyForm mediante formsets.
    """
    
    class Meta:
        model = PropertyImage
        fields = ['imagen', 'orden']
        widgets = {
            'imagen': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'orden': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Orden de visualización',
                'min': '0'
            }),
        }
        labels = {
            'imagen': 'Imagen',
            'orden': 'Orden',
        }