# import cv2
# import os
# import numpy as np
# from concurrent.futures import ThreadPoolExecutor, as_completed
# from functools import lru_cache
# from PIL import Image, ImageEnhance, ImageFilter, ImageOps
# from rembg import remove, new_session
# from django.conf import settings
# import time
# import glob
# import torch
# import torchvision.transforms.functional as TF
# from skimage.morphology import skeletonize, thin

# NUM_WORKERS = min(8, os.cpu_count() or 1)

# MAX_IMAGE_SIZE = 512 
# JPEG_QUALITY = 90    
# MIN_CONTOUR_SIZE = 50
# CROP_SIZE = 512 
# def apply_gabor_filters(image):
#     ksize = 1
#     sigma = 4.0
#     lamda = np.pi / 4
#     gamma = 0.5
#     orientations = [0, np.pi/4, np.pi/2, 3*np.pi/4]
#     filtered_images = []
    
#     for theta in orientations:
#         gabor_kernel = cv2.getGaborKernel((ksize, ksize), sigma, theta, lamda, gamma, ktype=cv2.CV_32F)
#         filtered_images.append(cv2.filter2D(image, cv2.CV_8UC3, gabor_kernel))
    
#     return np.mean(filtered_images, axis=0).astype(np.uint8)

# # Function to extract fingerprint ROI and remove outer border
# def extract_fingerprint_region(image):
#     # Convert to grayscale
#     gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
#     # Apply Otsu's thresholding
#     _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
#     # Find contours
#     contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
#     if contours:
#         # Find largest contour (finger)
#         largest_contour = max(contours, key=cv2.contourArea)
        
#         # Create mask
#         mask = np.zeros_like(gray)
#         cv2.drawContours(mask, [largest_contour], -1, 255, -1)
        
#         # Erode the mask to remove border
#         kernel_erode = np.ones((40, 40), np.uint8)
#         eroded_mask = cv2.erode(mask, kernel_erode, iterations=1)
        
#         # Get the coordinates of the fingerprint area
#         coords = cv2.findNonZero(eroded_mask)
#         x, y, w, h = cv2.boundingRect(coords)
        
#         # Apply the eroded mask to the original image
#         result = cv2.bitwise_and(image, image, mask=eroded_mask)
        
#         # Crop the image to remove empty borders
#         cropped = result[y:y+h, x:x+w]
        
#         return cropped
    
#     return image

# # Function to enhance image contrast and sharpness
# def enhance_image(image):
#     # Convert to grayscale
#     gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
#     # Apply CLAHE to enhance contrast
#     clahe = cv2.createCLAHE(clipLimit=5.0, tileGridSize=(8,8))
#     enhanced = clahe.apply(gray)
    
#     # Sharpen the image
#     kernel = np.array([[0, -1, 0],
#                        [-1, 5,-1],
#                        [0, -1, 0]])
#     sharpened = cv2.filter2D(enhanced, -1, kernel)
    
#     return sharpened

# def split_four_fingers(image_path, hand_side):
#     """Split four finger image into individual fingers with performance optimization"""
#     try:
#         # Load and resize image for faster processing
#         image = Image.open(image_path)
#         width, height = image.size
#         fingers = ['index', 'middle', 'ring', 'pinky']

#         widths = [int(height * 0.51), int(height * 0.45), int(height * 0.45), int(height * 0.48)]
#         positions = [30, int(height * 0.52), int(height * 0.93), int(height * 1.4)]        
#         # Create directory once
#         output_dir = os.path.join(settings.MEDIA_ROOT, 'all_ten_fingers')
#         os.makedirs(output_dir, exist_ok=True)
#         saved_paths = []
#         for i, finger in enumerate(fingers):
#             # Optimize cropping with boundary checking
#             left = positions[i]
#             right = min(left + widths[i], width)
            
#             if left >= width or right <= left:
#                 continue
                
#             # Crop and save in one operation
#             filename = f"{hand_side}_{finger}.jpg"
#             save_path = os.path.join(output_dir, filename)
#             image.crop((left, 0, right, height)).save(save_path, quality=95, optimize=True)
#             saved_paths.append(save_path)

#         return saved_paths
#     except Exception as e:
#         print(f"Error in split_four_fingers: {str(e)}")
#         return []
    
# # Create a persistent rembg session to reduce overhead
# rembg_session = new_session()
# def process_single_image(image_path, use_gpu=True):
#     """Optimized processing of a single fingerprint image with rotation, GPU-accelerated enhancement, and natural-dimension fingertip crop"""
#     try:
#         # Determine device (CUDA, MPS, or CPU) and log availability
#         if use_gpu:
#             cuda_available = torch.cuda.is_available()
#             mps_available = torch.backends.mps.is_available()
#             if cuda_available:
#                 device = torch.device("cuda")
#                 print(f"Using CUDA device: {torch.cuda.get_device_name(0)}")
#             elif mps_available:
#                 device = torch.device("mps")
#                 print("Using MPS device")
#             else:
#                 device = torch.device("cpu")
#                 print("Using CPU (no GPU detected)")
#         else:
#             device = torch.device("cpu")
#             print("Using CPU (forced)")
        
#         # Load image with reduced resolution
#         input_image = Image.open(image_path)
#         input_image.thumbnail((MAX_IMAGE_SIZE, MAX_IMAGE_SIZE), Image.Resampling.LANCZOS)
        
#         filename = os.path.basename(image_path)
#         filename_lower = filename.lower()
        
