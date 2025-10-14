from django.db import models
from django.contrib.auth.models import User

class GoogleApiToken(models.Model):
    """Modelo para almacenar tokens de OAuth2 de Google Calendar"""
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        verbose_name="Usuario Administrador"
    )
    token = models.TextField(verbose_name="Token de Acceso")
    refresh_token = models.TextField(verbose_name="Token de Actualización")
    token_uri = models.CharField(max_length=300, verbose_name="URI del Token")
    client_id = models.CharField(max_length=300, verbose_name="Client ID")
    client_secret = models.CharField(max_length=300, verbose_name="Client Secret")
    scopes = models.TextField(verbose_name="Scopes (permisos)")
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Token de Google API"
        verbose_name_plural = "Tokens de Google API"
    
    def __str__(self):
        return f"Token de {self.user.username}"
