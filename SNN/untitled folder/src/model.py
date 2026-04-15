# __all__ = ['SiameseNetwork', 'ContrastiveLoss']

# print("Starting model.py import")

# try:
#     import torch
#     import torch.nn as nn
#     import torch.nn.functional as F
#     print("Successfully imported torch modules")
# except Exception as e:
#     print(f"Error importing torch: {e}")

# print("Defining SiameseNetwork class...")

# class SiameseNetwork(nn.Module):
#     def __init__(self):
#         super(SiameseNetwork, self).__init__()
        
#         # Feature extractor layers
#         self.feature_extractor = nn.Sequential(
#             nn.Conv2d(1, 64, kernel_size=3, padding=1),
#             nn.BatchNorm2d(64),
#             nn.ReLU(inplace=True),
#             nn.MaxPool2d(2),
            
#             nn.Conv2d(64, 128, kernel_size=3, padding=1),
#             nn.BatchNorm2d(128),
#             nn.ReLU(inplace=True),
#             nn.MaxPool2d(2),
            
#             nn.Conv2d(128, 256, kernel_size=3, padding=1),
#             nn.BatchNorm2d(256),
#             nn.ReLU(inplace=True),
#             nn.MaxPool2d(2),
            
#             nn.Conv2d(256, 512, kernel_size=3, padding=1),
#             nn.BatchNorm2d(512),
#             nn.ReLU(inplace=True),
#             nn.AdaptiveAvgPool2d((8, 8))
#         )
        
#         # Fully connected layers
#         self.fc = nn.Sequential(
#             nn.Linear(512 * 8 * 8, 1024),
#             nn.ReLU(inplace=True),
#             nn.Dropout(0.5),
#             nn.Linear(1024, 256),
#             nn.BatchNorm1d(256)
#         )
    
#     def forward_one(self, x):
#         x = self.feature_extractor(x)
#         x = x.view(x.size(0), -1)
#         x = self.fc(x)
#         x = F.normalize(x, p=2, dim=1)  # L2 normalization
#         return x
    
#     def forward(self, input1, input2):
#         output1 = self.forward_one(input1)
#         output2 = self.forward_one(input2)
#         return output1, output2

# class ContrastiveLoss(nn.Module):
#     def __init__(self, margin=2.0):
#         super(ContrastiveLoss, self).__init__()
#         self.margin = margin
    
#     def forward(self, output1, output2, label):
#         euclidean_distance = F.pairwise_distance(output1, output2)
#         # Contrastive loss formula
#         loss_contrastive = torch.mean(
#             (1 - label) * torch.pow(euclidean_distance, 2) +
#             label * torch.pow(torch.clamp(self.margin - euclidean_distance, min=0.0), 2)
#         )
#         return loss_contrastive

# print("Finished loading model.py")


__all__ = ['SiameseNetwork', 'ContrastiveLoss']

# Informational print statements
print("Starting model.py import")

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    print("Successfully imported torch modules")
except ImportError as e:
    print(f"Error importing torch modules: {e}")
    raise

print("Defining SiameseNetwork class...")



class MiniatureCNN(nn.Module):
    """
    A miniature CNN feature extractor optimized for fingerprint features
    """
    def __init__(self):
        super(MiniatureCNN, self).__init__()
        
        # Use float32 for better compatibility with MPS
        self.to(torch.float32)
        
        # First convolutional block - extract basic features
        self.conv1 = nn.Sequential(
            nn.Conv2d(1, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.Conv2d(32, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2)
        )
        
        # Second convolutional block - extract intermediate features
        self.conv2 = nn.Sequential(
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2)
        )
        
        # Third convolutional block - extract advanced features
        self.conv3 = nn.Sequential(
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.Conv2d(128, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2)
        )

        # Feature refinement with attention
        self.attention = nn.Sequential(
            nn.Conv2d(128, 1, kernel_size=1),
            nn.Sigmoid()
        )
        
        # Global pooling and feature embedding
        self.global_pool = nn.AdaptiveAvgPool2d((4, 4))
        
        # Dense layers for final embedding
        self.fc = nn.Sequential(
            nn.Linear(128 * 4 * 4, 512),
            nn.ReLU(inplace=True),
            nn.Dropout(0.5),
            nn.Linear(512, 128)
        )

    def forward(self, x):
        # Ensure input is float32
        x = x.to(torch.float32)
        
        # Extract hierarchical features
        x = self.conv1(x)
        x = self.conv2(x)
        x = self.conv3(x)
        
        # Apply attention mechanism
        attention_weights = self.attention(x)
        x = x * attention_weights
        
        # Global pooling
        x = self.global_pool(x)
        
        # Flatten and get embedding
        x = x.view(x.size(0), -1)
        x = self.fc(x)
        
        # L2 normalize the embeddings
        x = F.normalize(x, p=2, dim=1)
        return x

class SiameseNetwork(nn.Module):
    """
    Siamese Network using the MiniatureCNN as feature extractor
    """
    def __init__(self):
        super(SiameseNetwork, self).__init__()
        self.feature_extractor = MiniatureCNN()
    
    def forward(self, input1, input2):
        """
        Forward pass for a pair of inputs
        """
        output1 = self.feature_extractor(input1)
        output2 = self.feature_extractor(input2)
        return output1, output2

class ContrastiveLoss(nn.Module):
    """
    Contrastive Loss with margin adjustment and temperature scaling
    """
    def __init__(self, margin=2.0, temperature=0.5):
        super(ContrastiveLoss, self).__init__()
        self.margin = margin
        self.temperature = temperature
    
    def forward(self, output1, output2, label):
        # Calculate temperature-scaled distances
        euclidean_distance = F.pairwise_distance(output1, output2)
        scaled_distance = euclidean_distance / self.temperature
        
        # Compute contrastive loss with margin
        loss_contrastive = torch.mean(
            (1 - label) * torch.pow(scaled_distance, 2) +
            label * torch.pow(torch.clamp(self.margin - scaled_distance, min=0.0), 2)
        )
        return loss_contrastive

print("Finished loading model.py")