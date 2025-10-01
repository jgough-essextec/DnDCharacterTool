"""
URL configuration for dnd_character_creator project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect, render

def home_redirect(request):
    """Redirect home to character list"""
    return redirect('character_list')

def browse_content(request):
    """Browse D&D content - placeholder"""
    return render(request, 'pages/browse_content.html')

def tools_page(request):
    """D&D tools - placeholder"""
    return render(request, 'pages/tools.html')

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # API routes - temporarily disabled
    # path('api/', include('core.urls')),

    # Frontend routes
    path('characters/', include('characters.urls')),

    # Content browsing and tools
    path('browse/', browse_content, name='browse_content'),
    path('tools/', tools_page, name='tools'),

    # Authentication - temporarily disabled
    # path('auth/', include('users.urls')),

    # Home redirect
    path('', home_redirect, name='home'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
