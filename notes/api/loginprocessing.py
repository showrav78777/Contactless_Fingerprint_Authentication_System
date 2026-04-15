# import time
# import cv2
# import os
# import numpy as np
# import matplotlib.pyplot as plt

# from concurrent.futures import ThreadPoolExecutor

# from skimage.morphology import skeletonize, thin
# from PIL import Image
# from rembg import remove,new_session
# from django.conf import settings

# import torch
# import torchvision.transforms.functional as TF

# NUM_WORKERS = min(8, os.cpu_count() or 1)
# MAX_IMAGE_SIZE = 500  # Max dimension for processing
# JPEG_QUALITY = 90     # Slightly reduced quality for faster processing
# MIN_CONTOUR_SIZE = 50
# CROP_SIZE = 256 

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



# # def split_four_fingers(image_path, hand_side):
# #     """Split four finger image into individual fingers"""
# #     try:
# #         image = Image.open(image_path)
# #         width, height = image.size
# #         finger_width = width // 4
# #         fingers = ['index', 'middle', 'ring', 'pinky']
# #         saved_paths = []

# #         # Create all_ten_fingers directory if it doesn't exist
# #         output_dir = os.path.join(settings.MEDIA_ROOT, 'all_ten_fingers')
# #         os.makedirs(output_dir, exist_ok=True)

# #         for i, finger in enumerate(fingers):
# #             # Crop individual finger
# #             left = i * finger_width
# #             right = (i + 1) * finger_width
# #             finger_image = image.crop((left, 0, right, height))
            
# #             # Save finger image
# #             filename = f"{hand_side}_{finger}.jpg"
# #             save_path = os.path.join(output_dir, filename)
# #             finger_image.save(save_path)
# #             saved_paths.append(save_path)

# #         return saved_paths

# #     except Exception as e:
# #         print(f"Error in split_four_fingers: {str(e)}")
# #         return []

# def split_four_fingers(image_path, hand_side):
#     """Split four finger image into individual fingers"""
#     try:
#         # Open image only once and reuse
#         image = Image.open(image_path)
#         width, height = image.size
#         fingers = ['index', 'middle', 'ring', 'pinky']
        
#         # Optimized width and position calculations
#         widths = [int(height * 0.51), int(height * 0.45), int(height * 0.45), int(height * 0.48)]
#         positions = [30, int(height * 0.52), int(height * 0.93), int(height * 1.4)]
        
#         # Create directory once before loop
#         output_dir = os.path.join(settings.MEDIA_ROOT, 'login')
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
    
# rembg_session = new_session()
# def process_image(image_path, use_gpu=True):
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
# # # Cache the processed images to avoid redundant processing
# # @lru_cache(maxsize=20)
# # def process_image(image_path):
# # #     """Process a single fingerprint image with caching"""
# # #     try:
# # #         image = Image.open(image_path)
# # #         filename = os.path.basename(image_path)
        
# # #         # Background removal
# # #         image_without_bg = remove(image)
        
# # #         # Optimize rotation logic
# # #         if 'thumb' in filename:
# # #             rotated_image = image_without_bg.rotate(-90, expand=True)
# # #         elif 'right_' in filename and not 'thumb' in filename:
# # #             rotated_image = image_without_bg.rotate(180, expand=True)
# # #         else:
# # #             rotated_image = image_without_bg
        
# # #         # # Create white background and paste in one operation
# # #         # white_bg = Image.new('RGB', rotated_image.size, (255, 255, 255))
# # #         # if rotated_image.mode == 'RGBA':
# # #         #     white_bg.paste(rotated_image, (0, 0), rotated_image.split()[3])
# # #         # else:
# # #         #     white_bg.paste(rotated_image, (0, 0))
# # #         if output_image.mode == 'RGBA':
# # #             white_bg = Image.new('RGB', output_image.size, (255, 255, 255))
# # #             white_bg.paste(output_image, mask=output_image.split()[3])
# # #             output_image = white_bg
        
        
         
# # #         # Process images
        
# # #             output_image_np = np.array(output_image)
# # #             image = extract_fingerprint_region(output_image_np)
    
# # #     # Enhance the image
# # #             enhanced = enhance_image(image)
    
