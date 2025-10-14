from django.contrib import admin
from .models import Property, PropertyImage

class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 3

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'tipo_inmueble', 'precio', 'ubicacion', 'is_visible']
    list_filter = ['tipo_inmueble', 'is_visible']
    search_fields = ['nombre', 'ubicacion']
    inlines = [PropertyImageInline]

@admin.register(PropertyImage)
class PropertyImageAdmin(admin.ModelAdmin):
    list_display = ['property', 'orden']
    list_filter = ['property']
