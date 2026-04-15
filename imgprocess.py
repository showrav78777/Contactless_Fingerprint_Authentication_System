import cv2
import numpy as np
import os
import glob
import matplotlib.pyplot as plt
from skimage.morphology import skeletonize, thin
from google.colab import drive

# Mount Google Drive
drive.mount('/content/drive')

# Define image path
image_folder = "/content/drive/MyDrive/f_images/finger/white"
output_folder = "/content/drive/MyDrive/f_images/finger/white/FINAL_output"

# Create output folder if not exists
os.makedirs(output_folder, exist_ok=True)

image_paths = glob.glob(os.path.join(image_folder, "*.png"))

# Function to apply Gabor filters for ridge enhancement
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



# Process images
for img_path in image_paths:
    image = cv2.imread(img_path)
    image = extract_fingerprint_region(image)
    
    # Enhance the image
    enhanced = enhance_image(image)
    
    # Apply adaptive thresholding for segmentation
    binary = cv2.adaptiveThreshold(enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                   cv2.THRESH_BINARY_INV, 11, 2)
    
    # Apply Gabor filters for ridge enhancement
    gabor_enhanced = apply_gabor_filters(enhanced)
    
    # Apply skeletonization and thinning
    skeleton = skeletonize(binary > 0)
    skeleton_img = (skeleton * 255).astype(np.uint8)
    
    thinned = thin(binary > 0)
    thinned_img = (thinned * 255).astype(np.uint8)
    
    # Minutiae detection using ORB
    orb = cv2.ORB_create(nfeatures=1000)
    keypoints = orb.detect(gabor_enhanced, None)
    minutiae_img = cv2.drawKeypoints(gabor_enhanced, keypoints, None, color=(0,0,255), flags=0)
    
    # Convert minutiae image to grayscale
    minutiae_img_gray = cv2.cvtColor(minutiae_img, cv2.COLOR_BGR2GRAY)
    
    # Combine minutiae image with thinned image
    x_output = cv2.addWeighted(minutiae_img_gray, 0.6, thinned_img, 0.4, 0)
    
    # Invert the image (White ridges, Black background)
    final_output = cv2.bitwise_not(x_output)

    # Save final output
    output_path = os.path.join(output_folder, os.path.basename(img_path))
    cv2.imwrite(output_path, final_output)

    # Display final output
    plt.figure(figsize=(6,6))
    plt.imshow(final_output, cmap='gray')
    plt.axis('off')
    plt.title("Final Fingerprint Output")
    plt.show()