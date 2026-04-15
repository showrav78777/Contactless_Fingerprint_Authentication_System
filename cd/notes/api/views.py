# from django.db import models
# from rest_framework.decorators import api_view
# from rest_framework.status import HTTP_200_OK
# from django.shortcuts import get_object_or_404
# from rest_framework.response import Response
# from django.http import JsonResponse
# #from django.views import View
# from rest_framework.parsers import MultiPartParser, FormParser
# from .serializers import NoteSerializer, ProcessedImageSerializer
# from .models import Note
# import os
# from .imageprocessing import process_image, split_fingers
# from .models import ProcessedImage
# from django.middleware.csrf import get_token
# from django.conf import settings
# from django.views.decorators.csrf import csrf_exempt


# # API Views
# @api_view(['GET'])
# def getRoutes(request):
#     routes = [
#         {
#             'Endpoint': '/uploadImage/',
#             'method': 'POST',
#             'body': {'finger_name': "", 'image': ""},
#             'description': 'Uploads a new set of images for the specified finger name.'
#         },
#         {
#             'Endpoint': '/getImages/',
#             'method': 'GET',
#             'body': None,
#             'description': 'Returns all images stored in the database.'
#         },
#             {'Endpoint': '/api/process-images/',
#              'method': 'POST', 
#               'body': {'images': []},
#               'description': 'Processes multiple images at once.'},

#     ]
#     return Response(routes)

# def get_csrf_token(request):
#     csrf_token = get_token(request)
#     return JsonResponse({'csrfToken': csrf_token})

# #This def process_image_view is for the imageprocessing.py(working) next ddef process_image_view should be for the modified code of imageprocessing.py
# # @api_view(['POST'])
# # def process_image_view(request):
# #     if 'image' not in request.FILES:
# #         return JsonResponse({'error': 'No image file provided'}, status=400)

# #     image_file = request.FILES['image']
# #     finger_name = request.POST.get('finger_name', 'unknown')
# #     image_path = os.path.join(settings.MEDIA_ROOT, 'uploads', image_file.name)

# #     # Save the uploaded image temporarily
# #     os.makedirs(os.path.dirname(image_path), exist_ok=True)
# #     with open(image_path, 'wb') as f:
# #         for chunk in image_file.chunks():
# #             f.write(chunk)

# #     try:
# #         # Process the image
# #         if 'thumb' in finger_name.lower():
# #             hand_side = 'left' if 'left' in finger_name.lower() else 'right'
# #             split_paths = split_fingers(image_path, save_dir=settings.MEDIA_ROOT, hand_side=hand_side, is_thumb_image=True)
# #         else:
# #             hand_side = 'left' if 'left' in finger_name.lower() else 'right'
# #             split_paths = split_fingers(image_path, save_dir=settings.MEDIA_ROOT, hand_side=hand_side)

# #         # Create a Note instance for the uploaded image
# #         # Create a Note instance for the uploaded image
# #         note = Note.objects.create(image=image_file, finger_name=finger_name)


# #         # Process each split image
# #         processed_images = []
# #         for split_path in split_paths:
# #             processed_image = process_image(split_path)
# #             if processed_image:
# #                 processed_path = os.path.join(settings.MEDIA_ROOT, 'processed', os.path.basename(split_path))
# #                 os.makedirs(os.path.dirname(processed_path), exist_ok=True)
# #                 processed_image.save(processed_path)

# #                 # Save metadata to the ProcessedImage table
# #                 processed_images.append(processed_path)
# #                 ProcessedImage.objects.create(
# #                     original_image=note,  # Now it should be a Note instance
# #                     processed_image=os.path.relpath(processed_path, settings.MEDIA_ROOT)
# #                 )

# #         return JsonResponse({'status': 'success', 'processed_images': processed_images})
# #     except Exception as e:
# #         return JsonResponse({'error': str(e)}, status=500)

# # ✅ **Updated: Handles multiple image processing at once**


# Django imports
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie, csrf_protect
from django.views.decorators.http import require_POST
from django.middleware.csrf import get_token
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from rest_framework.permissions import AllowAny

# Rest Framework imports
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

