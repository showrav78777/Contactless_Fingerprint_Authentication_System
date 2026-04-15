import cv2
import os
import numpy as np
from tqdm import tqdm
from glob import glob
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.poincare import calculate_singularities
from src.segmentation import create_segmented_and_variance_images
from src.normalization import normalize
from src.gabor_filter import gabor_filter
from src.frequency import ridge_freq
from src import orientation
from src.crossing_number import calculate_minutiaes
from src.skeletonize import skeletonize

def fingerprint_pipeline(input_img):
    block_size = 16

    # Normalization
    normalized_img = normalize(input_img.copy(), float(100), float(100))

    # ROI and normalization
    (segmented_img, normim, mask) = create_segmented_and_variance_images(normalized_img, block_size, 0.2)

    # Orientations
    angles = orientation.calculate_angles(normalized_img, W=block_size, smoth=False)
    orientation_img = orientation.visualize_angles(segmented_img, mask, angles, W=block_size)

    # Ridge frequency
    freq = ridge_freq(normim, mask, angles, block_size, kernel_size=5, minWaveLength=5, maxWaveLength=15)

    # Gabor filtering
    gabor_img = gabor_filter(normim, angles, freq)

    # Skeletonization
    thin_image = skeletonize(gabor_img)

    # Minutiae extraction
    minutias = calculate_minutiaes(thin_image)

    # Singularities detection
    singularities_img = calculate_singularities(thin_image, angles, 1, block_size, mask)

    # Resize to target size (300x300)
    target_size = (300, 300)
    gabor_img = cv2.resize(gabor_img, target_size)
    thin_image = cv2.resize(thin_image, target_size)
    minutias = cv2.resize(minutias, target_size)

    return {
        'gabor': gabor_img,
        'skeleton': thin_image,
        'minutiae': minutias
    }

def process_dataset(input_dir, output_dir):
    """
    Process all images in the dataset directory
    """
    # Verify input directory exists
    if not os.path.exists(input_dir):
        raise ValueError(f"Input directory {input_dir} does not exist")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    logging.info(f"Created output directory: {output_dir}")

    # Create output subdirectories
    for subdir in ['gabor', 'skeleton', 'minutiae']:
        os.makedirs(os.path.join(output_dir, subdir), exist_ok=True)
        logging.info(f"Created subdirectory: {subdir}")

    # Get all person directories
    person_dirs = [d for d in os.listdir(input_dir) if os.path.isdir(os.path.join(input_dir, d))]
    logging.info(f"Found {len(person_dirs)} person directories")
    
    for person_id in tqdm(person_dirs, desc="Processing persons"):
        person_dir = os.path.join(input_dir, person_id)
        output_person_dir = os.path.join(output_dir, person_id)
        
        # Create output directories for this person
        for subdir in ['gabor', 'skeleton', 'minutiae']:
            os.makedirs(os.path.join(output_person_dir, subdir), exist_ok=True)
        
        # Process each image
        image_files = [f for f in os.listdir(person_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        logging.info(f"Processing {len(image_files)} images for person {person_id}")
        
        for img_file in tqdm(image_files, desc=f"Processing {person_id}", leave=False):
            img_path = os.path.join(person_dir, img_file)
            
            try:
                # Read image
                img = cv2.imread(img_path, 0)
                if img is None:
                    logging.error(f"Failed to read image: {img_path}")
                    continue
                
                # Process image
                results = fingerprint_pipeline(img)
                
                # Save processed images
                base_name = os.path.splitext(img_file)[0]
                for key, processed_img in results.items():
                    output_path = os.path.join(output_person_dir, key, f"{base_name}.png")
                    success = cv2.imwrite(output_path, processed_img)
                    if not success:
                        logging.error(f"Failed to save image: {output_path}")
                    else:
                        logging.debug(f"Saved image: {output_path}")
                    
            except Exception as e:
                logging.error(f"Error processing {img_path}: {str(e)}")

if __name__ == '__main__':
    input_dir = 'data/new_dataset'
    output_dir = 'data/processed_dataset'
    
    try:
        process_dataset(input_dir, output_dir)
        logging.info("Processing completed successfully")
    except Exception as e:
        logging.error(f"Processing failed: {str(e)}") 