# # #     # Apply adaptive thresholding for segmentation
# # #             binary = cv2.adaptiveThreshold(enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
# # #                                    cv2.THRESH_BINARY_INV, 11, 2)
    
# # #     # Apply Gabor filters for ridge enhancement
# # #             gabor_enhanced = apply_gabor_filters(enhanced)
    
# # #     # Apply skeletonization and thinning
# # #             skeleton = skeletonize(binary > 0)
# # #             skeleton_img = (skeleton * 255).astype(np.uint8)
    
# # #             thinned = thin(binary > 0)
# # #             thinned_img = (thinned * 255).astype(np.uint8)
    
# # #     # Minutiae detection using ORB
# # #             orb = cv2.ORB_create(nfeatures=1000)
# # #             keypoints = orb.detect(gabor_enhanced, None)
# # #             minutiae_img = cv2.drawKeypoints(gabor_enhanced, keypoints, None, color=(0,0,255), flags=0)
    
# # #     # Convert minutiae image to grayscale
# # #             minutiae_img_gray = cv2.cvtColor(minutiae_img, cv2.COLOR_BGR2GRAY)
         
# # #     # Combine minutiae image with thinned image
# # #             x_output = cv2.addWeighted(minutiae_img_gray, 0.6, thinned_img, 0.4, 0)
    
# # #     # Invert the image (White ridges, Black background)
# # #             final_output = cv2.bitwise_not(x_output)
# # #             final_output_pil = Image.fromarray(final_output)
# # # # Optimize rotation logic
# # #         if 'thumb' in filename:
# # #             final_output_pil = final_output_pil.rotate(-90, expand=True)
# # #         elif 'right_' in filename and not 'thumb' in filename:
# # #             final_output_pil = final_output_pil.rotate(180, expand=True)
# # #         elif 'left_' in filename and not 'thumb' in filename:
# # #             final_output_pil = final_output_pil.rotate(0, expand=True)
            
# # #         return final_output_pil        
        
# # #     except Exception as e:
# # #         print(f"Error processing image {image_path}: {str(e)}")
# # #         return None

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
#     """Process all fingerprint images in login directory with parallelism"""
#     try:
#         login_dir = os.path.join(settings.MEDIA_ROOT, 'login')
#         image_files = [f for f in os.listdir(login_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        
#         # Process images in parallel using ThreadPoolExecutor
#         with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
#             # Create a list of (image_path, future) tuples
#             futures = []
#             for image_file in image_files:
#                 image_path = os.path.join(login_dir, image_file)
#                 futures.append((image_path, executor.submit(process_image, image_path)))
            
#             # Save results as they complete
#             for image_path, future in futures:
#                 processed_image = future.result()
#                 if processed_image:
#                     processed_image.save(image_path, quality=95, optimize=True)
        
#         return True
#     except Exception as e:
#         print(f"Error processing fingerprint images: {str(e)}")
#         return False

# def copy_thumb(thumb_path, hand_side):
#     """Copy and preprocess thumb image to focus on the fingertip region"""
#     try:
#         output_dir = os.path.join(settings.MEDIA_ROOT, 'login')
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

# def check_all_images_present():
#     """Check if all required images are present in login_temp"""
#     login_temp_dir = os.path.join(settings.MEDIA_ROOT, 'login_temp')
    
#     if not os.path.exists(login_temp_dir):
#         return False
    
#     required_files = {'left_thumb.jpg', 'right_thumb.jpg', '4_left_fingers.jpg', '4_right_fingers.jpg'}
    
#     # Using a set for faster lookups
#     existing_files = set(os.listdir(login_temp_dir))
    
#     # Fast set operation to check if all required files exist
#     return required_files.issubset(existing_files)

# def start_processing():
#     """Start processing all images with optimizations"""
#     start_time = time.time()
#     try:
#         # Check required images first to avoid unnecessary work
#         if not check_all_images_present():
#             print("Not all required images are present")
#             return False
        
#         # Setup directories
#         login_dir = os.path.join(settings.MEDIA_ROOT, 'login')
#         login_temp_dir = os.path.join(settings.MEDIA_ROOT, 'login_temp')
        
#         # Create login directory if it doesn't exist
#         os.makedirs(login_dir, exist_ok=True)
        
#         # Clear login directory in one pass
#         for file in os.listdir(login_dir):
#             os.remove(os.path.join(login_dir, file))
        
