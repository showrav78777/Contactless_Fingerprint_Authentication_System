# import torch
# import torch.nn.functional as F
# from torchvision import transforms
# from PIL import Image
# import matplotlib.pyplot as plt
# import os

# from src.model import SiameseNetwork  # Ensure this path is correct
# from src.utils import transform_val  # Ensure this path is correct

# # Constants
# MARGIN = 2.0

# def test_single_pair(model, img_path1, img_path2, transform, device, threshold=0.90):
#     model.eval()
    
#     # Load and preprocess images
#     img1 = Image.open(img_path1).convert('L')
#     img2 = Image.open(img_path2).convert('L')
    
#     if transform:
#         img1 = transform(img1)
#         img2 = transform(img2)
    
#     # Add batch dimension
#     img1 = img1.unsqueeze(0).to(device)
#     img2 = img2.unsqueeze(0).to(device)
    
#     with torch.no_grad():
#         output1, output2 = model(img1, img2)
#         distance = F.pairwise_distance(output1, output2)
        
#         similarity = 1 - (distance.item() / MARGIN)  # Normalized similarity score
#         is_same = similarity >= threshold
    
#     return is_same, similarity, distance.item()

# def visualize_comparison(img_path1, img_path2, is_same, similarity):
#     fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5))
    
#     img1 = Image.open(img_path1).convert('L')
#     img2 = Image.open(img_path2).convert('L')
    
#     ax1.imshow(img1, cmap='gray')
#     ax1.set_title('Fingerprint 1')
#     ax1.axis('off')
    
#     ax2.imshow(img2, cmap='gray')
#     ax2.set_title('Fingerprint 2')
#     ax2.axis('off')
    
#     result = "MATCH" if is_same else "NO MATCH"
#     similarity_percentage = similarity * 100
#     plt.suptitle(f'Result: {result}\nSimilarity Score: {similarity_percentage:.2f}% (Threshold: 90%)', y=1.05)
#     plt.tight_layout()
#     plt.show()

# def test_specific_pair(model, img_path1, img_path2):
#     device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
#     is_same, similarity, distance = test_single_pair(model, img_path1, img_path2, transform_val, device)
#     visualize_comparison(img_path1, img_path2, is_same, similarity)
    
#     print("\nTest Results:")
#     print(f"Distance: {distance:.4f}")
#     print(f"Similarity Score: {similarity * 100:.2f}%")
#     print(f"Threshold: 90%")
#     print(f"Model prediction: {'MATCH' if is_same else 'NO MATCH'}")

# def interactive_test():
#     # Set device
#     device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
#     print(f"Using device: {device}")
    
#     # Load model
#     model_path = 'models/best_model.pth'  # Ensure this path is correct
#     if not os.path.exists(model_path):
#         print(f"Error: Model not found at {model_path}")
#         return
    
#     model = SiameseNetwork().to(device)
#     model.load_state_dict(torch.load(model_path, map_location=device))
#     model.eval()
    
#     while True:
#         print("\nFingerprint Comparison Tool (90% threshold)")
        
#         # Get first image path
#         path1 = input("\nEnter path for first fingerprint image: ")
#         if path1.lower() == 'q':
#             print("Exiting...")
#             break
        
#         # Get second image path
#         path2 = input("Enter path for second fingerprint image: ")
#         if path2.lower() == 'q':
#             print("Exiting...")
#             break
        
#         try:
#             # Verify files exist
#             if not os.path.exists(path1):
#                 print(f"Error: File not found - {path1}")
#                 continue
#             if not os.path.exists(path2):
#                 print(f"Error: File not found - {path2}")
#                 continue
            
#             # Test the pair
#             print(f"\nComparing fingerprints...")
#             test_specific_pair(model, path1, path2)
        
#         except Exception as e:
#             print(f"Error: {str(e)}")
#             print("Please check the image paths and try again")
        
#         if input("\nTest another pair? (y/n): ").lower() != 'y':
#             print("Exiting...")
#             break

