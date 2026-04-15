# import json
# import os
# import torch
# import torch.nn.functional as F
# from torchvision import transforms
# from PIL import Image
# import matplotlib.pyplot as plt
# from django.conf import settings

# from api.model import SiameseNetwork
# from api.utils import transform_val

# # Constants
# MARGIN = 2.0
# THRESHOLD = 0.90
# DATABASE_DIR = os.path.join(settings.MEDIA_ROOT, 'processed')
# model_path = os.path.join(settings.BASE_DIR, 'models', 'new.pth')
# device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")

# # Define finger types in order
# FINGER_TYPES = [
#     "left_thumb",
#     "left_index",
#     "left_middle",
#     "left_ring",
#     "left_pinky",
#     "right_thumb",
#     "right_index",
#     "right_middle",
#     "right_ring",
#     "right_pinky"
# ]

# def test_single_pair(model, img_path1, img_path2, transform, device, threshold=THRESHOLD):
#     """Test a single pair of fingerprint images"""
#     model.eval()
    
#     try:
#         img1 = Image.open(img_path1).convert('L')
#         img2 = Image.open(img_path2).convert('L')
        
#         if transform:
#             img1 = transform(img1)
#             img2 = transform(img2)
        
#         img1 = img1.unsqueeze(0).to(device)
#         img2 = img2.unsqueeze(0).to(device)
        
#         with torch.no_grad():
#             output1, output2 = model(img1, img2)
#             distance = F.pairwise_distance(output1, output2)
#             print(distance)
#             similarity = 1 - (distance.item() / MARGIN)
#             is_same = similarity >= threshold
     
        
#         return is_same, similarity, distance.item()
#     except Exception as e:
#         print(f"Error comparing images: {e}")
#         return False, 0.0, float('inf')

# def compare_with_person_folder(model, login_dir, person_id, device):
#     """Compare login fingerprints with a specific person's folder"""
#     try:
#         person_dir = os.path.join(DATABASE_DIR, person_id)
#         print(f"Comparing with person directory: {person_dir}")

#         if not os.path.exists(person_dir):
#             print(f"Person directory not found: {person_dir}")
#             return {
#                 'person_id': person_id,
#                 'total_matches': 0,
#                 'match_percentage': 0,
#                 'similarity_scores': [],
#                 'fully_identified': False
#             }

#         # Get login fingerprint files
#         login_files = sorted([f for f in os.listdir(login_dir) 
#                             if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))])
        
#         print(f"Processing {len(login_files)} login files")

#         # Get database fingerprint files
#         db_files = sorted([f for f in os.listdir(person_dir) 
#                           if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))])

#         # Expect only 4 files for login
#         if len(db_files) < 4:
#             print(f"Person {person_id} has insufficient files: {len(db_files)}")
#             return {
#                 'person_id': person_id,
#                 'total_matches': 0,
#                 'match_percentage': 0,
#                 'similarity_scores': [],
#                 'fully_identified': False
#             }

#         matches = 0
#         similarities = []

#         # Compare each finger
#         for login_file, db_file in zip(login_files, db_files[:4]):  # Limit to 4 files
#             login_path = os.path.join(login_dir, login_file)
#             db_path = os.path.join(person_dir, db_file)
            
#             is_same, similarity, _ = test_single_pair(
#                 model, login_path, db_path, transform_val, device
#             )
            
#             similarities.append(similarity)
#             if is_same:
#                 matches += 1

#         match_percentage = (matches / 4) * 100  # Adjusted to 4 files
#         print(f"Match percentage for {person_id}: {match_percentage}%")

#         return {
#             'person_id': person_id,
#             'total_matches': matches,
#             'match_percentage': match_percentage,
#             'similarity_scores': similarities,
#             'fully_identified': match_percentage >= 90
#         }

#     except Exception as e:
#         print(f"Error in compare_with_person_folder: {str(e)}")
#         return {
#             'person_id': person_id,
#             'total_matches': 0,
#             'match_percentage': 0,
#             'similarity_scores': [],
#             'fully_identified': False
#         }