# Local imports
from .serializers import NoteSerializer, ProcessedImageSerializer
from .models import Note, ProcessedImage
from .imageprocessing import check_all_images_present, get_next_person_id, start_processing
from .loginprocessing import check_all_images_present as check_login_images
from .loginprocessing import start_processing as start_login_processing
from .test import verify_login as verify_login_test
from .loginprocessing import split_four_fingers, process_fingerprint_images, copy_thumb
from .imageprocessing import process_and_save_with_id
# Python standard library
import os
import json
import shutil

def get_routes(request):
    routes = [
        {
            'endpoint': '/api/upload/',
            'method': 'POST',
            'body': {'finger_name': "string", 'images': "file[]"},
            'description': 'Upload multiple finger images'
        },
        {
            'endpoint': '/api/images/',
            'method': 'GET',
            'description': 'Get all processed images'
        },
        {
            'endpoint': '/api/images/<id>/',
            'method': 'GET',
            'description': 'Get specific image by ID'
        },
        {
            'endpoint': '/api/process-images/',
            'method': 'POST',
            'body': {'images': "file[]", 'finger_name': "string"},
            'description': 'Process multiple images'
        }
    ]
    return Response(routes)

@ensure_csrf_cookie
def get_csrf_token(request):
    """
    This view sets and returns a CSRF token for the frontend
    """
    csrf_token = get_token(request)
    return JsonResponse({'csrfToken': csrf_token})

# @csrf_exempt
# @api_view(['POST'])
# def process_images(request):
#     if 'images' not in request.FILES:
#         return Response(
#             {'error': 'No images provided'}, 
#             status=status.HTTP_400_BAD_REQUEST
#         )

#     try:
#         image_files = request.FILES.getlist('images')
#         finger_name = request.POST.get('finger_name', 'unknown')
#         processed_images = []

#         for image_file in image_files:
#             # Save original image
#             note = Note.objects.create(
#                 image=image_file,
#                 finger_name=finger_name
#             )

#             # Create directory for temporary files
#             temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp')
#             os.makedirs(temp_dir, exist_ok=True)
#             temp_path = os.path.join(temp_dir, image_file.name)

#             # Save temporary file
#             with open(temp_path, 'wb+') as f:
#                 for chunk in image_file.chunks():
#                     f.write(chunk)

#             try:
#                 # Process image
#                 saved_paths = process_and_save_images(
#                     note_id=note.id,
#                     image_path=temp_path,
#                     image_type=finger_name
#                 )

#                 # Save processed images
#                 for path in saved_paths:
#                     relative_path = os.path.relpath(path, settings.MEDIA_ROOT)
#                     processed_images.append(relative_path)
#                     ProcessedImage.objects.create(
#                         original_image=note,
#                         processed_image=relative_path
#                     )

#             except Exception as e:
#                 print(f"Processing error: {str(e)}")  # For debugging
#                 return Response(
#                     {'error': f'Failed to process image: {str(e)}'}, 
#                     status=status.HTTP_500_INTERNAL_SERVER_ERROR
#                 )

#             finally:
#                 # Clean up temporary file
#                 if os.path.exists(temp_path):
#                     os.remove(temp_path)

#         return Response({
#             'status': 'success',
#             'message': 'Images processed successfully',
#             'processed_images': processed_images
#         })

#     except Exception as e:
#         print(f"Upload error: {str(e)}")  # For debugging
#         return Response(
#             {'error': f'Failed to handle upload: {str(e)}'}, 
#             status=status.HTTP_500_INTERNAL_SERVER_ERROR
#         )

# @csrf_exempt
# @api_view(['POST'])
# def upload_images(request):
#     """Handle image upload to the uploads directory"""
#     if 'images' not in request.FILES:
#         return Response({'error': 'No images provided'}, status=status.HTTP_400_BAD_REQUEST)

#     try:
#         image_file = request.FILES['images']
#         finger_name = request.POST.get('finger_name', '')

#         # Convert finger name to file naming format
#         file_name = finger_name.replace(' ', '_').lower() + '.jpg'
        
#         # Create uploads directory if it doesn't exist
#         upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')
#         os.makedirs(upload_dir, exist_ok=True)
        
#         # Create processed directory if it doesn't exist
#         processed_dir = os.path.join(settings.MEDIA_ROOT, 'processed')
#         os.makedirs(processed_dir, exist_ok=True)
        