# if __name__ == "__main__":
#     interactive_test()


import os
import torch
import torch.nn.functional as F
from torchvision import transforms
from PIL import Image
import matplotlib.pyplot as plt

from src.model import SiameseNetwork
from src.utils import transform_val

# Constants
MARGIN = 2.0
THRESHOLD = 0.90
DATABASE_DIR = "data/finger"  # Fixed database directory

# Define finger types in order
FINGER_TYPES = [
    "left_thumb",
    "left_index",
    "left_middle",
    "left_ring",
    "left_pinky",
    "right_thumb",
    "right_index",
    "right_middle",
    "right_ring",
    "right_pinky"
]

def test_single_pair(model, img_path1, img_path2, transform, device, threshold=THRESHOLD):
    """Test a single pair of fingerprint images"""
    model.eval()
    
    try:
        # Load and preprocess images
        img1 = Image.open(img_path1).convert('L')
        img2 = Image.open(img_path2).convert('L')
        
        if transform:
            img1 = transform(img1)
            img2 = transform(img2)
        
        # Add batch dimension
        img1 = img1.unsqueeze(0).to(device)
        img2 = img2.unsqueeze(0).to(device)
        
        with torch.no_grad():
            output1, output2 = model(img1, img2)
            distance = F.pairwise_distance(output1, output2)
            similarity = 1 - (distance.item() / MARGIN)
            is_same = similarity >= threshold
        
        return is_same, similarity, distance.item()
    except Exception as e:
        print(f"Error comparing images: {e}")
        return False, 0.0, float('inf')

