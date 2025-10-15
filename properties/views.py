from django.shortcuts import render, get_object_or_404
from django.db.models import Q

from .models import Property, PropertyImage


def property_list_view(request):
    """
    Vista de la galería de propiedades.
    Muestra todas las propiedades visibles en formato de tarjetas.
    
    Funcionalidades:
    - Lista todas las propiedades con is_visible=True
    - Las ordena por fecha de creación (más recientes primero)
    - Opcionalmente permite filtrar por tipo de inmueble
    - Opcionalmente permite buscar por nombre o ubicación
    """
    # Obtener todas las propiedades visibles
    propiedades = Property.objects.filter(is_visible=True)
    
    # Filtro por tipo de inmueble (si se proporciona en la URL)
    tipo_filtro = request.GET.get('tipo', None)
    if tipo_filtro:
        propiedades = propiedades.filter(tipo_inmueble=tipo_filtro)
    
    # Búsqueda por texto (nombre o ubicación)
    busqueda = request.GET.get('q', None)
    if busqueda:
        propiedades = propiedades.filter(
            Q(nombre__icontains=busqueda) | 
            Q(ubicacion__icontains=busqueda) |
            Q(descripcion__icontains=busqueda)
        )
    
    # Ordenar por fecha de creación (más recientes primero)
    propiedades = propiedades.order_by('-fecha_creacion')
    
    # Contar el total de propiedades encontradas
    total_propiedades = propiedades.count()
    
    # Obtener los tipos de inmueble disponibles para el filtro
    tipos_disponibles = Property.objects.filter(
        is_visible=True
    ).values_list('tipo_inmueble', flat=True).distinct()
    
    contexto = {
        'propiedades': propiedades,
        'total_propiedades': total_propiedades,
        'tipos_disponibles': tipos_disponibles,
        'tipo_actual': tipo_filtro,
        'busqueda_actual': busqueda,
        'titulo_pagina': 'Galería de Propiedades'
    }
    
    return render(request, 'property_list.html', contexto)


def property_detail_view(request, pk):
    """
    Vista de detalle de una propiedad específica.
    Muestra toda la información de la propiedad incluyendo:
    - Datos básicos (nombre, descripción, precio, ubicación, m²)
    - Imagen principal
    - Galería de imágenes adicionales
    - Botones para agendar cita (normal o prioritaria)
    
    Si la propiedad no existe o no está visible, muestra error 404.
    """
    # Obtener la propiedad o mostrar 404 si no existe o no es visible
    propiedad = get_object_or_404(
        Property, 
        pk=pk, 
        is_visible=True
    )
    
    # Obtener todas las imágenes adicionales de la propiedad
    # Ordenadas por el campo 'orden' que definimos en el modelo
    imagenes_adicionales = propiedad.imagenes.all().order_by('orden')
    
    # Contar cuántas imágenes adicionales hay
    total_imagenes = imagenes_adicionales.count()
    
    # Crear una lista con TODAS las imágenes (principal + adicionales)
    # Esto es útil para crear un carousel/slider en el template
    todas_las_imagenes = []
    
    # Agregar la imagen principal primero
    if propiedad.imagen_principal:
        todas_las_imagenes.append({
            'url': propiedad.imagen_principal.url,
            'es_principal': True
        })
    
    # Agregar las imágenes adicionales
    for imagen in imagenes_adicionales:
        todas_las_imagenes.append({
            'url': imagen.imagen.url,
            'es_principal': False
        })
    
    # Obtener propiedades similares (mismo tipo de inmueble)
    # Excluir la propiedad actual y limitar a 3
    propiedades_similares = Property.objects.filter(
        tipo_inmueble=propiedad.tipo_inmueble,
        is_visible=True
    ).exclude(pk=propiedad.pk)[:3]
    
    contexto = {
        'propiedad': propiedad,
        'imagenes_adicionales': imagenes_adicionales,
        'todas_las_imagenes': todas_las_imagenes,
        'total_imagenes': total_imagenes,
        'propiedades_similares': propiedades_similares,
        'titulo_pagina': propiedad.nombre
    }
    
    return render(request, 'property_detail.html', contexto)