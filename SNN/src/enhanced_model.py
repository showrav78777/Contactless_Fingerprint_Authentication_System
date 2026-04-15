import torch
import torch.nn as nn
import torch.nn.functional as F

class RidgeAttention(nn.Module):
    def __init__(self, in_channels):
        super(RidgeAttention, self).__init__()
        self.conv1 = nn.Conv2d(in_channels, in_channels//8, 1)
        self.conv2 = nn.Conv2d(in_channels//8, in_channels, 1)
        self.bn = nn.BatchNorm2d(in_channels)
        
    def forward(self, x):
        # Channel attention
        avg_pool = F.adaptive_avg_pool2d(x, 1)
        max_pool = F.adaptive_max_pool2d(x, 1)
        
        avg_out = self.conv2(F.relu(self.conv1(avg_pool)))
        max_out = self.conv2(F.relu(self.conv1(max_pool)))
        
        out = torch.sigmoid(avg_out + max_out)
        return x * out

class RidgeFeatureExtractor(nn.Module):
    def __init__(self, in_channels):
        super(RidgeFeatureExtractor, self).__init__()
        
        self.conv_layers = nn.Sequential(
            nn.Conv2d(in_channels, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
            
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
            
            nn.Conv2d(128, 256, kernel_size=3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
            
            nn.Conv2d(256, 512, kernel_size=3, padding=1),
            nn.BatchNorm2d(512),
            nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool2d((1, 1))
        )
        
        self.attention = RidgeAttention(512)
        
    def forward(self, x):
        features = self.conv_layers(x)
        features = self.attention(features)
        return features.view(features.size(0), -1)

class EnhancedFingerprintNetwork(nn.Module):
    def __init__(self):
        super(EnhancedFingerprintNetwork, self).__init__()
        
        # Feature extractors for each type of fingerprint representation
        self.gabor_extractor = RidgeFeatureExtractor(1)  # Gabor filtered image
        self.skeleton_extractor = RidgeFeatureExtractor(1)  # Skeletonized image
        self.minutiae_extractor = RidgeFeatureExtractor(1)  # Minutiae points
        
        # Fusion layers
        self.fusion = nn.Sequential(
            nn.Linear(512 * 3, 1024),
            nn.ReLU(inplace=True),
            nn.Dropout(0.5),
            nn.Linear(1024, 512),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(512, 256)
        )
        
    def forward_one(self, gabor, skeleton, minutiae):
        # Extract features from each representation
        gabor_features = self.gabor_extractor(gabor)
        skeleton_features = self.skeleton_extractor(skeleton)
        minutiae_features = self.minutiae_extractor(minutiae)
        
        # Concatenate features
        combined_features = torch.cat([
            gabor_features,
            skeleton_features,
            minutiae_features
        ], dim=1)
        
        # Fuse features
        fused_features = self.fusion(combined_features)
        
        # L2 normalization
        return F.normalize(fused_features, p=2, dim=1)
    
    def forward(self, gabor1, skeleton1, minutiae1, gabor2, skeleton2, minutiae2):
        output1 = self.forward_one(gabor1, skeleton1, minutiae1)
        output2 = self.forward_one(gabor2, skeleton2, minutiae2)
        return output1, output2

class EnhancedContrastiveLoss(nn.Module):
    def __init__(self, margin=1.0):
        super(EnhancedContrastiveLoss, self).__init__()
        self.margin = margin
        
    def forward(self, output1, output2, label):
        # Euclidean distance
        euclidean_distance = F.pairwise_distance(output1, output2)
        
        # Cosine similarity
        cosine_similarity = F.cosine_similarity(output1, output2)
        
        # Combined loss
        distance_loss = torch.mean(
            (1 - label) * torch.pow(euclidean_distance, 2) +
            label * torch.pow(torch.clamp(self.margin - euclidean_distance, min=0.0), 2)
        )
        
        similarity_loss = torch.mean(
            (1 - label) * torch.pow(1 - cosine_similarity, 2) +
            label * torch.pow(cosine_similarity, 2)
        )
        
        return distance_loss + similarity_loss 