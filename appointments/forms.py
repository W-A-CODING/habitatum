from django import forms
from .models import Appointment
from properties.models import Property

class NormalAppointmentForm(forms.ModelForm):
    """
    Formulario para agendar una cita normal.
    Solo requiere datos básicos del cliente y la fecha deseada.
    El sistema identificará automáticamente la propiedad de interés.
    """
    
    class Meta:
        model = Appointment
        fields = [
            'nombre_cliente',
            'email_cliente',
            'telefono_cliente',
            'fecha_cita',
        ]
        widgets = {
            'nombre_cliente': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tu nombre completo',
                'required': True
            }),
            'email_cliente': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'tu_email@ejemplo.com',
                'required': True
            }),
            'telefono_cliente': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 2221234567',
                'required': True
            }),
            'fecha_cita': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
        }
        labels = {
            'nombre_cliente': 'Nombre Completo',
            'email_cliente': 'Correo Electrónico',
            'telefono_cliente': 'Teléfono',
            'fecha_cita': 'Fecha de la Cita',
        }
    
    def __init__(self, *args, **kwargs):
        """
        Inicializa el formulario y establece el tipo de cita como 'normal'.
        """
        super().__init__(*args, **kwargs)
        if self.instance:
            self.instance.tipo_cita = 'normal'
    
    def clean_telefono_cliente(self):
        """
        Valida que el teléfono contenga solo números y tenga al menos 10 dígitos.
        """
        telefono = self.cleaned_data.get('telefono_cliente')
        # Eliminar espacios y guiones
        telefono_limpio = telefono.replace(' ', '').replace('-', '')
        
        if not telefono_limpio.isdigit():
            raise forms.ValidationError('El teléfono debe contener solo números.')
        
        if len(telefono_limpio) < 10:
            raise forms.ValidationError('El teléfono debe tener al menos 10 dígitos.')
        
        return telefono


class PriorityAppointmentForm(forms.ModelForm):
    """
    Formulario para agendar una cita prioritaria.
    Requiere datos adicionales sobre ingresos y tipo de crédito
    para ofrecer asesoramiento crediticio especializado.
    """
    
    class Meta:
        model = Appointment
        fields = [
            'nombre_cliente',
            'email_cliente',
            'telefono_cliente',
            'fecha_cita',
            'ingresos_mensuales',
            'tipo_credito',
        ]
        widgets = {
            'nombre_cliente': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tu nombre completo',
                'required': True
            }),
            'email_cliente': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'tu_email@ejemplo.com',
                'required': True
            }),
            'telefono_cliente': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 2221234567',
                'required': True
            }),
            'fecha_cita': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'ingresos_mensuales': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 15000',
                'step': '0.01',
                'required': True
            }),
            'tipo_credito': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
        }
        labels = {
            'nombre_cliente': 'Nombre Completo',
            'email_cliente': 'Correo Electrónico',
            'telefono_cliente': 'Teléfono',
            'fecha_cita': 'Fecha de la Cita',
            'ingresos_mensuales': 'Ingresos Mensuales (MXN)',
            'tipo_credito': 'Tipo de Crédito',
        }
    
    def __init__(self, *args, **kwargs):
        """
        Inicializa el formulario y establece el tipo de cita como 'prioritaria'.
        """
        super().__init__(*args, **kwargs)
        if self.instance:
            self.instance.tipo_cita = 'prioritaria'
    
    def clean_telefono_cliente(self):
        """
        Valida que el teléfono contenga solo números y tenga al menos 10 dígitos.
        """
        telefono = self.cleaned_data.get('telefono_cliente')
        telefono_limpio = telefono.replace(' ', '').replace('-', '')
        
        if not telefono_limpio.isdigit():
            raise forms.ValidationError('El teléfono debe contener solo números.')
        
        if len(telefono_limpio) < 10:
            raise forms.ValidationError('El teléfono debe tener al menos 10 dígitos.')
        
        return telefono
    
    def clean_ingresos_mensuales(self):
        """
        Valida que los ingresos mensuales sean mayores a cero.
        """
        ingresos = self.cleaned_data.get('ingresos_mensuales')
        if ingresos <= 0:
            raise forms.ValidationError('Los ingresos mensuales deben ser mayores a cero.')
        return ingresos