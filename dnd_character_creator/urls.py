"""
URL configuration for dnd_character_creator project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

def home_redirect(request):
    """Redirect home to character list"""
    return redirect('character_list')

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # API routes
    path('api/', include('core.urls')),

    # Frontend routes
    path('characters/', include('characters.urls')),

    # Authentication
    path('auth/', include('users.urls')),

    # Home redirect
    path('', home_redirect, name='home'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