#         # Apply rotation for perfect fingertip alignment
#         if 'thumb' in filename:
#             input_image = input_image.rotate(-90, expand=True)
#         elif 'right_' in filename and not 'thumb' in filename:
#             input_image = input_image.rotate(180, expand=True)
#         elif 'left_' in filename and not 'thumb' in filename:
#             input_image = input_image.rotate(0, expand=True)

#         # Use faster background removal with persistent session
#         output_image = remove(input_image, alpha_matting=False, session=rembg_session)
#         if output_image.mode == 'RGBA':
#             white_bg = Image.new('RGB', output_image.size, (255, 255, 255))
#             white_bg.paste(output_image, mask=output_image.split()[3])
#             output_image_np = np.array(white_bg)
#         else:
#             output_image_np = np.array(output_image.convert('RGB'))
        
#         # Convert to grayscale for enhancement
#         gray_image = cv2.cvtColor(output_image_np, cv2.COLOR_RGB2GRAY)
        
#         # Enhance image with lightweight CLAHE 
#         clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
#         enhanced = clahe.apply(gray_image)
        
#         # Convert to PyTorch tensor for GPU processing
#         enhanced_tensor = torch.from_numpy(enhanced).float() / 255.0  # Normalize to [0, 1]
#         enhanced_tensor = enhanced_tensor.unsqueeze(0).unsqueeze(0).to(device)  # Shape: (1, 1, H, W)
        
#         # Apply minimal sharpening on GPU
#         kernel = torch.tensor([[-1, -1, -1],
#                                [-1, 10, -1], 
#                                [-1, -1, -1]], dtype=torch.float32, device=device)
#         kernel = kernel.view(1, 1, 3, 3)
#         enhanced_tensor = torch.nn.functional.conv2d(enhanced_tensor, kernel, padding=1)
#         enhanced_tensor = torch.clamp(enhanced_tensor, 0, 1)
        
#         # Fast adaptive thresholding on GPU with stricter constant
#         thresh_kernel = torch.ones(1, 1, 9, 9, device=device) / 81  # 9x9 window
#         local_mean = torch.nn.functional.conv2d(enhanced_tensor, thresh_kernel, padding=4)
#         binary_tensor = (enhanced_tensor < (local_mean - 1 / 255.0)).float()  # Stricter threshold
        
#         # Minimal morphological cleanup on GPU (closing: dilation + erosion)
#         morph_kernel = torch.ones(1, 1, 7, 7, device=device)  # Larger kernel for better contour
#         # Dilation
#         dilated = torch.nn.functional.max_pool2d(binary_tensor, kernel_size=7, stride=1, padding=3)
#         # Erosion
#         binary_tensor = -torch.nn.functional.max_pool2d(-dilated, kernel_size=7, stride=1, padding=3)
        
#         # Convert back to NumPy for contour detection
#         binary_np = (binary_tensor.squeeze(0).squeeze(0).cpu().numpy() * 255).astype(np.uint8)
        
#         # Find contours
#         contours, _ = cv2.findContours(binary_np, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
#         if contours:
#             # Use largest contour
#             largest_contour = max(contours, key=cv2.contourArea)
#             x, y, w, h = cv2.boundingRect(largest_contour)
#             print(f"Bounding box for {filename}: x={x}, y={y}, w={w}, h={h}")
            
#             # Early validation of finger region
#             if w < MIN_CONTOUR_SIZE or h < MIN_CONTOUR_SIZE:
#                 print(f"Invalid finger region in {image_path}: width={w}, height={h}")
#                 final_output_pil = Image.fromarray(output_image_np)
#             else:
#                 # Crop finger region
#                 finger_region = output_image_np[y:y+h, x:x+w]
                
#                 # Determine crop position (no fixed size)
#                 center_x = w // 2
                
#                 # Fingers requiring top crop
#                 upper_crop_fingers = ['left_thumb', 'right_thumb', 'right_index', 'right_middle', 'right_ring', 'right_pinky']
#                 is_upper_crop = any(finger in filename_lower for finger in upper_crop_fingers)
                
#                 if is_upper_crop:
#                     # Adjust crop for thumbs to focus on fingertip
#                     if 'thumb' in filename_lower:
#                         # Since copy_thumb already cropped the top 50%, take the top 60% of the remaining region
#                         crop_top = 0
#                         crop_bottom = int(h * 0.8)  # Take top 60% of the pre-cropped region
#                     else:
#                         # For non-thumb fingers, take the top 50% to capture more of the fingertip
#                         crop_top = 0
#                         crop_bottom = int(h * 0.6)  # Increased from 40% to 50%
#                 else:
#                     # Non-upper crop fingers: focus on tip
#                     crop_top = 0
#                     crop_bottom = int(h * 0.6)  # Increased from 40% to 50%
                
#                 # Horizontal crop (use full width for simplicity)
#                 crop_left = 0
#                 crop_right = w
                
#                 # Crop fingertip
#                 fingertip_crop = finger_region[crop_top:crop_bottom, crop_left:crop_right]
                
#                 # No resizing to fixed dimensions
#                 enhanced = enhance_image(fingertip_crop)
#                 binary = cv2.adaptiveThreshold(enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
#                                    cv2.THRESH_BINARY_INV, 11, 2)
#                 # Apply Gabor filters for ridge enhancement
#                 gabor_enhanced = apply_gabor_filters(enhanced)
    
#                 # Apply skeletonization and thinning
#                 skeleton = skeletonize(binary > 0)
#                 skeleton_img = (skeleton * 255).astype(np.uint8)
    
#                 thinned = thin(binary > 0)
#                 thinned_img = (thinned * 255).astype(np.uint8)
    
