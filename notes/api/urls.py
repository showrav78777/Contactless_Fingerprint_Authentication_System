from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('upload/', views.upload_images, name='upload_images'),
    path('upload-full-hand/', views.upload_full_hand, name='upload_full_hand'),
    path('upload-finger/', views.upload_finger, name='upload_finger'),
    path('reset-person-counter/', views.reset_person_counter, name='reset_person_counter'),
    path('get-current-person-id/', views.get_current_person_id, name='get_current_person_id'),
    path('get-csrf-token/', views.get_csrf_token, name='get_csrf_token'),
    path('check-processing-status/', views.check_processing_status, name='check_processing_status'),
    path('get-images/', views.get_images, name='get_images'),
    path('get-image/<int:pk>/', views.get_image_by_id, name='get_image_by_id'),
    path('verify-login/', views.verify_login, name='verify_login'),
    path('process-images/', views.process_images, name='process_images'),
    path('get-database-images/', views.get_database_images, name='get_database_images'),
    path('delete-person/', views.delete_person, name='delete_person'),
    path('check-server/', views.check_server, name='check_server'),
    path('get-person-id/', views.get_person_id, name='get_person_id'),
    path('hand-tracking/', views.hand_tracking, name='hand_tracking'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



#path('process-images/', ProcessImageView.as_view(), name='process_images'),
