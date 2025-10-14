from django import forms

class CreditAdviceForm(forms.Form):
    """
    Formulario para solicitar asesoría crediticia desde la página de servicios.
    No crea un registro en la base de datos, solo envía un email al administrador.
    """
    
    nombre = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tu nombre completo',
            'required': True
        }),
        label='Nombre Completo'
    )
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'tu_email@ejemplo.com',
            'required': True
        }),
        label='Correo Electrónico'
    )
    
    telefono = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 2221234567',
            'required': True
        }),
        label='Teléfono'
    )
    
    ingresos_mensuales = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 15000',
            'step': '0.01',
            'required': True
        }),
        label='Ingresos Mensuales (MXN)'
    )
    
    tipo_credito = forms.ChoiceField(
        choices=[
            ('', 'Selecciona una opción'),
            ('infonavit', 'Infonavit'),
            ('fovissste', 'Fovissste'),
            ('bancario', 'Crédito Bancario'),
            ('contado', 'Contado'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-control',
            'required': True
        }),
        label='Tipo de Crédito'
    )
    
    mensaje = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': '¿Tienes alguna pregunta o comentario adicional? (Opcional)'
        }),
        label='Mensaje Adicional'
    )
    
    def clean_telefono(self):
        """
        Valida que el teléfono contenga solo números y tenga al menos 10 dígitos.
        """
        telefono = self.cleaned_data.get('telefono')
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
    
    def clean_tipo_credito(self):
        """
        Valida que se haya seleccionado un tipo de crédito válido.
        """
        tipo_credito = self.cleaned_data.get('tipo_credito')
        if not tipo_credito:
            raise forms.ValidationError('Por favor selecciona un tipo de crédito.')
        return tipo_credito