#                 # Minutiae detection using ORB
#                 orb = cv2.ORB_create(nfeatures=1000)
#                 keypoints = orb.detect(gabor_enhanced, None)
#                 minutiae_img = cv2.drawKeypoints(gabor_enhanced, keypoints, None, color=(0,0,255), flags=0)
    
#                 # Convert minutiae image to grayscale
#                 minutiae_img_gray = cv2.cvtColor(minutiae_img, cv2.COLOR_BGR2GRAY)
    
#                 # Combine minutiae image with thinned image
#                 x_output = cv2.addWeighted(minutiae_img_gray, 0.6, thinned_img, 0.4, 0)
                
#                 # Invert the image (White ridges, Black background)
#                 final_output = cv2.bitwise_not(x_output)
#                 final_output_pil = Image.fromarray(final_output)
#         else:
#             print(f"No finger region found in {image_path}, using processed image")
#             final_output_pil = Image.fromarray(output_image_np)
        
#         # Save to all_ten_fingers
#         output_dir = os.path.join(settings.MEDIA_ROOT, 'all_ten_fingers')
#         os.makedirs(output_dir, exist_ok=True)
#         save_path = os.path.join(output_dir, filename)
#         final_output_pil.save(save_path, quality=JPEG_QUALITY, optimize=True)
        
#         return final_output_pil
#     except Exception as e:
#         print(f"Error processing image {image_path}: {str(e)}")
#         return None
    
# # def process_single_image(image_path):
# #  """Process a single fingerprint image with caching and optimizations"""
# #  try:
# #         # Load and resize image for faster processing
# #         input_image = Image.open(image_path)
        
# #         # Resize large images for faster processing
# #         if max(input_image.size) > MAX_IMAGE_SIZE:
# #             input_image.thumbnail((MAX_IMAGE_SIZE, MAX_IMAGE_SIZE), Image.Resampling.LANCZOS)
            
# #         filename = os.path.basename(image_path)
        
# #         # Use faster background removal with lower resolution
# #         output_image = remove(input_image, alpha_matting=False)
        
# #         # Convert RGBA to RGB with white background in one step
# #         if output_image.mode == 'RGBA':
# #             white_bg = Image.new('RGB', output_image.size, (255, 255, 255))
# #             white_bg.paste(output_image, mask=output_image.split()[3])
# #             output_image = white_bg
        
# #         #     x, y, w, h = cv2.boundingRect(contour)
# #         #  #         # Get fingertip region
# #         #     tip_start_y = y
# #         #     tip_height = int(h * 0.75)  # Take top 50% of finger
# #         #     fingertip = gray_image[tip_start_y:tip_start_y+tip_height, x:x+w]
        
# #         # Process images
        
# #     #         output_image_np = np.array(output_image)
# #     #         image = extract_fingerprint_region(output_image_np)
    
# #     # # Enhance the image
# #     #         enhanced = enhance_image(image)
    
# #     # # Apply adaptive thresholding for segmentation
# #     #         binary = cv2.adaptiveThreshold(enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
# #     #                                cv2.THRESH_BINARY_INV, 11, 2)
    
# #     # # Apply Gabor filters for ridge enhancement
# #     #         gabor_enhanced = apply_gabor_filters(enhanced)
    
# #     # # Apply skeletonization and thinning
# #     #         skeleton = skeletonize(binary > 0)
# #     #         skeleton_img = (skeleton * 255).astype(np.uint8)
    
# #     #         thinned = thin(binary > 0)
# #     #         thinned_img = (thinned * 255).astype(np.uint8)
    
# #     # # Minutiae detection using ORB
# #     #         orb = cv2.ORB_create(nfeatures=1000)
# #     #         keypoints = orb.detect(gabor_enhanced, None)
# #     #         minutiae_img = cv2.drawKeypoints(gabor_enhanced, keypoints, None, color=(0,0,255), flags=0)
    
# #     # # Convert minutiae image to grayscale
# #     #         minutiae_img_gray = cv2.cvtColor(minutiae_img, cv2.COLOR_BGR2GRAY)
         
# #     # # Combine minutiae image with thinned image
# #     #         x_output = cv2.addWeighted(minutiae_img_gray, 0.6, thinned_img, 0.4, 0)
    
# #     # # Invert the image (White ridges, Black background)
# #     #         final_output = cv2.bitwise_not(x_output)
# #     #         final_output_pil = Image.fromarray(final_output)
# #             final_output_pil=output_image
# # # Optimize rotation logic
# #         if 'thumb' in filename:
# #             final_output_pil = final_output_pil.rotate(-90, expand=True)
# #         elif 'right_' in filename and not 'thumb' in filename:
# #             final_output_pil = final_output_pil.rotate(180, expand=True)
# #         elif 'left_' in filename and not 'thumb' in filename:
# #             final_output_pil = final_output_pil.rotate(0, expand=True)
            
# #         return final_output_pil
# #  except Exception as e:
# #         print(f"Error processing image {image_path}: {str(e)}")
# #         return None

# def process_fingerprint_images():
#     """Process fingerprint images with optimized parallel execution"""
#     start_time = time.time()
#     try:
#         output_dir = os.path.join(settings.MEDIA_ROOT, 'all_ten_fingers')
#         if not os.path.exists(output_dir):
#             return False
            
#         image_files = [f for f in os.listdir(output_dir) if f.endswith(('.jpg', '.jpeg', '.png'))]
        
#         # Use parallel processing with optimized thread count
#         with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
#             # Submit all processing tasks
#             futures = {}
#             for filename in image_files:
#                 image_path = os.path.join(output_dir, filename)
#                 futures[executor.submit(process_single_image, image_path)] = image_path
            