#         # Full path for saving the uploaded file
#         file_path = os.path.join(upload_dir, file_name)
        
#         # Save the uploaded file, overwriting if it exists
#         with open(file_path, 'wb+') as destination:
#             for chunk in image_file.chunks():
#                 destination.write(chunk)

#         # Check if all required images are present in uploads directory
#         if check_all_images_present():
#             # Process all images and get the paths of processed images
#             processed_paths = process_all_images()
            
#             if processed_paths:
#                 return Response({
#                     'status': 'success',
#                     'message': 'All images processed successfully',
#                     'processed_paths': processed_paths
#                 })
#             else:
#                 return Response({
#                     'status': 'error',
#                     'message': 'Image processing failed'
#                 }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#         else:
#             return Response({
#                 'status': 'success',
#                 'message': f'Image saved as {file_name}, waiting for other images'
#             })

#     except Exception as e:
#         print(f"Error in upload_images: {str(e)}")
#         return Response(
#             {'error': f'Failed to upload image: {str(e)}'}, 
#             status=status.HTTP_500_INTERNAL_SERVER_ERROR
#         )

# @api_view(['GET'])
# def check_processing_status(request):
#     """Check if all images are present and ready for processing"""
#     try:
#         all_present = check_all_images_present()
#         return Response({
#             'status': 'ready' if all_present else 'waiting',
#             'message': 'All images present' if all_present else 'Waiting for all images'
#         })
#     except Exception as e:
#         return Response({
#             'status': 'error',
#             'message': str(e)
#         }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# @api_view(['POST'])
# def trigger_processing(request):
#     """Manually trigger processing of uploaded images"""
#     try:
#         if check_all_images_present():
#             processed_paths = process_all_images()
#             if processed_paths:
#                 return Response({
#                     'status': 'success',
#                     'message': 'Processing completed',
#                     'processed_paths': processed_paths
#                 })
#             else:
#                 return Response({
#                     'status': 'error',
#                     'message': 'Processing failed'
#                 }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#         else:
#             return Response({
#                 'status': 'error',
#                 'message': 'Not all required images are present'
#             }, status=status.HTTP_400_BAD_REQUEST)
#     except Exception as e:
#         return Response({
#             'status': 'error',
#             'message': str(e)
#         }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def upload_images(request):
    """Handle image uploads for both registration and login"""
    try:
        print("Received upload request")
        print(f"Request FILES: {request.FILES}")
        print(f"Request POST: {request.POST}")
        
        if 'images' in request.FILES:
            image = request.FILES['images']
            finger_name = request.POST.get('finger_name', '')
            is_login = request.POST.get('is_login', 'false').lower() == 'true'
            
            print(f"Processing image: {finger_name}, is_login: {is_login}")
            
            # Determine the directory and filename
            if is_login:
                directory = 'login_temp'
            else:
                directory = 'uploads'
            
            # Map finger names to filenames
            filename_map = {
                'left thumb': 'left_thumb.jpg',
                'right thumb': 'right_thumb.jpg',
                '4 left fingers': '4_left_fingers.jpg',
                '4 right fingers': '4_right_fingers.jpg'
            }
            
            if finger_name in filename_map:
                filename = filename_map[finger_name]
            else:
                filename = f"{finger_name.replace(' ', '_')}.jpg"
            
            # Create directory if it doesn't exist
            media_dir = os.path.join(settings.MEDIA_ROOT, directory)
            os.makedirs(media_dir, exist_ok=True)
            
            # Save the image
            image_path = os.path.join(media_dir, filename)
            with open(image_path, 'wb+') as destination:
                for chunk in image.chunks():
                    destination.write(chunk)
            
            print(f"Image saved to: {image_path}")
            
            # Check if all required images are present and trigger processing
            if not is_login:
                from .imageprocessing import check_all_images_present, start_processing
                if check_all_images_present():
                    print("All required images are present. Starting processing...")
                    result = start_processing()
                    if result:
                        print("Processing completed successfully")
                    else:
                        print("Processing failed")
            
            return JsonResponse({'status': 'success', 'message': f'{finger_name} uploaded successfully'})
        else:
            return JsonResponse({'status': 'error', 'message': 'No image found in request'}, status=400)
    except Exception as e:
        print(f"Error in upload_image: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

@api_view(['GET'])
def check_processing_status(request):
    """Check if all required images are present"""
    try:
        is_login = request.GET.get('is_login', 'false').lower() == 'true'
        
        if is_login:
            status_check = check_login_images()
            dir_name = 'login'
        else:
            status_check = check_all_images_present()
            dir_name = 'uploads'
            
        directory = os.path.join(settings.MEDIA_ROOT, dir_name)
        existing_images = os.listdir(directory) if os.path.exists(directory) else []
        
        return Response({
            'status': 'ready' if status_check else 'waiting',
            'existing_images': existing_images
        })
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_images(request):
    images = ProcessedImage.objects.all()
    serializer = ProcessedImageSerializer(images, many=True, context={'request': request})
    return Response(serializer.data)

@api_view(['GET'])
def get_image_by_id(request, pk):
    image = get_object_or_404(Note, pk=pk)
    serializer = NoteSerializer(image, context={'request': request})
    return Response(serializer.data)

from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
import os
import json
import importlib
import traceback

@csrf_exempt
@api_view(['POST'])
def verify_login(request):
    """Handle login verification"""
    try:
        print("Starting verification process...")

        # Parse person_id from request body
        if not request.body:
            return Response({
                'status': 'error',
                'message': 'No data provided in request body'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            data = json.loads(request.body)
            person_id = data.get('person_id')
            if not person_id:
                return Response({
                    'status': 'error',
                    'message': 'Person ID is required'
                }, status=status.HTTP_400_BAD_REQUEST)
        except json.JSONDecodeError:
            return Response({
                'status': 'error',
                'message': 'Invalid JSON format in request body'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Define directories
        login_dir = os.path.join(settings.MEDIA_ROOT, 'login')
        login_temp_dir = os.path.join(settings.MEDIA_ROOT, 'login_temp')
        processed_dir = os.path.join(settings.MEDIA_ROOT, 'processed')

        # Create directories if they don’t exist
        for directory in [login_dir, login_temp_dir, processed_dir]:
            if not os.path.exists(directory):
                print(f"Creating directory: {directory}")
                os.makedirs(directory, exist_ok=True)

        # List files in login_temp directory
        login_temp_files = os.listdir(login_temp_dir)
        print(f"Files in login_temp directory: {login_temp_files}")

        # Check if required files exist in login_temp directory
        required_files = ['left_thumb.jpg', 'right_thumb.jpg', '4_left_fingers.jpg', '4_right_fingers.jpg']
        missing_files = [file for file in required_files if file not in login_temp_files]

        if missing_files:
            return Response({
                'status': 'error',
                'message': f'Missing required files: {", ".join(missing_files)}'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Import and reload loginprocessing to avoid circular imports and ensure latest changes
        from . import loginprocessing
        importlib.reload(loginprocessing)

        # Process images using loginprocessing.py
        print("Starting image processing...")
        processing_result = loginprocessing.start_processing()

        if not processing_result:
            return Response({
                'status': 'error',
                'message': 'Failed to process fingerprint images. Check server logs for details.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        print("Image processing completed successfully")

        # Check if login directory has fingerprint images
        login_files = os.listdir(login_dir)
        print(f"Files in login directory: {login_files}")

        if not login_files:
            return Response({
                'status': 'error',
                'message': 'No processed fingerprint images found'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Verify login using test.py with the provided person_id
        print("Starting verification...")
        from .test import verify_login as verify_login_test
        # Pass the modified request with person_id to test.py
        result = verify_login_test(request)

        print(f"Verification result: {result}")

        # Ensure the response includes person_id even in error cases
        if 'person_id' not in result:
            result['person_id'] = person_id

        return Response(result, status=status.HTTP_200_OK if result['status'] != 'error' else status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        print(f"Error in verify_login view: {str(e)}")
        traceback.print_exc()
        return Response({
            'status': 'error',
            'message': f'Verification failed: {str(e)}',
            'person_id': data.get('person_id') if 'data' in locals() else None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def check_login_images_present(login_temp_dir):
    """Check if all 10 fingerprint images are present"""
    try:
        if not os.path.exists(login_temp_dir):
            return False
            
        files = os.listdir(login_temp_dir)
        required_count = 10  # We need all 10 fingerprints
        image_count = len([f for f in files if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))])
        
        return image_count == required_count
    except Exception as e:
        print(f"Error checking login images: {str(e)}")
        return False

@api_view(['POST'])
def process_images(request):
    """API endpoint to manually trigger image processing"""
    try:
        from .imageprocessing import check_all_images_present, start_processing
        
        if check_all_images_present():
            print("All required images are present. Starting manual processing...")
            result = start_processing()
            if result:
                return JsonResponse({'status': 'success', 'message': 'Processing completed successfully'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Processing failed'}, status=500)
        else:
            return JsonResponse({'status': 'error', 'message': 'Not all required images are present'}, status=400)
    except Exception as e:
        print(f"Error in process_images: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@csrf_exempt
def get_database_images(request):
    """API endpoint to retrieve processed fingerprint images"""
    if request.method == 'GET':
        try:
            database_dir = os.path.join(settings.MEDIA_ROOT, 'processed')
            
            if not os.path.exists(database_dir):
                return JsonResponse({
                    'error': 'Database directory not found'
                }, status=404)
            
            # Get all person directories
            person_dirs = [d for d in os.listdir(database_dir) 
                          if os.path.isdir(os.path.join(database_dir, d))]
            
            if not person_dirs:
                return JsonResponse({
                    'message': 'No registered users found'
                }, status=200)
            
            # Build response data
            response_data = {}
            
            for person_id in person_dirs:
                person_path = os.path.join(database_dir, person_id)
                fingerprints = {}
                
                # Get all fingerprint images for this person
                image_files = [f for f in os.listdir(person_path) 
                              if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
                
                for img_file in image_files:
                    # Extract finger name from filename (e.g., left_thumb.jpg -> left_thumb)
                    finger_name = os.path.splitext(img_file)[0]
                    
                    # Build the relative URL for the image
                    image_url = f'/media/processed/{person_id}/{img_file}'
                    
                    fingerprints[finger_name] = image_url
                
                response_data[person_id] = fingerprints
            
            return JsonResponse(response_data)
            
        except Exception as e:
            print(f"Error in get_database_images: {str(e)}")
            return JsonResponse({
                'error': str(e)
            }, status=500)
    
    return JsonResponse({
        'error': 'Only GET method is allowed'
    }, status=405)

@csrf_exempt  # Add this to bypass CSRF for now
@require_POST
def delete_person(request):
    try:
        data = json.loads(request.body)
        person_id = data.get('person_id')
        
        if not person_id:
            return JsonResponse({'error': 'Person ID is required'}, status=400)
        
        # Get the person directory path
        person_dir = os.path.join(settings.MEDIA_ROOT, 'processed', person_id)
        
        # Check if directory exists
        if not os.path.exists(person_dir):
            return JsonResponse({'error': f'Person ID {person_id} not found'}, status=404)
        
        # Delete the directory and all its contents
        try:
            shutil.rmtree(person_dir)
            print(f"Successfully deleted directory: {person_dir}")
            return JsonResponse({'success': True, 'message': f'Person ID {person_id} deleted successfully'})
        except PermissionError:
            # Handle permission errors
            print(f"Permission error when deleting {person_dir}")
            return JsonResponse({'error': 'Permission denied when deleting directory'}, status=403)
        except Exception as e:
            print(f"Error deleting directory {person_dir}: {str(e)}")
            return JsonResponse({'error': f'Error deleting directory: {str(e)}'}, status=500)
    
    except Exception as e:
        print(f"Error in delete_person: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def check_server(request):
    """
    Simple endpoint to check if the server is reachable
    """
    return JsonResponse({
        'status': 'ok',
        'message': 'Server is running',
        'server_ip': request.get_host(),
    })


def process_images(request):
    """Process uploaded images and return person_id"""
    if request.method == 'POST':
        saved_paths, person_id = process_and_save_with_id()
        if person_id is not None:
            return JsonResponse({'person_id': person_id, 'saved_paths': saved_paths})
        return JsonResponse({'error': 'Processing failed'}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=400)

def get_person_id(request):
    """Get the latest person_id"""
    try:
        latest_person_id = get_next_person_id() - 1  # Last used ID
        if latest_person_id < 1:
            return JsonResponse({'person_id': 0})  # No IDs assigned yet
        return JsonResponse({'person_id': latest_person_id})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)