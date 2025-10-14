from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Página principal con carousel de propiedades destacadas
    path('', views.home_view, name='home'),
    
    # Página de servicios con formulario de asesoría crediticia
    path('servicios/', views.services_view, name='services'),
    
    # Procesar formulario de asesoría crediticia
    path('servicios/asesoria/', views.credit_advice_view, name='credit_advice'),
]