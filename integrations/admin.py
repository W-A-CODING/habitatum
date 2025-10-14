from django.contrib import admin
from .models import GoogleApiToken

@admin.register(GoogleApiToken)
class GoogleApiTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'fecha_actualizacion']