#             # Process as they complete to maximize throughput
#             for future in as_completed(futures):
#                 image_path = futures[future]
#                 try:
#                     processed_image = future.result()
#                     if processed_image:
#                         processed_image.save(image_path, quality=JPEG_QUALITY, optimize=True)
#                 except Exception as e:
#                     print(f"Error processing {image_path}: {e}")

#         print(f"Processed {len(image_files)} images in {time.time() - start_time:.2f} seconds")
#         return True
#     except Exception as e:
#         print(f"Error in process_fingerprint_images: {str(e)}")
#         return False

# def copy_thumb(thumb_path, hand_side):
#     """Copy and preprocess thumb image to focus on the fingertip region"""
#     try:
#         output_dir = os.path.join(settings.MEDIA_ROOT, 'all_ten_fingers')
#         os.makedirs(output_dir, exist_ok=True)
        
#         # Load and resize image to a manageable size
#         image = Image.open(thumb_path)
#         image.thumbnail((MAX_IMAGE_SIZE, MAX_IMAGE_SIZE), Image.Resampling.LANCZOS)
        
#         # Get image dimensions
#         width, height = image.size
        
#         # Focus on the fingertip region (top 70% of the thumb height to ensure full fingertip coverage)
#         fingertip_ratio = 0.8  # Take the top 70% of the height
#         crop_top = 0
#         crop_bottom = int(height * fingertip_ratio)  # Crop to the top 70%
        
#         # Center the crop horizontally
#         crop_width = int(width * 0.8)  # Take 80% of the width to avoid edges
#         crop_left = (width - crop_width) // 2
#         crop_right = crop_left + crop_width
        
#         # Ensure boundaries are valid
#         if crop_right > width:
#             crop_left = max(0, width - crop_width)
#             crop_right = width
        
#         # Crop the fingertip region
#         image = image.crop((crop_left, crop_top, crop_right, crop_bottom))
        
#         # Save thumb image
#         save_path = os.path.join(output_dir, f"{hand_side}_thumb.jpg")
#         image.save(save_path, quality=95, optimize=True)
        
#         return save_path
#     except Exception as e:
#         print(f"Error in copy_thumb: {str(e)}")
#         return None
    
# def get_next_person_id():
#     """Get the next available person ID from processed directory"""
#     try:
#         processed_dir = os.path.join(settings.MEDIA_ROOT, 'processed')
#         if not os.path.exists(processed_dir):
#             return 1
        
#         # Get existing person IDs efficiently
#         existing_ids = [int(d) for d in os.listdir(processed_dir) if d.isdigit()]
#         return max(existing_ids, default=0) + 1
#     except Exception as e:
#         print(f"Error in get_next_person_id: {str(e)}")
#         return 1

# def process_and_save_with_id():
#     """Process images from all_ten_fingers and save with person ID"""
#     try:
#         # Get next person ID
#         person_id = get_next_person_id()
        
#         # Setup directories
#         all_ten_dir = os.path.join(settings.MEDIA_ROOT, 'all_ten_fingers')
#         processed_dir = os.path.join(settings.MEDIA_ROOT, 'processed')
#         person_dir = os.path.join(processed_dir, str(person_id))
        
#         # Check directories
#         if not os.path.exists(all_ten_dir):
#             return []
            
#         image_files = [f for f in os.listdir(all_ten_dir) if f.endswith(('.jpg', '.jpeg', '.png'))]
#         if not image_files:
#             return []
            
#         # Create directories
#         os.makedirs(processed_dir, exist_ok=True)
#         os.makedirs(person_dir, exist_ok=True)
        
#         saved_paths = []
        
#         # Batch process images for better performance
#         batch_size = min(50, len(image_files))
        
#         # Process in batches with parallel execution
#         for i in range(0, len(image_files), batch_size):
#             batch = image_files[i:i+batch_size]
            
#             with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
#                 futures = []
#                 for filename in batch:
#                     new_filename = f"{person_id}_{filename}"
#                     source_path = os.path.join(all_ten_dir, filename)
#                     dest_path = os.path.join(person_dir, new_filename)
                    
#                     # Process and save in single function for better performance
#                     futures.append((dest_path, executor.submit(
#                         lambda src, dst: Image.open(src).save(dst, quality=JPEG_QUALITY, optimize=True),
#                         source_path, dest_path
#                     )))
                
#                 # Collect results from this batch
#                 for dest_path, future in futures:
#                     try:
#                         future.result()
#                         saved_paths.append(dest_path)
#                     except Exception as e:
#                         print(f"Error saving to {dest_path}: {str(e)}")
        
#         return saved_paths, person_id
#     except Exception as e:
#         print(f"Error in process_and_save_with_id: {str(e)}")
#         return []

# def check_all_images_present():
#     """Check if all required images exist in uploads directory"""
#     try:
#         uploads_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')
#         if not os.path.exists(uploads_dir):
#             return False
            
#         # Use set operations for faster checking
#         required_images = {
#             'left_thumb.jpg',
#             '4_left_fingers.jpg',
#             'right_thumb.jpg',
#             '4_right_fingers.jpg'
#         }
        
#         existing_files = set(os.listdir(uploads_dir))
#         return required_images.issubset(existing_files)
#     except Exception as e:
#         print(f"Error checking images: {str(e)}")
#         return False

# def start_processing():
#     """Main entry point for processing pipeline with performance tracking"""
#     start_time = time.time()
#     try:
#         # Get paths
#         uploads_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')
        
