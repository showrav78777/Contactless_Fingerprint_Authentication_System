import os
import cv2
import torch
import numpy as np
from PIL import Image
from pathlib import Path
import torch.nn.functional as F
from src.model import SiameseNetwork
from src.utils import transform_val

class FingerprintMatcher:
    def __init__(self, model_path='models/new.pth', database_path='data/finger', annotation_path='data/annotation'):
        # Set up device (prioritize MPS for Mac)
        if torch.backends.mps.is_available() and torch.backends.mps.is_built():
            self.device = torch.device("mps")
            print("Using MPS (Metal Performance Shaders) for M-series Mac")
        else:
            self.device = torch.device("cpu")
            print("MPS not available, falling back to CPU")
        
        print(f"Using device: {self.device}")
        
        # Load model
        self.model = self.load_model(model_path)
        
        # Set up database and annotation paths
        self.database_path = Path(database_path)
        self.annotation_path = Path(annotation_path)
        
        # Threshold for matching
        self.threshold = 0.90
        self.margin = 2.0
    
    def load_model(self, model_path):
        """Load and prepare the Siamese model"""
        try:
            model = SiameseNetwork().to(self.device)
            state_dict = torch.load(model_path, map_location=self.device)
            model.load_state_dict(state_dict, strict=False)
            model.eval()
            return model
        except Exception as e:
            raise RuntimeError(f"Error loading model: {e}")

    def preprocess_image(self, image):
        """Preprocess a single image for the model"""
        if transform_val:
            image = transform_val(image)
        return image.unsqueeze(0).to(self.device)

    def compute_similarity(self, img1, img2):
        """Compute similarity between two fingerprint images"""
        with torch.no_grad():
            output1, output2 = self.model(img1, img2)
            distance = F.pairwise_distance(output1, output2)
            similarity = 1 - (distance.item() / self.margin)  # Normalize to [0,1]
            return similarity, distance.item()

    def compare_fingerprints(self, img_path1, img_path2):
        """Compare two fingerprint images and return similarity score"""
        try:
            # Load and preprocess images
            img1 = Image.open(img_path1).convert('L')
            img2 = Image.open(img_path2).convert('L')
            
            # Transform images
            img1_tensor = self.preprocess_image(img1)
            img2_tensor = self.preprocess_image(img2)
            
            # Compute similarity
            similarity, distance = self.compute_similarity(img1_tensor, img2_tensor)
            is_match = similarity >= self.threshold
            
            return is_match, similarity, distance
            
        except Exception as e:
            raise RuntimeError(f"Error comparing fingerprints: {e}")

    def find_match_in_database(self, test_dir):
        """
        Find matching fingerprints in the database
        Args:
            test_dir: Directory containing the test fingerprint images
        Returns: (matched, person_id, match_scores)
        """
        if not self.database_path.exists():
            raise FileNotFoundError(f"Database directory not found: {self.database_path}")

        best_match_score = 0
        best_match_id = None
        all_match_scores = {}

        # Get all person directories in database
        person_dirs = [d for d in self.database_path.iterdir() if d.is_dir()]

        if not person_dirs:
            raise RuntimeError("No registered fingerprints found in the database.")

        # Get list of test fingerprint images
        test_files = sorted([f for f in os.listdir(test_dir) 
                           if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))])

        for person_dir in person_dirs:
            person_id = person_dir.name
            match_count = 0
            finger_scores = []

            # Get list of stored fingerprint images
            stored_files = sorted([f for f in os.listdir(person_dir) 
                                 if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))])
            
            if len(stored_files) != len(test_files):
                print(f"Warning: Number of fingerprints doesn't match for person {person_id}")
                continue

            # Compare each test fingerprint with corresponding stored fingerprint
            for test_file, stored_file in zip(test_files, stored_files):
                test_path = os.path.join(test_dir, test_file)
                stored_path = os.path.join(person_dir, stored_file)
                
                try:
                    is_match, similarity, distance = self.compare_fingerprints(test_path, stored_path)
                finger_scores.append(similarity)
                
                    if is_match:
                    match_count += 1
                except Exception as e:
                    print(f"Error comparing {test_file} with {stored_file}: {e}")
                    continue

            # Calculate overall match score for this person
            match_percentage = match_count / len(test_files)
            all_match_scores[person_id] = {
                'overall_score': match_percentage,
                'finger_scores': finger_scores
            }
            
            if match_percentage > best_match_score:
                best_match_score = match_percentage
                best_match_id = person_id

        return best_match_score >= 0.9, best_match_id, all_match_scores

    def verify_identity(self, test_dir):
        """Main function to verify identity using fingerprints"""
        print("Starting fingerprint verification...")
        
        if not os.path.isdir(test_dir):
            print(f"Error: Directory not found: {test_dir}")
            return
        
        print(f"Loading fingerprints from directory: {test_dir}")
        
        try:
        # Find matches in database
            matched, person_id, match_scores = self.find_match_in_database(test_dir)
        
        # Display results
        if matched:
            print(f"\nMATCH FOUND!")
            print(f"Person ID: {person_id}")
            print("\nMatch scores for each finger:")
            scores = match_scores[person_id]['finger_scores']
                for i, score in enumerate(scores):
                    print(f"Finger {i+1}: {score*100:.2f}%")
            print(f"\nOverall match score: {match_scores[person_id]['overall_score']*100:.2f}%")
        else:
            print("\nNO MATCH FOUND")
            if person_id:
                print(f"Best match (below threshold) - Person ID: {person_id}")
                print(f"Match score: {match_scores[person_id]['overall_score']*100:.2f}%")
        except Exception as e:
            print(f"Error during verification: {str(e)}")

def main():
    # Initialize matcher
    matcher = FingerprintMatcher()
    
    while True:
        print("\nFingerprint Verification System")
        print("1. Verify Identity")
        print("2. Exit")
        
        choice = input("Enter your choice (1-2): ")
        
        if choice == '1':
            test_dir = input("Enter the directory path containing the test fingerprint images: ")
            matcher.verify_identity(test_dir)
        elif choice == '2':
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main() 