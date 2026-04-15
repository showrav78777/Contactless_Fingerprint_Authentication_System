import sys
import os
# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
import numpy as np
from sklearn.metrics import confusion_matrix, roc_curve, auc, f1_score
import matplotlib.pyplot as plt
from model import SiameseNetwork
from utils import transform_val
from dataset import SiameseDataset

def evaluate_model(model_path, test_dataset_path, device):
    # Load the model
    model = SiameseNetwork().to(device)
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.eval()

    # Create test dataset and dataloader
    test_dataset = SiameseDataset(test_dataset_path, transform=transform_val, train=False)
    test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)

    # Lists to store predictions and ground truth
    all_predictions = []
    all_labels = []
    all_scores = []

    # Evaluation loop
    with torch.no_grad():
        for img1, img2, labels in test_loader:
            img1, img2 = img1.to(device), img2.to(device)
            
            # Forward pass
            output1, output2 = model(img1, img2)
            
            # Calculate distance
            distance = nn.functional.pairwise_distance(output1, output2)
            similarity_scores = 1 - (distance / 2.0)  # Normalize to [0,1]
            
            # Convert to binary predictions using threshold of 0.90
            predictions = (similarity_scores >= 0.90).cpu().numpy()
            
            all_predictions.extend(predictions)
            all_labels.extend(labels.cpu().numpy())
            all_scores.extend(similarity_scores.cpu().numpy())

    # Convert to numpy arrays
    all_predictions = np.array(all_predictions)
    all_labels = np.array(all_labels)
    all_scores = np.array(all_scores)

    # Calculate metrics
    # F1 Score
    f1 = f1_score(all_labels, all_predictions)
    
    # Confusion Matrix
    cm = confusion_matrix(all_labels, all_predictions)
    
    # ROC Curve and AUC
    fpr, tpr, _ = roc_curve(all_labels, all_scores)
    roc_auc = auc(fpr, tpr)

    # Print metrics
    print(f"\nEvaluation Metrics:")
    print(f"F1 Score: {f1:.4f}")
    print("\nConfusion Matrix:")
    print(cm)
    print(f"\nAUC Score: {roc_auc:.4f}")

    # Plot ROC Curve
    plt.figure(figsize=(8, 6))
    plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (AUC = {roc_auc:.2f})')
    plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('Receiver Operating Characteristic (ROC) Curve')
    plt.legend(loc="lower right")
    plt.show()

    # Plot Confusion Matrix
    plt.figure(figsize=(8, 6))
    plt.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
    plt.title('Confusion Matrix')
    plt.colorbar()
    tick_marks = np.arange(2)
    plt.xticks(tick_marks, ['Non-Match', 'Match'])
    plt.yticks(tick_marks, ['Non-Match', 'Match'])
    
    # Add text annotations to confusion matrix
    thresh = cm.max() / 2.
    for i, j in np.ndindex(cm.shape):
        plt.text(j, i, format(cm[i, j], 'd'),
                horizontalalignment="center",
                color="white" if cm[i, j] > thresh else "black")

    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    # Device selection (similar to your existing code)
    if torch.backends.mps.is_available() and torch.backends.mps.is_built():
        device = torch.device("mps")
        print("Using MPS (Metal Performance Shaders) for M-series Mac")
    else:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Using device: {device}")

    model_path = 'models/new.pth'
    test_dataset_path = 'data/test'  # Update this path to your test dataset location
    
    evaluate_model(model_path, test_dataset_path, device)