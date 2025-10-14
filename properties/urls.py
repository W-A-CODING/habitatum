from django.urls import path
from . import views

app_name = 'properties'

urlpatterns = [
    # Galería de propiedades (todas las visibles)
    path('', views.property_list_view, name='property_list'),
    
    # Detalle de una propiedad específica con galería de imágenes
    path('<int:pk>/', views.property_detail_view, name='property_detail'),
]