#         # Get paths to the required images
#         left_fingers_path = os.path.join(login_temp_dir, '4_left_fingers.jpg')
#         right_fingers_path = os.path.join(login_temp_dir, '4_right_fingers.jpg')
#         left_thumb_path = os.path.join(login_temp_dir, 'left_thumb.jpg')
#         right_thumb_path = os.path.join(login_temp_dir, 'right_thumb.jpg')
        
#         # Batch process thumbs and finger splitting in parallel
#         with ThreadPoolExecutor(max_workers=4) as executor:
#             # Start all tasks concurrently
#             left_split_future = executor.submit(split_four_fingers, left_fingers_path, 'left')
#             right_split_future = executor.submit(split_four_fingers, right_fingers_path, 'right')
#             left_thumb_future = executor.submit(copy_thumb, left_thumb_path, 'left')
#             right_thumb_future = executor.submit(copy_thumb, right_thumb_path, 'right')
            
#             # Get results
#             left_split_paths = left_split_future.result()
#             right_split_paths = right_split_future.result()
#             left_thumb_result = left_thumb_future.result()
#             right_thumb_result = right_thumb_future.result()
        
#         # Process all fingerprints after splitting and copying
#         process_result = process_fingerprint_images()
        
#         # Verify results
#         login_files = set(os.listdir(login_dir))
#         expected_files = {
#             'left_thumb.jpg', 'left_index.jpg', 'left_middle.jpg', 'left_ring.jpg', 'left_pinky.jpg',
#             'right_thumb.jpg', 'right_index.jpg', 'right_middle.jpg', 'right_ring.jpg', 'right_pinky.jpg'
#         }
        
#         # Check for missing files
#         missing_files = expected_files - login_files
        
#         # Handle missing files more efficiently
#         if missing_files:
#             print(f"Missing files: {missing_files}")
            
#             # Direct file copy for any missing thumbs
#             if 'left_thumb.jpg' in missing_files and os.path.exists(left_thumb_path):
#                 Image.open(left_thumb_path).save(os.path.join(login_dir, 'left_thumb.jpg'))
                
#             if 'right_thumb.jpg' in missing_files and os.path.exists(right_thumb_path):
#                 Image.open(right_thumb_path).save(os.path.join(login_dir, 'right_thumb.jpg'))
            
#             # Check if we have enough files to proceed
#             if len(login_files) < 6:
#                 return False
        
#         # Remove unexpected files if any
#         unexpected_files = login_files - expected_files
#         for file in unexpected_files:
#             os.remove(os.path.join(login_dir, file))
        
#         processing_time = time.time() - start_time
#         print(f"Total processing completed in {processing_time:.2f} seconds")
#         return True
#     except Exception as e:
#         print(f"Error in start_processing: {str(e)}")
#         return False


import time
import cv2
import os
import numpy as np
import matplotlib.pyplot as plt

from concurrent.futures import ThreadPoolExecutor


from PIL import Image
from rembg import remove,new_session
from django.conf import settings

import torch
import torchvision.transforms.functional as TF

NUM_WORKERS = min(8, os.cpu_count() or 1)
MAX_IMAGE_SIZE = 500  # Max dimension for processing
JPEG_QUALITY = 90     # Slightly reduced quality for faster processing
MIN_CONTOUR_SIZE = 50
CROP_SIZE = 256 

def apply_gabor_filters(image):
    ksize = 1
    sigma = 4.0
    lamda = np.pi / 4
    gamma = 0.5
    orientations = [0, np.pi/4, np.pi/2, 3*np.pi/4]
    filtered_images = []
    
    for theta in orientations:
        gabor_kernel = cv2.getGaborKernel((ksize, ksize), sigma, theta, lamda, gamma, ktype=cv2.CV_32F)
        filtered_images.append(cv2.filter2D(image, cv2.CV_8UC3, gabor_kernel))
    
    return np.mean(filtered_images, axis=0).astype(np.uint8)

