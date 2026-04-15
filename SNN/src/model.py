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



class ResidualBlock(nn.Module):
    def __init__(self, in_channels, out_channels, stride=1):
        super(ResidualBlock, self).__init__()
        self.conv1 = nn.Conv2d(in_channels, out_channels, kernel_size=3, 
                              stride=stride, padding=1, bias=False)
        self.bn1 = nn.BatchNorm2d(out_channels)
        self.conv2 = nn.Conv2d(out_channels, out_channels, kernel_size=3,
                              stride=1, padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(out_channels)
        
        # Shortcut connection
        self.shortcut = nn.Sequential()
        if stride != 1 or in_channels != out_channels:
            self.shortcut = nn.Sequential(
                nn.Conv2d(in_channels, out_channels, kernel_size=1,
                         stride=stride, bias=False),
                nn.BatchNorm2d(out_channels)
            )

    def forward(self, x):
        out = F.relu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))
        out += self.shortcut(x)
        out = F.relu(out)
        return out

class EnhancedSiameseNetwork(nn.Module):
    def __init__(self):
        super(EnhancedSiameseNetwork, self).__init__()
        
        # Initial preprocessing layers
        self.preprocessing = nn.Sequential(
            nn.Conv2d(1, 32, kernel_size=7, stride=1, padding=3),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.MaxPool2d(2)
        )
        
        # Feature extraction layers with residual blocks
        self.feature_extractor = nn.Sequential(
            ResidualBlock(32, 64, stride=2),
            ResidualBlock(64, 64),
            ResidualBlock(64, 128, stride=2),
            ResidualBlock(128, 128),
            ResidualBlock(128, 256, stride=2),
            ResidualBlock(256, 256),
            nn.AdaptiveAvgPool2d((1, 1))  # Global average pooling
        )
        
        # Attention mechanism
        self.attention = nn.Sequential(
            nn.Conv2d(256, 1, kernel_size=1),
            nn.Sigmoid()
        )
        
        # Fully connected layers
        self.fc = nn.Sequential(
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(128, 64)
        )
        
    def forward_one(self, x):
        # Input normalization
        x = x / 255.0  # Normalize to [0,1]
        
        # Initial feature extraction
        x = self.preprocessing(x)
        
        # Deep feature extraction
        features = self.feature_extractor(x)
        
        # Apply attention
        attention_weights = self.attention(features)
        features = features * attention_weights
        
        # Flatten and pass through FC layers
        features = features.view(features.size(0), -1)
        features = self.fc(features)
        
        # L2 normalization
        features = F.normalize(features, p=2, dim=1)
        
        return features
    
    def forward(self, input1, input2):
        output1 = self.forward_one(input1)
        output2 = self.forward_one(input2)
        return output1, output2

# Custom loss function with margin
class ContrastiveLoss(nn.Module):
    def __init__(self, margin=1.0):
        super(ContrastiveLoss, self).__init__()
        self.margin = margin

    def forward(self, output1, output2, label):
        euclidean_distance = F.pairwise_distance(output1, output2)
        loss_contrastive = torch.mean((1-label) * torch.pow(euclidean_distance, 2) +
                                    label * torch.pow(torch.clamp(self.margin - euclidean_distance, min=0.0), 2))
        return loss_contrastive

print("Finished loading model.py")

# Initialize model
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = EnhancedSiameseNetwork().to(device)
criterion = ContrastiveLoss(margin=1.0)

# Define transforms for 300x300 images
transform = transforms.Compose([
    transforms.Resize((300, 300)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5], std=[0.5])
])

# Update your dataset class with the new transform
dataset = SiameseDataset(data_dir='path/to/data', transform=transform)

def train_model(model, train_loader, criterion, optimizer, num_epochs=50):
    model.train()
    for epoch in range(num_epochs):
        running_loss = 0.0
        for i, (img1, img2, label) in enumerate(train_loader):
            img1, img2, label = img1.to(device), img2.to(device), label.to(device)
            
            optimizer.zero_grad()
            output1, output2 = model(img1, img2)
            loss = criterion(output1, output2, label)
            
            loss.backward()
            optimizer.step()
            
            running_loss += loss.item()
            
        print(f'Epoch [{epoch+1}/{num_epochs}], Loss: {running_loss/len(train_loader):.4f}')