# def verify_login(request):
#     """Verify login by comparing fingerprints with specified person_id"""
#     try:
#         # Parse person_id from request
#         if not request.body:
#             return {
#                 'status': 'error',
#                 'message': 'No person_id provided'
#             }
#         data = json.loads(request.body)
#         person_id = data.get('person_id')
#         if not person_id:
#             return {
#                 'status': 'error',
#                 'message': 'Person ID is required'
#             }

#         login_dir = os.path.join(settings.MEDIA_ROOT, 'login')
#         if not os.path.exists(login_dir):
#             print(f"Login directory not found at: {login_dir}")
#             return {
#                 'status': 'error',
#                 'message': 'Login directory not found'
#             }

#         # Load model
#         print(f"Loading model from {model_path}")
#         model = SiameseNetwork()
#         model.load_state_dict(torch.load(model_path, map_location=device, weights_only=True))
#         model.to(device)
#         model.eval()
#         print("Model loaded successfully")
#         print()
#         # Compare with specific person folder
#         match_result = compare_with_person_folder(model, login_dir, person_id, device)

#         if match_result['fully_identified']:
#             print(f"User fully identified: {person_id}")
#             return {
#                 'status': 'success',
#                 'message': 'Login successful',
#                 'person_id': person_id,
#                 'match_percentage': f"{match_result['match_percentage']:.2f}%",
#                 'fully_identified': True
                
#             }
#         elif match_result['match_percentage'] > 70:
#             print(f"Partial match for {person_id}")
#             return {
#                 'status': 'partial_match',
#                 'message': 'Partial match found',
#                 'person_id': person_id,
#                 'match_percentage': f"{match_result['match_percentage']:.2f}%",
#                 'fully_identified': False
#             }
#         else:
#             print(f"No sufficient match for {person_id}")
#             return {
#                 'status': 'failed',
#                 'message': 'Login failed - fingerprints do not match',
#                 'person_id': person_id,
#                 'match_percentage': f"{match_result['match_percentage']:.2f}%"
#             }

#     except Exception as e:
#         print(f"Error in verify_login: {str(e)}")
#         import traceback
#         traceback.print_exc()
#         return {
#             'status': 'error',
#             'message': f'Verification failed: {str(e)}'
#         }

# def compare_fingerprints(model, img_path1, img_path2):
#     """Compare two fingerprint images and return similarity score"""
#     is_same, similarity, _ = test_single_pair(model, img_path1, img_path2, transform_val, device)
#     return similarity

import json
import os
import torch
import torch.nn.functional as F
from torchvision import transforms
from PIL import Image
import matplotlib.pyplot as plt
from django.conf import settings

from api.model import SiameseNetwork
from api.utils import transform_val

# Constants
MARGIN = 2.0
THRESHOLD = 0.84
DATABASE_DIR = os.path.join(settings.MEDIA_ROOT, 'processed')
model_path = os.path.join(settings.BASE_DIR, 'models', 'new.pth')
device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")

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
        img1 = Image.open(img_path1).convert('L')
        img2 = Image.open(img_path2).convert('L')
        
        if transform:
            img1 = transform(img1)
            img2 = transform(img2)
        
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