# Function to extract fingerprint ROI and remove outer border
def extract_fingerprint_region(image):
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Apply Otsu's thresholding
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    # Find contours
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if contours:
        # Find largest contour (finger)
        largest_contour = max(contours, key=cv2.contourArea)
        
        # Create mask
        mask = np.zeros_like(gray)
        cv2.drawContours(mask, [largest_contour], -1, 255, -1)
        
        # Erode the mask to remove border
        kernel_erode = np.ones((40, 40), np.uint8)
        eroded_mask = cv2.erode(mask, kernel_erode, iterations=1)
        
        # Get the coordinates of the fingerprint area
        coords = cv2.findNonZero(eroded_mask)
        x, y, w, h = cv2.boundingRect(coords)
        
        # Apply the eroded mask to the original image
        result = cv2.bitwise_and(image, image, mask=eroded_mask)
        
        # Crop the image to remove empty borders
        cropped = result[y:y+h, x:x+w]
        
        return cropped
    
    return image

# Function to enhance image contrast and sharpness
def enhance_image(image):
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Apply CLAHE to enhance contrast
    clahe = cv2.createCLAHE(clipLimit=5.0, tileGridSize=(8,8))
    enhanced = clahe.apply(gray)
    
    # Sharpen the image
    kernel = np.array([[0, -1, 0],
                       [-1, 5,-1],
                       [0, -1, 0]])
    sharpened = cv2.filter2D(enhanced, -1, kernel)
    
    return sharpened



# def split_four_fingers(image_path, hand_side):
#     """Split four finger image into individual fingers"""
#     try:
#         image = Image.open(image_path)
#         width, height = image.size
#         finger_width = width // 4
#         fingers = ['index', 'middle', 'ring', 'pinky']
#         saved_paths = []

#         # Create all_ten_fingers directory if it doesn't exist
#         output_dir = os.path.join(settings.MEDIA_ROOT, 'all_ten_fingers')
#         os.makedirs(output_dir, exist_ok=True)

#         for i, finger in enumerate(fingers):
#             # Crop individual finger
#             left = i * finger_width
#             right = (i + 1) * finger_width
#             finger_image = image.crop((left, 0, right, height))
            
#             # Save finger image
#             filename = f"{hand_side}_{finger}.jpg"
#             save_path = os.path.join(output_dir, filename)
#             finger_image.save(save_path)
#             saved_paths.append(save_path)

#         return saved_paths

#     except Exception as e:
#         print(f"Error in split_four_fingers: {str(e)}")
#         return []

def split_four_fingers(image_path, hand_side):
    """Split four finger image into individual fingers"""
    try:
        # Open image only once and reuse
        image = Image.open(image_path)
        width, height = image.size
        fingers = ['index', 'middle', 'ring', 'pinky']
        
        # Optimized width and position calculations
        widths = [int(height * 0.51), int(height * 0.45), int(height * 0.45), int(height * 0.48)]
        positions = [30, int(height * 0.52), int(height * 0.93), int(height * 1.4)]
        
        # Create directory once before loop
        output_dir = os.path.join(settings.MEDIA_ROOT, 'login')
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
    
rembg_session = new_session()
def process_image(image_path, use_gpu=True):
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
# # Cache the processed images to avoid redundant processing
# @lru_cache(maxsize=20)
# def process_image(image_path):
# #     """Process a single fingerprint image with caching"""
# #     try:
# #         image = Image.open(image_path)
# #         filename = os.path.basename(image_path)
        
# #         # Background removal
# #         image_without_bg = remove(image)
        
# #         # Optimize rotation logic
# #         if 'thumb' in filename:
# #             rotated_image = image_without_bg.rotate(-90, expand=True)
# #         elif 'right_' in filename and not 'thumb' in filename:
# #             rotated_image = image_without_bg.rotate(180, expand=True)
# #         else:
# #             rotated_image = image_without_bg
        
# #         # # Create white background and paste in one operation
# #         # white_bg = Image.new('RGB', rotated_image.size, (255, 255, 255))
# #         # if rotated_image.mode == 'RGBA':
# #         #     white_bg.paste(rotated_image, (0, 0), rotated_image.split()[3])
# #         # else:
# #         #     white_bg.paste(rotated_image, (0, 0))
# #         if output_image.mode == 'RGBA':
# #             white_bg = Image.new('RGB', output_image.size, (255, 255, 255))
# #             white_bg.paste(output_image, mask=output_image.split()[3])
# #             output_image = white_bg
        
        
         
# #         # Process images
        
# #             output_image_np = np.array(output_image)
# #             image = extract_fingerprint_region(output_image_np)
    
