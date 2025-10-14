from django.urls import path
from . import views

app_name = 'appointments'

urlpatterns = [
    # Agendar cita normal para una propiedad específica
    path('agendar/normal/<int:property_id>/', views.create_normal_appointment_view, name='create_normal'),
    
    # Agendar cita prioritaria para una propiedad específica
    path('agendar/prioritaria/<int:property_id>/', views.create_priority_appointment_view, name='create_priority'),
    
    # Página de confirmación después de agendar una cita
    path('confirmacion/', views.appointment_confirmation_view, name='confirmation'),
]