def visualize_comparison(img_path1, img_path2, is_same, similarity, finger_type):
    """Visualize the comparison between two fingerprint images"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5))
    
    img1 = Image.open(img_path1).convert('L')
    img2 = Image.open(img_path2).convert('L')
    
    ax1.imshow(img1, cmap='gray')
    ax1.set_title(f'Test Fingerprint\n({finger_type})')
    ax1.axis('off')
    
    ax2.imshow(img2, cmap='gray')
    ax2.set_title(f'Database Fingerprint\n({finger_type})')
    ax2.axis('off')
    
    result = "MATCH" if is_same else "NO MATCH"
    plt.suptitle(f'Result: {result}\nSimilarity: {similarity * 100:.2f}%', y=1.05)
    plt.tight_layout()
    plt.show()

def compare_with_database(model, test_dir, device):
    """Compare test fingerprints with all persons in database"""
    if not os.path.isdir(test_dir):
        raise ValueError(f"Test directory not found: {test_dir}")

    best_match = {
        'person_id': None,
        'total_matches': 0,
        'match_percentage': 0,
        'results': None,
        'fully_identified': False  # New field to track complete identification
    }

    # Get test fingerprint files
    test_files = sorted([f for f in os.listdir(test_dir) 
                        if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))])

    if len(test_files) != 10:
        raise ValueError(f"Expected 10 fingerprint images, found {len(test_files)}")

    # Get all person directories from database
    person_dirs = [d for d in os.listdir(DATABASE_DIR) 
                  if os.path.isdir(os.path.join(DATABASE_DIR, d))]

    print(f"\nComparing fingerprints with database...")

    for person_id in person_dirs:
        db_dir = os.path.join(DATABASE_DIR, person_id)
        results = []
        total_matches = 0

        # Get database fingerprint files
        db_files = sorted([f for f in os.listdir(db_dir) 
                         if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))])

        if len(db_files) != 10:
            print(f"Warning: Person {person_id} doesn't have 10 fingerprints, skipping...")
            continue

        # Compare corresponding fingerprints
        for test_file, db_file, finger_type in zip(test_files, db_files, FINGER_TYPES):
            test_path = os.path.join(test_dir, test_file)
            db_path = os.path.join(db_dir, db_file)
            
            # Compare fingerprints
            is_same, similarity, distance = test_single_pair(
                model, test_path, db_path, transform_val, device
            )
            
            results.append({
                'finger_type': finger_type,
                'is_match': is_same,
                'similarity': similarity,
                'test_path': test_path,
                'db_path': db_path
            })
            
            if is_same:
                total_matches += 1

        if results:
            match_percentage = (total_matches / len(results)) * 100
            # Check if all fingerprints match above threshold
            fully_identified = all(result['similarity'] >= THRESHOLD for result in results)
            
            if fully_identified:  # Changed to prioritize full identification
                best_match = {
                    'person_id': person_id,
                    'total_matches': total_matches,
                    'match_percentage': match_percentage,
                    'results': results,
                    'fully_identified': fully_identified
                }
                # Break early if we find a complete match
                break
            elif match_percentage > best_match['match_percentage']:
                best_match = {
                    'person_id': person_id,
                    'total_matches': total_matches,
                    'match_percentage': match_percentage,
                    'results': results,
                    'fully_identified': fully_identified
                }

    return best_match

def interactive_test():
    """Interactive tool for comparing fingerprints against the database"""
    # Device selection for Mac (prioritize MPS)
    if torch.backends.mps.is_available() and torch.backends.mps.is_built():
        device = torch.device("mps")
        print("Using MPS (Metal Performance Shaders) for M-series Mac")
    else:
        device = torch.device("cpu")
        print("MPS not available, falling back to CPU")
    
    print(f"Using device: {device}")
    
    # Load model
    model_path = os.path.join('models', 'new.pth')
    if not os.path.exists(model_path):
        print(f"Error: Model not found at {model_path}")
        return
    
    try:
        model = SiameseNetwork().to(device)
        state_dict = torch.load(model_path, map_location=device)
        model.load_state_dict(state_dict)
        model.eval()
    except Exception as e:
        print(f"Error loading model: {e}")
        return

    while True:
        print("\nFingerprint Verification System")
        print(f"Database Directory: {DATABASE_DIR}")
        print("Enter 'q' to quit")

        # Get test directory path
        test_dir = input("\nEnter path to test fingerprint directory: ").strip()
        if test_dir.lower() == 'q':
            print("Exiting...")
            break

        try:
            best_match = compare_with_database(model, test_dir, device)
            
            if best_match['person_id'] is None:
                print("\nNO MATCH FOUND IN DATABASE")
                continue
            
            # Display results
            if best_match['fully_identified']:
                print("\n" + "="*50)
                print("🎯 POSITIVE IDENTIFICATION")
                print("="*50)
                print(f"✅ PERSON IDENTIFIED AS ID: {best_match['person_id']}")
                print(f"✅ All 10 fingerprints matched above 90% threshold")
                print(f"✅ Overall Match Percentage: {best_match['match_percentage']:.2f}%")
                print("="*50)
            else:
                print("\n" + "="*50)
                print("❌ NO POSITIVE IDENTIFICATION")
                print("="*50)
                print(f"Best partial match found: Person {best_match['person_id']}")
                print(f"Overall Match Percentage: {best_match['match_percentage']:.2f}%")
                print(f"Matched Fingerprints: {best_match['total_matches']}/10")
                print("Not all fingerprints matched above 90% threshold")
                print("="*50)
            
            # Display individual finger results
            print("\nDetailed Fingerprint Results:")
            for result in best_match['results']:
                print(f"\n{result['finger_type'].upper()}:")
                print(f"Similarity: {result['similarity'] * 100:.2f}%")
                print(f"Status: {'MATCH ✓' if result['is_match'] else 'NO MATCH ✗'}")
                
                # Visualize the comparison
                visualize_comparison(
                    result['test_path'],
                    result['db_path'],
                    result['is_match'],
                    result['similarity'],
                    result['finger_type']
                )
                
        except Exception as e:
            print(f"Error during verification: {str(e)}")

        if input("\nTest another set? (y/n): ").strip().lower() != 'y':
            print("Exiting...")
            break

if __name__ == "__main__":
    interactive_test()