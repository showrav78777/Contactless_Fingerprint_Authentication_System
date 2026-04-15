# import torch
# from torch.utils.data import Dataset
# from PIL import Image
# import os
# import random
# from itertools import combinations

# class FingerprintDataset(Dataset):
#     def __init__(self, fingerprint_pairs, labels, transform=None):
#         self.fingerprint_pairs = fingerprint_pairs
#         self.labels = labels
#         self.transform = transform
    
#     def __len__(self):
#         return len(self.labels)
    
#     def __getitem__(self, idx):
#         img1_path, img2_path = self.fingerprint_pairs[idx]
        
#         try:
#             img1 = Image.open(img1_path).convert('L')
#             img2 = Image.open(img2_path).convert('L')
#         except Exception as e:
#             print(f"Error loading images: {e}")
#             return None  # Or handle this case based on your requirements
        
#         if self.transform:
#             img1 = self.transform(img1)
#             img2 = self.transform(img2)
        
#         return img1, img2, torch.FloatTensor([self.labels[idx]])

# def create_balanced_pairs(image_paths, labels, num_pairs_per_class=1000):
#     pairs = []
#     pair_labels = []
#     label_dict = {}
    
#     # Group images by labels
#     for idx, label in enumerate(labels):
#         label_dict.setdefault(label, []).append(image_paths[idx])
    
#     # Generate balanced positive and negative pairs
#     for label, images in label_dict.items():
#         # Positive pairs (same class)
#         pos_pairs = list(combinations(images, 2))
#         if len(pos_pairs) > num_pairs_per_class:
#             pos_pairs = random.sample(pos_pairs, num_pairs_per_class)
#         pairs.extend(pos_pairs)
#         pair_labels.extend([0] * len(pos_pairs))  # Label 0 for positive pairs
        
#         # Negative pairs (different classes)
#         neg_pairs = []
#         other_labels = [l for l in label_dict.keys() if l != label]
#         while len(neg_pairs) < len(pos_pairs):
#             other_label = random.choice(other_labels)
#             img1 = random.choice(images)
#             img2 = random.choice(label_dict[other_label])
#             neg_pairs.append((img1, img2))
#         pairs.extend(neg_pairs)
#         pair_labels.extend([1] * len(neg_pairs))  # Label 1 for negative pairs
    
#     # Shuffle pairs to ensure random distribution of positive and negative pairs
#     combined = list(zip(pairs, pair_labels))
#     random.shuffle(combined)
#     pairs, pair_labels = zip(*combined)
    
#     return pairs, list(pair_labels)


import torch
from torch.utils.data import Dataset
from PIL import Image
import os
import random
from itertools import combinations
import numpy as np
from torchvision import transforms


class FingerprintDataset(Dataset):
    """
    Custom Dataset for fingerprint images with class labels
    """
    def __init__(self, fingerprint_pairs, labels, transform=None):
        self.fingerprint_pairs = fingerprint_pairs
        self.labels = labels
        self.transform = transform
        
        # Verify data consistency
        assert len(fingerprint_pairs) == len(labels), "Pairs and labels must have same length"
    
    def __len__(self):
        return len(self.labels)
    
    def __getitem__(self, idx):
        img1_path, img2_path = self.fingerprint_pairs[idx]
        
        try:
            # Load and preprocess fingerprint images
            img1 = Image.open(img1_path).convert('L')
            img2 = Image.open(img2_path).convert('L')
            
            # Apply image enhancement for fingerprints
            img1 = self.enhance_fingerprint(img1)
            img2 = self.enhance_fingerprint(img2)
            
            if self.transform:
                img1 = self.transform(img1)
                img2 = self.transform(img2)
            
            # Ensure tensors are float32 for MPS compatibility
            img1 = img1.to(torch.float32)
            img2 = img2.to(torch.float32)
            
            return img1, img2, torch.tensor(self.labels[idx], dtype=torch.float32)
            
        except Exception as e:
            raise RuntimeError(f"Error loading fingerprint images: {e}\nPaths: {img1_path}, {img2_path}")
    
    @staticmethod
    def enhance_fingerprint(img):
        """
        Enhance fingerprint image quality
        """
        # Convert to numpy array
        img_array = np.array(img)
        
        # Apply contrast enhancement
        p2, p98 = np.percentile(img_array, (2, 98))
        img_array = np.clip(img_array, p2, p98)
        
        # Normalize to 0-255 range
        img_array = ((img_array - p2) / (p98 - p2) * 255).astype(np.uint8)
        
        # Convert back to PIL Image
        return Image.fromarray(img_array)

def create_balanced_pairs(image_paths, labels, num_pairs_per_class=1000, min_pairs_per_class=50):
    """
    Creates balanced pairs of fingerprint images for training
    
    Args:
        image_paths: List of paths to fingerprint images
        labels: List of corresponding labels
        num_pairs_per_class: Maximum number of pairs per class
        min_pairs_per_class: Minimum number of pairs per class
    """
    # Group images by label (fingerprint class)
    label_to_images = {}
    for path, label in zip(image_paths, labels):
        label_to_images.setdefault(label, []).append(path)
    
    pairs = []
    pair_labels = []
    
    # Generate positive pairs (same fingerprint class)
    for label, images in label_to_images.items():
        # Create all possible positive pairs
        pos_pairs = list(combinations(images, 2))
        
        # Ensure minimum number of pairs
        if len(pos_pairs) < min_pairs_per_class:
            # If not enough natural pairs, create augmented pairs
            while len(pos_pairs) < min_pairs_per_class:
                img = random.choice(images)
                other_img = random.choice(images)
                pos_pairs.append((img, other_img))
        
        # Limit maximum number of pairs
        if len(pos_pairs) > num_pairs_per_class:
            pos_pairs = random.sample(pos_pairs, num_pairs_per_class)
        
        pairs.extend(pos_pairs)
        pair_labels.extend([0] * len(pos_pairs))  # 0 for positive pairs
        
        # Generate negative pairs (different fingerprint classes)
        neg_pairs = []
        other_labels = [l for l in label_to_images if l != label]
        
        while len(neg_pairs) < len(pos_pairs):
            other_label = random.choice(other_labels)
            img1 = random.choice(images)
            img2 = random.choice(label_to_images[other_label])
            neg_pairs.append((img1, img2))
        
        pairs.extend(neg_pairs)
        pair_labels.extend([1] * len(neg_pairs))  # 1 for negative pairs
    
    # Shuffle pairs and labels together
    combined = list(zip(pairs, pair_labels))
    random.shuffle(combined)
    pairs, pair_labels = zip(*combined)
    
    return list(pairs), list(pair_labels)

def split_dataset(image_paths, labels, test_size=0.2, val_size=0.2, random_state=42):
    """
    Split dataset into train, validation, and test sets while preserving class distribution
    """
    from sklearn.model_selection import train_test_split
    
    # First split: separate test set
    train_val_paths, test_paths, train_val_labels, test_labels = train_test_split(
        image_paths, labels,
        test_size=test_size,
        stratify=labels,
        random_state=random_state
    )
    
    # Second split: separate validation set from training set
    train_paths, val_paths, train_labels, val_labels = train_test_split(
        train_val_paths,
        train_val_labels,
        test_size=val_size,
        stratify=train_val_labels,
        random_state=random_state
    )
    
    return (train_paths, train_labels), (val_paths, val_labels), (test_paths, test_labels)