#         if not os.path.exists(uploads_dir):
#             return False
            
#         # Check required files
#         if not check_all_images_present():
#             return False
            
#         # Define paths
#         left_thumb_path = os.path.join(uploads_dir, 'left_thumb.jpg')
#         right_thumb_path = os.path.join(uploads_dir, 'right_thumb.jpg')
#         left_fingers_path = os.path.join(uploads_dir, '4_left_fingers.jpg')
#         right_fingers_path = os.path.join(uploads_dir, '4_right_fingers.jpg')

#         # Create and clear all_ten_fingers directory
#         all_ten_dir = os.path.join(settings.MEDIA_ROOT, 'all_ten_fingers')
#         os.makedirs(all_ten_dir, exist_ok=True)
        
#         # Clear directory efficiently
#         for file in os.listdir(all_ten_dir):
#             file_path = os.path.join(all_ten_dir, file)
#             if os.path.isfile(file_path):
#                 os.remove(file_path)

#         # Process images in parallel
#         with ThreadPoolExecutor(max_workers=4) as executor:
#             # Start all tasks concurrently
#             left_split_future = executor.submit(split_four_fingers, left_fingers_path, 'left')
#             right_split_future = executor.submit(split_four_fingers, right_fingers_path, 'right')
#             left_thumb_future = executor.submit(copy_thumb, left_thumb_path, 'left')
#             right_thumb_future = executor.submit(copy_thumb, right_thumb_path, 'right')
            
#             # Get results
#             left_split_paths = left_split_future.result()
#             right_split_paths = right_split_future.result()
#             left_thumb_path = left_thumb_future.result()
#             right_thumb_path = right_thumb_future.result()
        
#         # Verify and continue
#         if not (left_split_paths and right_split_paths and left_thumb_path and right_thumb_path):
#             # Try to continue with partial results
#             if len(os.listdir(all_ten_dir)) < 5:  # Need at least half the fingers
#                 return False

#         # Process all fingerprint images
#         process_result = process_fingerprint_images()
#         if not process_result:
#             return False
            
#         # Save with person ID
#         final_paths = process_and_save_with_id()
        
#         if not final_paths:
#             return False
            
#         # Clean up uploads directory
#         for file in os.listdir(uploads_dir):
#             if file.endswith('.jpg'):
#                 os.remove(os.path.join(uploads_dir, file))
        
#         processing_time = time.time() - start_time
#         print(f"Total processing completed in {processing_time:.2f} seconds")
        
#         return final_paths

#     except Exception as e:
#         print(f"Error in start_processing: {str(e)}")
#         return False

import cv2
import os
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
from rembg import remove, new_session
from django.conf import settings
import time
import glob
import torch
import torchvision.transforms.functional as TF

NUM_WORKERS = min(8, os.cpu_count() or 1)

MAX_IMAGE_SIZE = 512 
JPEG_QUALITY = 90    
MIN_CONTOUR_SIZE = 50
CROP_SIZE = 512 


def split_four_fingers(image_path, hand_side):
    """Split four finger image into individual fingers with performance optimization"""
    try:
        # Load and resize image for faster processing
        image = Image.open(image_path)
        width, height = image.size
        fingers = ['index', 'middle', 'ring', 'pinky']

        widths = [int(height * 0.51), int(height * 0.45), int(height * 0.45), int(height * 0.48)]
        positions = [30, int(height * 0.52), int(height * 0.93), int(height * 1.4)]        
        # Create directory once
        output_dir = os.path.join(settings.MEDIA_ROOT, 'all_ten_fingers')
        os.makedirs(output_dir, exist_ok=True)
        saved_paths = []
        for i, finger in enumerate(fingers):
            # Optimize cropping with boundary checking
            left = positions[i]
            right = min(left + widths[i], width)
            
            if left >= width or right <= left:
                continue
                
            # Crop and save in one operation
            filename = f"{hand_side}_{finger}.jpg"
            save_path = os.path.join(output_dir, filename)
            image.crop((left, 0, right, height)).save(save_path, quality=95, optimize=True)
            saved_paths.append(save_path)

        return saved_paths
    except Exception as e:
        print(f"Error in split_four_fingers: {str(e)}")
        return []
    
