from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('getRoutes/', views.get_routes, name='routes'),
    path('get-csrf-token/', views.get_csrf_token, name='csrf_token'),
    path('get-token/', views.get_token, name='get_token'),
    path('check-status/', views.check_processing_status, name='check_status'),
    #path('process-images/', views.process_images, name='process_images'),
    path('upload/', views.upload_images, name='upload_images'),
    path('getImages/', views.get_images, name='get_images'),
    path('<int:pk>/getImages/', views.get_image_by_id, name='get_image_by_id'),
    #path('check-status/', views.check_processing_status, name='check_status'),
    #path('process/', views.trigger_processing, name='trigger_processing'),
    path('verify-login/', views.verify_login, name='verify_login'),
    path('process-images/', views.process_images, name='process_images'),
    path('get-person-id/', views.get_person_id, name='get_person_id'),
    path('get-database-images/', views.get_database_images, name='get_database_images'),
    path('delete-person/', views.delete_person, name='delete_person'),
    path('check-server/', views.check_server, name='check_server'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



#path('process-images/', ProcessImageView.as_view(), name='process_images'),
