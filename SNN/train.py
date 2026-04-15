import os
import sys
import random
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader
from torchvision import transforms
from sklearn.model_selection import train_test_split
from tqdm import tqdm
from torch.cuda.amp import GradScaler, autocast  # For mixed precision training

# Add the 'src' folder to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, 'src'))

# Import custom modules
from src.model import SiameseNetwork, ContrastiveLoss
from src.dataset import FingerprintDataset, create_balanced_pairs, split_dataset
from src.utils import transform_train, transform_val, visualize_pairs, plot_metrics

# Constants
BATCH_SIZE = 64
EPOCHS = 50
LEARNING_RATE = 0.001
WEIGHT_DECAY = 1e-5
PATIENCE = 20
MARGIN = 2.0
TEMPERATURE = 0.5

# Train one epoch
def train_epoch(model, train_loader, criterion, optimizer, scaler, device):
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0

    pbar = tqdm(train_loader, desc="Training")
    for img1, img2, label in pbar:
        img1, img2, label = img1.to(device), img2.to(device), label.to(device)
        
        # Zero gradients
        optimizer.zero_grad()
        
        # Mixed precision training
        with autocast():
            output1, output2 = model(img1, img2)
            loss = criterion(output1, output2, label)
        
        # Backward pass with gradient scaling
        scaler.scale(loss).backward()
        
        # Gradient clipping
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        
        scaler.step(optimizer)
        scaler.update()
        
        running_loss += loss.item()
        
        # Calculate accuracy with temperature scaling
        distance = F.pairwise_distance(output1, output2)
        pred = (distance > MARGIN / 2).float()
        correct += (pred == label.squeeze()).sum().item()
        total += label.size(0)
        
        # Update progress bar
        pbar.set_postfix({
            "loss": f"{loss.item():.4f}",
            "acc": f"{100 * correct / total:.2f}%"
        })

    return running_loss / len(train_loader), 100 * correct / total

# Evaluate the model
def evaluate(model, val_loader, criterion, device):
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0

    with torch.no_grad():
        for img1, img2, label in val_loader:
            img1, img2, label = img1.to(device), img2.to(device), label.to(device)
            output1, output2 = model(img1, img2)
            loss = criterion(output1, output2, label)

            running_loss += loss.item()

            distance = F.pairwise_distance(output1, output2)
            pred = (distance > MARGIN / 2).float()
            correct += (pred == label.squeeze()).sum().item()
            total += label.size(0)

    return running_loss / len(val_loader), 100 * correct / total

# Main function
def main():
    # Set random seeds for reproducibility
    torch.manual_seed(42)
    random.seed(42)
    np.random.seed(42)

    # Check if MPS is available and set device
    if torch.backends.mps.is_available():
        device = torch.device("mps")
        print("Using MPS (Metal Performance Shaders)")
    else:
        device = torch.device("cpu")
        print("MPS not available, using CPU")
    
    print(f"Using device: {device}")

    # Dataset Path
    base_path = '/Users/niloyshowrav/Downloads/SNN/data/fingerprints'

    # Validate dataset files
    image_paths = [os.path.join(base_path, f) for f in os.listdir(base_path)
                   if f.endswith(('.png', '.jpg', '.jpeg', '.tif', '.BMP'))]
    if len(image_paths) == 0:
        print("No image files found in the dataset directory.")
        return

    # Labels and splitting
    labels = [os.path.basename(path).split('_')[0] for path in image_paths]

    # Split dataset into train, validation, and test sets
    (train_paths, train_labels), (val_paths, val_labels), (test_paths, test_labels) = \
        split_dataset(image_paths, labels)

    # Create balanced pairs for training and validation
    train_pairs, train_pair_labels = create_balanced_pairs(
        train_paths, 
        train_labels,
        num_pairs_per_class=1000,
        min_pairs_per_class=50
    )
    
    val_pairs, val_pair_labels = create_balanced_pairs(
        val_paths, 
        val_labels,
        num_pairs_per_class=200,
        min_pairs_per_class=20
    )

    # Create datasets
    train_dataset = FingerprintDataset(train_pairs, train_pair_labels, transform=transform_train)
    val_dataset = FingerprintDataset(val_pairs, val_pair_labels, transform=transform_val)

    # Create data loaders with num_workers for parallel loading
    train_loader = DataLoader(
        train_dataset,
        batch_size=BATCH_SIZE,
        shuffle=True,
        num_workers=4,
        pin_memory=True
    )
    
    val_loader = DataLoader(
        val_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=4,
        pin_memory=True
    )

    # Initialize model and training components
    model = SiameseNetwork().to(device)
    criterion = ContrastiveLoss(margin=MARGIN, temperature=TEMPERATURE)
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=LEARNING_RATE,
        weight_decay=WEIGHT_DECAY,
        betas=(0.9, 0.999)
    )
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer,
        mode='min',
        factor=0.5,
        patience=5,
        verbose=True
    )
    scaler = GradScaler()

    # Training loop
    best_val_acc = 0
    patience_counter = 0
    train_losses, val_losses = [], []
    train_accs, val_accs = [], []

    for epoch in range(EPOCHS):
        print(f"\nEpoch {epoch + 1}/{EPOCHS}")

        try:
            train_loss, train_acc = train_epoch(model, train_loader, criterion, optimizer, scaler, device)
            val_loss, val_acc = evaluate(model, val_loader, criterion, device)

            train_losses.append(train_loss)
            val_losses.append(val_loss)
            train_accs.append(train_acc)
            val_accs.append(val_acc)

            print(f"Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.2f}%")
            print(f"Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.2f}%")

            scheduler.step(val_loss)

            if val_acc > best_val_acc:
                best_val_acc = val_acc
                model_save_path = "models/new.pth"
                torch.save(model.state_dict(), model_save_path)
                print(f"New best model saved: {model_save_path}")
                patience_counter = 0
            else:
                patience_counter += 1

            if patience_counter >= PATIENCE:
                print(f"Early stopping triggered after {epoch + 1} epochs.")
                break

        except Exception as e:
            print(f"Error occurred during epoch {epoch + 1}: {e}")
            break

    print(f"\nBest validation accuracy: {best_val_acc:.2f}%")
    plot_metrics(train_losses, val_losses, train_accs, val_accs)


if __name__ == "__main__":
    os.makedirs('models', exist_ok=True)
    main()
