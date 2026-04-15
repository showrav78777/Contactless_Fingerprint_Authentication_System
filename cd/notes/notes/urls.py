from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    #path('api/process-image/', process_image_view, name='process_image'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# path('image-processing/', include('image_processing.urls')),

# Add the media URL patterns to serve media files
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)