import os
import cv2
import numpy as np
import math
import json

# Directory paths
INPUT_FOLDER = "/Users/niloyshowrav/Downloads/SNN/data/finger"  # Path to the folder containing fingerprint images
OUTPUT_FOLDER = "/Users/niloyshowrav/Downloads/SNN/data/annotation"  # Path to save generated minutiae labels

def extract_minutiae(image_path):
    """
    Extract minutiae points (x, y, theta) from a fingerprint image.
    Args:
        image_path: Path to the fingerprint image.
    Returns:
        A list of minutiae points as (x, y, theta).
    """
    # Load the image in grayscale
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise ValueError(f"Cannot read image file: {image_path}")
    
    # Binarize the image using Otsu's thresholding
    _, binarized_image = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Apply thinning (make ridge lines 1-pixel wide)
    thin_image = cv2.ximgproc.thinning(binarized_image)

    # Extract minutiae points
    minutiae_points = find_minutiae(thin_image)
    return minutiae_points

def find_minutiae(thin_image):
    """
    Identify minutiae points (endings and bifurcations) in the thinned fingerprint image.
    Args:
        thin_image: Thinned binary fingerprint image.
    Returns:
        A list of minutiae points (x, y, theta).
    """
    minutiae_points = []
    rows, cols = thin_image.shape

    # Precompute neighbors' offsets for 3x3 neighborhood
    neighbors_offset = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

    for i in range(1, rows - 1):
        for j in range(1, cols - 1):
            if thin_image[i, j] == 255:  # If it's a ridge pixel
                # Get the 3x3 neighborhood as a flattened array
                neighborhood = [
                    thin_image[i + dx, j + dy]
                    for dx, dy in neighbors_offset
                ]
                ridge_count = sum(pixel == 255 for pixel in neighborhood)

                # Check for ridge ending (1 white neighbor) or bifurcation (3 white neighbors)
                if ridge_count in [1, 3]:
                    angle = calculate_orientation(thin_image, i, j)
                    minutiae_points.append((i, j, angle))

    return minutiae_points

def calculate_orientation(image, x, y):
    """
    Calculate the orientation (angle) of the minutiae point.
    Args:
        image: The thinned binary fingerprint image.
        x, y: Coordinates of the minutiae point.
    Returns:
        The orientation angle in radians.
    """
    # Apply Sobel operator to get gradients
    gradient_x = cv2.Sobel(image, cv2.CV_64F, 1, 0, ksize=3)
    gradient_y = cv2.Sobel(image, cv2.CV_64F, 0, 1, ksize=3)

    # Compute angle (avoid division by zero with epsilon)
    epsilon = 1e-8
    angle = math.atan2(gradient_y[x, y], gradient_x[x, y] + epsilon)
    return angle

def process_folders(input_folder, output_folder):
    """
    Process each subdirectory in the input folder, extract minutiae, and save them in the output folder.
    Args:
        input_folder: Root folder containing subdirectories of fingerprint images.
        output_folder: Root folder to save minutiae label files.
    """
    for subdir in os.listdir(input_folder):
        subdir_path = os.path.join(input_folder, subdir)
        if not os.path.isdir(subdir_path):
            continue

        output_subdir = os.path.join(output_folder, subdir)
        os.makedirs(output_subdir, exist_ok=True)

        image_files = sorted(os.listdir(subdir_path))
        valid_extensions = {".jpg", ".jpeg", ".png", ".bmp"}  # Supported image formats

        for image_file in image_files:
            if not os.path.splitext(image_file)[1].lower() in valid_extensions:
                print(f"Skipping unsupported file: {image_file}")
                continue

            image_path = os.path.join(subdir_path, image_file)
            print(f"Processing file: {image_path}")

            try:
                # Extract minutiae
                minutiae = extract_minutiae(image_path)
                # Save minutiae to a JSON file
                output_file = os.path.join(output_subdir, f"{os.path.splitext(image_file)[0]}.json")
                with open(output_file, 'w') as f:
                    json.dump([(x, y, theta) for x, y, theta in minutiae], f, indent=4)
                print(f"Saved minutiae to {output_file}")
            except Exception as e:
                print(f"Error processing {image_file}: {e}")

# Run the processing
if __name__ == "__main__":
    process_folders(INPUT_FOLDER, OUTPUT_FOLDER)