# #     # Enhance the image
# #             enhanced = enhance_image(image)
    
# #     # Apply adaptive thresholding for segmentation
# #             binary = cv2.adaptiveThreshold(enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
# #                                    cv2.THRESH_BINARY_INV, 11, 2)
    
# #     # Apply Gabor filters for ridge enhancement
# #             gabor_enhanced = apply_gabor_filters(enhanced)
    
# #     # Apply skeletonization and thinning
# #             skeleton = skeletonize(binary > 0)
# #             skeleton_img = (skeleton * 255).astype(np.uint8)
    
# #             thinned = thin(binary > 0)
# #             thinned_img = (thinned * 255).astype(np.uint8)
    
# #     # Minutiae detection using ORB
# #             orb = cv2.ORB_create(nfeatures=1000)
# #             keypoints = orb.detect(gabor_enhanced, None)
# #             minutiae_img = cv2.drawKeypoints(gabor_enhanced, keypoints, None, color=(0,0,255), flags=0)
    
# #     # Convert minutiae image to grayscale
# #             minutiae_img_gray = cv2.cvtColor(minutiae_img, cv2.COLOR_BGR2GRAY)
         
# #     # Combine minutiae image with thinned image
# #             x_output = cv2.addWeighted(minutiae_img_gray, 0.6, thinned_img, 0.4, 0)
    
# #     # Invert the image (White ridges, Black background)
# #             final_output = cv2.bitwise_not(x_output)
# #             final_output_pil = Image.fromarray(final_output)
# # # Optimize rotation logic
# #         if 'thumb' in filename:
# #             final_output_pil = final_output_pil.rotate(-90, expand=True)
# #         elif 'right_' in filename and not 'thumb' in filename:
# #             final_output_pil = final_output_pil.rotate(180, expand=True)
# #         elif 'left_' in filename and not 'thumb' in filename:
# #             final_output_pil = final_output_pil.rotate(0, expand=True)
            
# #         return final_output_pil        
        