# Create a persistent rembg session to reduce overhead
rembg_session = new_session()
def process_single_image(image_path, use_gpu=True):
    """Optimized processing of a single fingerprint image with rotation, GPU-accelerated enhancement, and natural-dimension fingertip crop"""
    try:
        # Determine device (CUDA, MPS, or CPU) and log availability
        if use_gpu:
            cuda_available = torch.cuda.is_available()
            mps_available = torch.backends.mps.is_available()
            if cuda_available:
                device = torch.device("cuda")
                print(f"Using CUDA device: {torch.cuda.get_device_name(0)}")
            elif mps_available:
                device = torch.device("mps")
                print("Using MPS device")
            else:
                device = torch.device("cpu")
                print("Using CPU (no GPU detected)")
        else:
            device = torch.device("cpu")
            print("Using CPU (forced)")
        
        # Load image with reduced resolution
        input_image = Image.open(image_path)
        input_image.thumbnail((MAX_IMAGE_SIZE, MAX_IMAGE_SIZE), Image.Resampling.LANCZOS)
        
        filename = os.path.basename(image_path)
        filename_lower = filename.lower()
        
        # Apply rotation for perfect fingertip alignment
        if 'thumb' in filename:
            input_image = input_image.rotate(-90, expand=True)
        elif 'right_' in filename and not 'thumb' in filename:
            input_image = input_image.rotate(180, expand=True)
        elif 'left_' in filename and not 'thumb' in filename:
            input_image = input_image.rotate(0, expand=True)

        # Use faster background removal with persistent session
        output_image = remove(input_image, alpha_matting=False, session=rembg_session)
        if output_image.mode == 'RGBA':
            white_bg = Image.new('RGB', output_image.size, (255, 255, 255))
            white_bg.paste(output_image, mask=output_image.split()[3])
            output_image_np = np.array(white_bg)
        else:
            output_image_np = np.array(output_image.convert('RGB'))
        
        # Convert to grayscale for enhancement
        gray_image = cv2.cvtColor(output_image_np, cv2.COLOR_RGB2GRAY)
        
        # Enhance image with lightweight CLAHE 
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray_image)
        
        # Convert to PyTorch tensor for GPU processing
        enhanced_tensor = torch.from_numpy(enhanced).float() / 255.0  # Normalize to [0, 1]
        enhanced_tensor = enhanced_tensor.unsqueeze(0).unsqueeze(0).to(device)  # Shape: (1, 1, H, W)
        
        # Apply minimal sharpening on GPU
        kernel = torch.tensor([[-1, -1, -1],
                               [-1, 10, -1], 
                               [-1, -1, -1]], dtype=torch.float32, device=device)
        kernel = kernel.view(1, 1, 3, 3)
        enhanced_tensor = torch.nn.functional.conv2d(enhanced_tensor, kernel, padding=1)
        enhanced_tensor = torch.clamp(enhanced_tensor, 0, 1)
        
        # Fast adaptive thresholding on GPU with stricter constant
        thresh_kernel = torch.ones(1, 1, 9, 9, device=device) / 81  # 9x9 window
        local_mean = torch.nn.functional.conv2d(enhanced_tensor, thresh_kernel, padding=4)
        binary_tensor = (enhanced_tensor < (local_mean - 1 / 255.0)).float()  # Stricter threshold
        
        # Minimal morphological cleanup on GPU (closing: dilation + erosion)
        morph_kernel = torch.ones(1, 1, 7, 7, device=device)  # Larger kernel for better contour
        # Dilation
        dilated = torch.nn.functional.max_pool2d(binary_tensor, kernel_size=7, stride=1, padding=3)
        # Erosion
        binary_tensor = -torch.nn.functional.max_pool2d(-dilated, kernel_size=7, stride=1, padding=3)
        
        # Convert back to NumPy for contour detection
        binary_np = (binary_tensor.squeeze(0).squeeze(0).cpu().numpy() * 255).astype(np.uint8)
        
        # Find contours
        contours, _ = cv2.findContours(binary_np, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            # Use largest contour
            largest_contour = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(largest_contour)
            print(f"Bounding box for {filename}: x={x}, y={y}, w={w}, h={h}")
            
            # Early validation of finger region
            if w < MIN_CONTOUR_SIZE or h < MIN_CONTOUR_SIZE:
                print(f"Invalid finger region in {image_path}: width={w}, height={h}")
                final_output_pil = Image.fromarray(output_image_np)
            else:
                # Crop finger region
                finger_region = output_image_np[y:y+h, x:x+w]
                
                # Determine crop position (no fixed size)
                center_x = w // 2
                
                # Fingers requiring top crop
                upper_crop_fingers = ['left_thumb', 'right_thumb', 'right_index', 'right_middle', 'right_ring', 'right_pinky']
                is_upper_crop = any(finger in filename_lower for finger in upper_crop_fingers)
                
                if is_upper_crop:
                    # Adjust crop for thumbs to focus on fingertip
                    if 'thumb' in filename_lower:
                        # Since copy_thumb already cropped the top 50%, take the top 60% of the remaining region
                        crop_top = 0
                        crop_bottom = int(h * 0.8)  # Take top 60% of the pre-cropped region
                    else:
                        # For non-thumb fingers, take the top 50% to capture more of the fingertip
                        crop_top = 0
                        crop_bottom = int(h * 0.6)  # Increased from 40% to 50%
                else:
                    # Non-upper crop fingers: focus on tip
                    crop_top = 0
                    crop_bottom = int(h * 0.6)  # Increased from 40% to 50%
                
                # Horizontal crop (use full width for simplicity)
                crop_left = 0
                crop_right = w
                
                # Crop fingertip
                fingertip_crop = finger_region[crop_top:crop_bottom, crop_left:crop_right]
                
                # No resizing to fixed dimensions
                final_output_pil = Image.fromarray(fingertip_crop)
        else:
            print(f"No finger region found in {image_path}, using processed image")
            final_output_pil = Image.fromarray(output_image_np)
        
        # Save to all_ten_fingers
        output_dir = os.path.join(settings.MEDIA_ROOT, 'all_ten_fingers')
        os.makedirs(output_dir, exist_ok=True)
        save_path = os.path.join(output_dir, filename)
        final_output_pil.save(save_path, quality=JPEG_QUALITY, optimize=True)
        
        return final_output_pil
    except Exception as e:
        print(f"Error processing image {image_path}: {str(e)}")
        return None
    
# def process_single_image(image_path):
#  """Process a single fingerprint image with caching and optimizations"""
#  try:
#         # Load and resize image for faster processing
#         input_image = Image.open(image_path)
        
#         # Resize large images for faster processing
#         if max(input_image.size) > MAX_IMAGE_SIZE:
#             input_image.thumbnail((MAX_IMAGE_SIZE, MAX_IMAGE_SIZE), Image.Resampling.LANCZOS)
            
#         filename = os.path.basename(image_path)
        
#         # Use faster background removal with lower resolution
#         output_image = remove(input_image, alpha_matting=False)
        
#         # Convert RGBA to RGB with white background in one step
#         if output_image.mode == 'RGBA':
#             white_bg = Image.new('RGB', output_image.size, (255, 255, 255))
#             white_bg.paste(output_image, mask=output_image.split()[3])
#             output_image = white_bg
        
#         #     x, y, w, h = cv2.boundingRect(contour)
#         #  #         # Get fingertip region
#         #     tip_start_y = y
#         #     tip_height = int(h * 0.75)  # Take top 50% of finger
#         #     fingertip = gray_image[tip_start_y:tip_start_y+tip_height, x:x+w]
        
#         # Process images
        
#     #         output_image_np = np.array(output_image)
#     #         image = extract_fingerprint_region(output_image_np)
    
#     # # Enhance the image
#     #         enhanced = enhance_image(image)
    
#     # # Apply adaptive thresholding for segmentation
#     #         binary = cv2.adaptiveThreshold(enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
#     #                                cv2.THRESH_BINARY_INV, 11, 2)
    
#     # # Apply Gabor filters for ridge enhancement
#     #         gabor_enhanced = apply_gabor_filters(enhanced)
    
#     # # Apply skeletonization and thinning
#     #         skeleton = skeletonize(binary > 0)
#     #         skeleton_img = (skeleton * 255).astype(np.uint8)
    
#     #         thinned = thin(binary > 0)
#     #         thinned_img = (thinned * 255).astype(np.uint8)
    
#     # # Minutiae detection using ORB
#     #         orb = cv2.ORB_create(nfeatures=1000)
#     #         keypoints = orb.detect(gabor_enhanced, None)
#     #         minutiae_img = cv2.drawKeypoints(gabor_enhanced, keypoints, None, color=(0,0,255), flags=0)
    
#     # # Convert minutiae image to grayscale
#     #         minutiae_img_gray = cv2.cvtColor(minutiae_img, cv2.COLOR_BGR2GRAY)
         
#     # # Combine minutiae image with thinned image
#     #         x_output = cv2.addWeighted(minutiae_img_gray, 0.6, thinned_img, 0.4, 0)
    
#     # # Invert the image (White ridges, Black background)
#     #         final_output = cv2.bitwise_not(x_output)
#     #         final_output_pil = Image.fromarray(final_output)
#             final_output_pil=output_image
# # Optimize rotation logic
#         if 'thumb' in filename:
#             final_output_pil = final_output_pil.rotate(-90, expand=True)
#         elif 'right_' in filename and not 'thumb' in filename:
#             final_output_pil = final_output_pil.rotate(180, expand=True)
#         elif 'left_' in filename and not 'thumb' in filename:
#             final_output_pil = final_output_pil.rotate(0, expand=True)
            
#         return final_output_pil
#  except Exception as e:
#         print(f"Error processing image {image_path}: {str(e)}")
#         return None

def process_fingerprint_images():
    """Process fingerprint images with optimized parallel execution"""
    start_time = time.time()
    try:
        output_dir = os.path.join(settings.MEDIA_ROOT, 'all_ten_fingers')
        if not os.path.exists(output_dir):
            return False
            
        image_files = [f for f in os.listdir(output_dir) if f.endswith(('.jpg', '.jpeg', '.png'))]
        
        # Use parallel processing with optimized thread count
        with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
            # Submit all processing tasks
            futures = {}
            for filename in image_files:
                image_path = os.path.join(output_dir, filename)
                futures[executor.submit(process_single_image, image_path)] = image_path
            
            # Process as they complete to maximize throughput
            for future in as_completed(futures):
                image_path = futures[future]
                try:
                    processed_image = future.result()
                    if processed_image:
                        processed_image.save(image_path, quality=JPEG_QUALITY, optimize=True)
                except Exception as e:
                    print(f"Error processing {image_path}: {e}")

        print(f"Processed {len(image_files)} images in {time.time() - start_time:.2f} seconds")
        return True
    except Exception as e:
        print(f"Error in process_fingerprint_images: {str(e)}")
        return False

def copy_thumb(thumb_path, hand_side):
    """Copy and preprocess thumb image to focus on the fingertip region"""
    try:
        output_dir = os.path.join(settings.MEDIA_ROOT, 'all_ten_fingers')
        os.makedirs(output_dir, exist_ok=True)
        
        # Load and resize image to a manageable size
        image = Image.open(thumb_path)
        image.thumbnail((MAX_IMAGE_SIZE, MAX_IMAGE_SIZE), Image.Resampling.LANCZOS)
        
        # Get image dimensions
        width, height = image.size
        
        # Focus on the fingertip region (top 70% of the thumb height to ensure full fingertip coverage)
        fingertip_ratio = 0.8  # Take the top 70% of the height
        crop_top = 0
        crop_bottom = int(height * fingertip_ratio)  # Crop to the top 70%
        
        # Center the crop horizontally
        crop_width = int(width * 0.8)  # Take 80% of the width to avoid edges
        crop_left = (width - crop_width) // 2
        crop_right = crop_left + crop_width
        
        # Ensure boundaries are valid
        if crop_right > width:
            crop_left = max(0, width - crop_width)
            crop_right = width
        
        # Crop the fingertip region
        image = image.crop((crop_left, crop_top, crop_right, crop_bottom))
        
        # Save thumb image
        save_path = os.path.join(output_dir, f"{hand_side}_thumb.jpg")
        image.save(save_path, quality=95, optimize=True)
        
        return save_path
    except Exception as e:
        print(f"Error in copy_thumb: {str(e)}")
        return None
    
def get_next_person_id():
    """Get the next available person ID from processed directory"""
    try:
        processed_dir = os.path.join(settings.MEDIA_ROOT, 'processed')
        if not os.path.exists(processed_dir):
            return 1
        
        # Get existing person IDs efficiently
        existing_ids = [int(d) for d in os.listdir(processed_dir) if d.isdigit()]
        return max(existing_ids, default=0) + 1
    except Exception as e:
        print(f"Error in get_next_person_id: {str(e)}")
        return 1

def process_and_save_with_id():
    """Process images from all_ten_fingers and save with person ID"""
    try:
        # Get next person ID
        person_id = get_next_person_id()
        
        # Setup directories
        all_ten_dir = os.path.join(settings.MEDIA_ROOT, 'all_ten_fingers')
        processed_dir = os.path.join(settings.MEDIA_ROOT, 'processed')
        person_dir = os.path.join(processed_dir, str(person_id))
        
        # Check directories
        if not os.path.exists(all_ten_dir):
            return []
            
        image_files = [f for f in os.listdir(all_ten_dir) if f.endswith(('.jpg', '.jpeg', '.png'))]
        if not image_files:
            return []
            
        # Create directories
        os.makedirs(processed_dir, exist_ok=True)
        os.makedirs(person_dir, exist_ok=True)
        
        saved_paths = []
        
        # Batch process images for better performance
        batch_size = min(50, len(image_files))
        
        # Process in batches with parallel execution
        for i in range(0, len(image_files), batch_size):
            batch = image_files[i:i+batch_size]
            
            with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
                futures = []
                for filename in batch:
                    new_filename = f"{person_id}_{filename}"
                    source_path = os.path.join(all_ten_dir, filename)
                    dest_path = os.path.join(person_dir, new_filename)
                    
                    # Process and save in single function for better performance
                    futures.append((dest_path, executor.submit(
                        lambda src, dst: Image.open(src).save(dst, quality=JPEG_QUALITY, optimize=True),
                        source_path, dest_path
                    )))
                
                # Collect results from this batch
                for dest_path, future in futures:
                    try:
                        future.result()
                        saved_paths.append(dest_path)
                    except Exception as e:
                        print(f"Error saving to {dest_path}: {str(e)}")
        
        return saved_paths, person_id
    except Exception as e:
        print(f"Error in process_and_save_with_id: {str(e)}")
        return []

def check_all_images_present():
    """Check if all required images exist in uploads directory"""
    try:
        uploads_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')
        if not os.path.exists(uploads_dir):
            return False
            
        # Use set operations for faster checking
        required_images = {
            'left_thumb.jpg',
            '4_left_fingers.jpg',
            'right_thumb.jpg',
            '4_right_fingers.jpg'
        }
        
        existing_files = set(os.listdir(uploads_dir))
        return required_images.issubset(existing_files)
    except Exception as e:
        print(f"Error checking images: {str(e)}")
        return False

def start_processing():
    """Main entry point for processing pipeline with performance tracking"""
    start_time = time.time()
    try:
        # Get paths
        uploads_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')
        
        if not os.path.exists(uploads_dir):
            return False
            
        # Check required files
        if not check_all_images_present():
            return False
            
        # Define paths
        left_thumb_path = os.path.join(uploads_dir, 'left_thumb.jpg')
        right_thumb_path = os.path.join(uploads_dir, 'right_thumb.jpg')
        left_fingers_path = os.path.join(uploads_dir, '4_left_fingers.jpg')
        right_fingers_path = os.path.join(uploads_dir, '4_right_fingers.jpg')

        # Create and clear all_ten_fingers directory
        all_ten_dir = os.path.join(settings.MEDIA_ROOT, 'all_ten_fingers')
        os.makedirs(all_ten_dir, exist_ok=True)
        
        # Clear directory efficiently
        for file in os.listdir(all_ten_dir):
            file_path = os.path.join(all_ten_dir, file)
            if os.path.isfile(file_path):
                os.remove(file_path)

        # Process images in parallel
        with ThreadPoolExecutor(max_workers=4) as executor:
            # Start all tasks concurrently
            left_split_future = executor.submit(split_four_fingers, left_fingers_path, 'left')
            right_split_future = executor.submit(split_four_fingers, right_fingers_path, 'right')
            left_thumb_future = executor.submit(copy_thumb, left_thumb_path, 'left')
            right_thumb_future = executor.submit(copy_thumb, right_thumb_path, 'right')
            
            # Get results
            left_split_paths = left_split_future.result()
            right_split_paths = right_split_future.result()
            left_thumb_path = left_thumb_future.result()
            right_thumb_path = right_thumb_future.result()
        
        # Verify and continue
        if not (left_split_paths and right_split_paths and left_thumb_path and right_thumb_path):
            # Try to continue with partial results
            if len(os.listdir(all_ten_dir)) < 5:  # Need at least half the fingers
                return False

        # Process all fingerprint images
        process_result = process_fingerprint_images()
        if not process_result:
            return False
            
        # Save with person ID
        final_paths = process_and_save_with_id()
        
        if not final_paths:
            return False
            
        # Clean up uploads directory
        for file in os.listdir(uploads_dir):
            if file.endswith('.jpg'):
                os.remove(os.path.join(uploads_dir, file))
        
        processing_time = time.time() - start_time
        print(f"Total processing completed in {processing_time:.2f} seconds")
        
        return final_paths

    except Exception as e:
        print(f"Error in start_processing: {str(e)}")
        return False