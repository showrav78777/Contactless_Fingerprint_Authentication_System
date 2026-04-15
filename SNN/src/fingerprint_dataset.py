import os
import torch
from torch.utils.data import Dataset
from PIL import Image
import torchvision.transforms as transforms
import random
import numpy as np

class FingerprintDataset(Dataset):
    def __init__(self, root_dir, transform=None, train=True):
        """
        Args:
            root_dir (string): Directory with all the preprocessed fingerprint images.
            transform (callable, optional): Optional transform to be applied on a sample.
            train (bool): If True, creates dataset from training set, otherwise from test set.
        """
        self.root_dir = root_dir
        self.transform = transform
        self.train = train
        
        # Get all person directories
        self.person_dirs = [d for d in os.listdir(root_dir) if os.path.isdir(os.path.join(root_dir, d))]
        
        # Create pairs of images
        self.pairs = []
        self.labels = []
        
        # For each person, create positive pairs (same person)
        for person_id in self.person_dirs:
            person_dir = os.path.join(root_dir, person_id)
            
            # Get all images for this person
            gabor_dir = os.path.join(person_dir, 'gabor')
            skeleton_dir = os.path.join(person_dir, 'skeleton')
            minutiae_dir = os.path.join(person_dir, 'minutiae')
            
            image_files = [f for f in os.listdir(gabor_dir) if f.endswith('.png')]
            
            # Create positive pairs
            for i in range(len(image_files)):
                for j in range(i + 1, len(image_files)):
                    self.pairs.append((
                        os.path.join(gabor_dir, image_files[i]),
                        os.path.join(skeleton_dir, image_files[i]),
                        os.path.join(minutiae_dir, image_files[i]),
                        os.path.join(gabor_dir, image_files[j]),
                        os.path.join(skeleton_dir, image_files[j]),
                        os.path.join(minutiae_dir, image_files[j])
                    ))
                    self.labels.append(1.0)
        
        # Create negative pairs (different persons)
        num_negative_pairs = len(self.pairs)  # Balance positive and negative pairs
        for _ in range(num_negative_pairs):
            # Randomly select two different persons
            person1, person2 = random.sample(self.person_dirs, 2)
            
            # Get random images from each person
            person1_dir = os.path.join(root_dir, person1)
            person2_dir = os.path.join(root_dir, person2)
            
            img1 = random.choice([f for f in os.listdir(os.path.join(person1_dir, 'gabor')) if f.endswith('.png')])
            img2 = random.choice([f for f in os.listdir(os.path.join(person2_dir, 'gabor')) if f.endswith('.png')])
            
            self.pairs.append((
                os.path.join(person1_dir, 'gabor', img1),
                os.path.join(person1_dir, 'skeleton', img1),
                os.path.join(person1_dir, 'minutiae', img1),
                os.path.join(person2_dir, 'gabor', img2),
                os.path.join(person2_dir, 'skeleton', img2),
                os.path.join(person2_dir, 'minutiae', img2)
            ))
            self.labels.append(0.0)
    
    def __len__(self):
        return len(self.pairs)
    
    def __getitem__(self, idx):
        gabor1_path, skeleton1_path, minutiae1_path, gabor2_path, skeleton2_path, minutiae2_path = self.pairs[idx]
        label = self.labels[idx]
        
        # Load images
        gabor1 = Image.open(gabor1_path).convert('L')
        skeleton1 = Image.open(skeleton1_path).convert('L')
        minutiae1 = Image.open(minutiae1_path).convert('L')
        
        gabor2 = Image.open(gabor2_path).convert('L')
        skeleton2 = Image.open(skeleton2_path).convert('L')
        minutiae2 = Image.open(minutiae2_path).convert('L')
        
        # Apply transforms
        if self.transform:
            gabor1 = self.transform(gabor1)
            skeleton1 = self.transform(skeleton1)
            minutiae1 = self.transform(minutiae1)
            
            gabor2 = self.transform(gabor2)
            skeleton2 = self.transform(skeleton2)
            minutiae2 = self.transform(minutiae2)
        
        return gabor1, skeleton1, minutiae1, gabor2, skeleton2, minutiae2, torch.FloatTensor([label]) 