# #     except Exception as e:
# #         print(f"Error processing image {image_path}: {str(e)}")
# #         return None

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
    """Process all fingerprint images in login directory with parallelism"""
    try:
        login_dir = os.path.join(settings.MEDIA_ROOT, 'login')
        image_files = [f for f in os.listdir(login_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        
        # Process images in parallel using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
            # Create a list of (image_path, future) tuples
            futures = []
            for image_file in image_files:
                image_path = os.path.join(login_dir, image_file)
                futures.append((image_path, executor.submit(process_image, image_path)))
            
            # Save results as they complete
            for image_path, future in futures:
                processed_image = future.result()
                if processed_image:
                    processed_image.save(image_path, quality=95, optimize=True)
        
        return True
    except Exception as e:
        print(f"Error processing fingerprint images: {str(e)}")
        return False

def copy_thumb(thumb_path, hand_side):
    """Copy and preprocess thumb image to focus on the fingertip region"""
    try:
        output_dir = os.path.join(settings.MEDIA_ROOT, 'login')
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

def check_all_images_present():
    """Check if all required images are present in login_temp"""
    login_temp_dir = os.path.join(settings.MEDIA_ROOT, 'login_temp')
    
    if not os.path.exists(login_temp_dir):
        return False
    
    required_files = {'left_thumb.jpg', 'right_thumb.jpg', '4_left_fingers.jpg', '4_right_fingers.jpg'}
    
    # Using a set for faster lookups
    existing_files = set(os.listdir(login_temp_dir))
    
    # Fast set operation to check if all required files exist
    return required_files.issubset(existing_files)

def start_processing():
    """Start processing all images with optimizations"""
    start_time = time.time()
    try:
        # Check required images first to avoid unnecessary work
        if not check_all_images_present():
            print("Not all required images are present")
            return False
        
        # Setup directories
        login_dir = os.path.join(settings.MEDIA_ROOT, 'login')
        login_temp_dir = os.path.join(settings.MEDIA_ROOT, 'login_temp')
        
        # Create login directory if it doesn't exist
        os.makedirs(login_dir, exist_ok=True)
        
        # Clear login directory in one pass
        for file in os.listdir(login_dir):
            os.remove(os.path.join(login_dir, file))
        
        # Get paths to the required images
        left_fingers_path = os.path.join(login_temp_dir, '4_left_fingers.jpg')
        right_fingers_path = os.path.join(login_temp_dir, '4_right_fingers.jpg')
        left_thumb_path = os.path.join(login_temp_dir, 'left_thumb.jpg')
        right_thumb_path = os.path.join(login_temp_dir, 'right_thumb.jpg')
        
        # Batch process thumbs and finger splitting in parallel
        with ThreadPoolExecutor(max_workers=4) as executor:
            # Start all tasks concurrently
            left_split_future = executor.submit(split_four_fingers, left_fingers_path, 'left')
            right_split_future = executor.submit(split_four_fingers, right_fingers_path, 'right')
            left_thumb_future = executor.submit(copy_thumb, left_thumb_path, 'left')
            right_thumb_future = executor.submit(copy_thumb, right_thumb_path, 'right')
            
            # Get results
            left_split_paths = left_split_future.result()
            right_split_paths = right_split_future.result()
            left_thumb_result = left_thumb_future.result()
            right_thumb_result = right_thumb_future.result()
        
        # Process all fingerprints after splitting and copying
        process_result = process_fingerprint_images()
        
        # Verify results
        login_files = set(os.listdir(login_dir))
        expected_files = {
            'left_thumb.jpg', 'left_index.jpg', 'left_middle.jpg', 'left_ring.jpg', 'left_pinky.jpg',
            'right_thumb.jpg', 'right_index.jpg', 'right_middle.jpg', 'right_ring.jpg', 'right_pinky.jpg'
        }
        
        # Check for missing files
        missing_files = expected_files - login_files
        
        # Handle missing files more efficiently
        if missing_files:
            print(f"Missing files: {missing_files}")
            
            # Direct file copy for any missing thumbs
            if 'left_thumb.jpg' in missing_files and os.path.exists(left_thumb_path):
                Image.open(left_thumb_path).save(os.path.join(login_dir, 'left_thumb.jpg'))
                
            if 'right_thumb.jpg' in missing_files and os.path.exists(right_thumb_path):
                Image.open(right_thumb_path).save(os.path.join(login_dir, 'right_thumb.jpg'))
            
            # Check if we have enough files to proceed
            if len(login_files) < 6:
                return False
        
        # Remove unexpected files if any
        unexpected_files = login_files - expected_files
        for file in unexpected_files:
            os.remove(os.path.join(login_dir, file))
        
        processing_time = time.time() - start_time
        print(f"Total processing completed in {processing_time:.2f} seconds")
        return True
    except Exception as e:
        print(f"Error in start_processing: {str(e)}")
        return False

# def get_fingertip_region(gray_image, contour, mask):
#     """Get clean fingerprint pattern with white background"""
#     try:
#         # Initial bounding box
#         x, y, w, h = cv2.boundingRect(contour)
        
#         # Get fingertip region
#         tip_start_y = y
#         tip_height = int(h * 0.75)  # Take top 50% of finger
#         fingertip = gray_image[tip_start_y:tip_start_y+tip_height, x:x+w]
        
#         # Create initial binary mask
#         _, binary_mask = cv2.threshold(fingertip, 127, 255, cv2.THRESH_BINARY_INV)
#         inner_contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
#         if inner_contours:
#             # Get precise fingerprint area
#             inner_contour = max(inner_contours, key=cv2.contourArea)
#             ix, iy, iw, ih = cv2.boundingRect(inner_contour)
            
#             # Crop to fingerprint area
#             fingerprint = fingertip[iy:iy+ih, ix:ix+iw]
            
#             # Enhance fingerprint
#             blurred = cv2.GaussianBlur(fingerprint, (9, 9), 0)
            
#             # Adaptive thresholding for ridge detection
#             binary = cv2.adaptiveThreshold(
#                 blurred, 
#                 255, 
#                 cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
#                 cv2.THRESH_BINARY,
#                 43, 
#                 3
#             )
            
#             # Clean up the pattern
#             kernel = np.ones((3, 3), np.uint8)
#             cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
#             cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel)
            
#             # Invert to get black ridges on white background
#             final = cv2.bitwise_not(cleaned)
            
#             return final
            
#         return None
        
#     except Exception as e:
#         print(f"Error getting fingertip region: {str(e)}")
#         return None