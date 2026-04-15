import os
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
import torchvision.transforms as transforms
from tqdm import tqdm
import numpy as np
from src.enhanced_model import EnhancedFingerprintNetwork, EnhancedContrastiveLoss
from src.fingerprint_dataset import FingerprintDataset

def train_model(model, train_loader, criterion, optimizer, device, num_epochs=50):
    model.train()
    best_loss = float('inf')
    
    for epoch in range(num_epochs):
        running_loss = 0.0
        progress_bar = tqdm(train_loader, desc=f'Epoch {epoch+1}/{num_epochs}')
        
        for gabor1, skeleton1, minutiae1, gabor2, skeleton2, minutiae2, labels in progress_bar:
            # Move data to device
            gabor1 = gabor1.to(device)
            skeleton1 = skeleton1.to(device)
            minutiae1 = minutiae1.to(device)
            gabor2 = gabor2.to(device)
            skeleton2 = skeleton2.to(device)
            minutiae2 = minutiae2.to(device)
            labels = labels.to(device)
            
            # Zero the parameter gradients
            optimizer.zero_grad()
            
            # Forward pass
            output1, output2 = model(gabor1, skeleton1, minutiae1, gabor2, skeleton2, minutiae2)
            
            # Calculate loss
            loss = criterion(output1, output2, labels)
            
            # Backward pass and optimize
            loss.backward()
            optimizer.step()
            
            # Update statistics
            running_loss += loss.item()
            progress_bar.set_postfix({'loss': loss.item()})
        
        # Calculate epoch statistics
        epoch_loss = running_loss / len(train_loader)
        print(f'Epoch {epoch+1}/{num_epochs}, Loss: {epoch_loss:.4f}')
        
        # Save best model
        if epoch_loss < best_loss:
            best_loss = epoch_loss
            torch.save(model.state_dict(), 'models/enhanced_model.pth')
            print(f'Model saved with loss: {best_loss:.4f}')

def main():
    # Set device
    if torch.backends.mps.is_available() and torch.backends.mps.is_built():
        device = torch.device("mps")
        print("Using MPS (Metal Performance Shaders) for M-series Mac")
    else:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Using device: {device}")
    
    # Create output directory
    os.makedirs('models', exist_ok=True)
    
    # Define transforms
    transform = transforms.Compose([
        transforms.Resize((300, 300)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.5], std=[0.5])
    ])
    
    # Create dataset and dataloader
    dataset = FingerprintDataset(
        root_dir='data/processed_dataset',
        transform=transform,
        train=True
    )
    
    train_loader = DataLoader(
        dataset,
        batch_size=32,
        shuffle=True,
        num_workers=4
    )
    
    # Initialize model
    model = EnhancedFingerprintNetwork().to(device)
    criterion = EnhancedContrastiveLoss(margin=1.0)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.0001)
    
    # Train model
    train_model(model, train_loader, criterion, optimizer, device)
    
    print("Training completed!")

if __name__ == '__main__':
    main() 