def compare_with_person_folder(model, login_dir, person_id, device):
    """Compare login fingerprints with a specific person's folder"""
    try:
        person_dir = os.path.join(DATABASE_DIR, person_id)
        print(f"Comparing with person directory: {person_dir}")

        if not os.path.exists(person_dir):
            print(f"Person directory not found: {person_dir}")
            return {
                'person_id': person_id,
                'total_matches': 0,
                'match_percentage': 0,
                'actual_ratio': "0/0",
                'similarity_scores': [],
                'fully_identified': False
            }

        # Get login fingerprint files
        login_files = sorted([f for f in os.listdir(login_dir) 
                            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))])
        
        # Get database fingerprint files
        db_files = sorted([f for f in os.listdir(person_dir) 
                          if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))])

        # Expect 10 files for both login and database
        if len(db_files) != 10:
            print(f"Person {person_id} has incorrect number of files: {len(db_files)}")
            return {
                'person_id': person_id,
                'total_matches': 0,
                'match_percentage': 0,
                'actual_ratio': f"0/{len(db_files)}",
                'similarity_scores': [],
                'fully_identified': False
            }

        if len(login_files) != 10:
            print(f"Login directory has incorrect number of files: {len(login_files)}")
            return {
                'person_id': person_id,
                'total_matches': 0,
                'match_percentage': 0,
                'actual_ratio': f"0/{len(login_files)}",
                'similarity_scores': [],
                'fully_identified': False
            }

        print(f"Processing {len(login_files)} login files against {len(db_files)} database files")

        matches = 0
        similarities = []

        # Compare each finger in order
        for finger_idx, (login_file, db_file) in enumerate(zip(login_files, db_files)):
            login_path = os.path.join(login_dir, login_file)
            db_path = os.path.join(person_dir, db_file)
            
            is_same, similarity, _ = test_single_pair(
                model, login_path, db_path, transform_val, device
            )
            
            similarities.append(similarity)
            if is_same:
                matches += 1

        match_percentage = (matches / 10) * 100
        actual_ratio = f"{matches}/10"
        print(f"Match percentage for {person_id}: {match_percentage}% ({actual_ratio})")

        return {
            'person_id': person_id,
            'total_matches': matches,
            'match_percentage': match_percentage,
            'actual_ratio': actual_ratio,
            'similarity_scores': similarities,
            'fully_identified': match_percentage >= 90
        }

    except Exception as e:
        print(f"Error in compare_with_person_folder: {str(e)}")
        return {
            'person_id': person_id,
            'total_matches': 0,
            'match_percentage': 0,
            'actual_ratio': "0/0",
            'similarity_scores': [],
            'fully_identified': False
        }

def verify_login(request):
    """Verify login by comparing fingerprints with specified person_id"""
    try:
        # Parse person_id from request
        if not request.body:
            return {
                'status': 'error',
                'message': 'No person_id provided'
            }
        data = json.loads(request.body)
        person_id = data.get('person_id')
        if not person_id:
            return {
                'status': 'error',
                'message': 'Person ID is required'
            }

        login_dir = os.path.join(settings.MEDIA_ROOT, 'login')
        if not os.path.exists(login_dir):
            print(f"Login directory not found at: {login_dir}")
            return {
                'status': 'error',
                'message': 'Login directory not found'
            }

        # Load model
        print(f"Loading model from {model_path}")
        model = SiameseNetwork()
        model.load_state_dict(torch.load(model_path, map_location=device, weights_only=True))
        model.to(device)
        model.eval()
        print("Model loaded successfully")
        print()
        # Compare with specific person folder
        match_result = compare_with_person_folder(model, login_dir, person_id, device)

        if match_result['fully_identified']:
            print(f"User fully identified: {person_id}")
            return {
                'status': 'success',
                'message': 'Login successful',
                'person_id': person_id,
                'match_percentage': f"{match_result['match_percentage']:.2f}%",
                'actual_ratio': match_result['actual_ratio'],
                'fully_identified': True
            }
        elif match_result['match_percentage'] > 70:
            print(f"Partial match for {person_id}")
            return {
                'status': 'partial_match',
                'message': 'Partial match found',
                'person_id': person_id,
                'match_percentage': f"{match_result['match_percentage']:.2f}%",
                'actual_ratio': match_result['actual_ratio'],
                'fully_identified': False
            }
        else:
            print(f"No sufficient match for {person_id}")
            return {
                'status': 'failed',
                'message': 'Login failed - fingerprints do not match',
                'person_id': person_id,
                'match_percentage': f"{match_result['match_percentage']:.2f}%",
                'actual_ratio': match_result['actual_ratio']
            }

    except Exception as e:
        print(f"Error in verify_login: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'status': 'error',
            'message': f'Verification failed: {str(e)}'
        }

def compare_fingerprints(model, img_path1, img_path2):
    """Compare two fingerprint images and return similarity score"""
    is_same, similarity, _ = test_single_pair(model, img_path1, img_path2, transform_val, device)
    return similarity