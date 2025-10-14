from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Login personalizado para el administrador
    path('login/', views.admin_login_view, name='login'),
    
    # Logout del administrador
    path('logout/', views.admin_logout_view, name='logout'),
    
    # Calendario de citas con código de colores
    path('calendario/', views.calendar_view, name='calendar'),
    
    # Ver detalles de una cita específica
    path('cita/<int:appointment_id>/', views.appointment_detail_view, name='appointment_detail'),
    
    # CRUD de propiedades
    path('propiedades/', views.admin_property_list_view, name='property_list'),
    path('propiedades/crear/', views.property_create_view, name='property_create'),
    path('propiedades/editar/<int:pk>/', views.property_update_view, name='property_update'),
    path('propiedades/ocultar/<int:pk>/', views.property_toggle_visibility_view, name='property_toggle'),
    path('propiedades/eliminar/<int:pk>/', views.property_delete_view, name='property_delete'),
    
    # Asignar días disponibles para citas
    path('asignar-dias/', views.assign_days_view, name='assign_days'),
    path('asignar-dias/normal/', views.assign_normal_days_view, name='assign_normal_days'),
    path('asignar-dias/prioritaria/', views.assign_priority_days_view, name='assign_priority_days'),
]