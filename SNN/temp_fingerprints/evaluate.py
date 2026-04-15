import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import transforms
import numpy as np
from sklearn.metrics import confusion_matrix, roc_curve, auc, f1_score, precision_recall_curve, average_precision_score
import matplotlib.pyplot as plt
from model import EnhancedSiameseNetwork, get_device
from dataset import SiameseDataset

def evaluate_model(model_path, test_data_dir, batch_size=32):
    # Set up device
    device = get_device()
    
    # Load model
    model = EnhancedSiameseNetwork().to(device)
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.eval()
    
    # Data transformation
    transform = transforms.Compose([
        transforms.Resize((300, 300)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.5], std=[0.5])
    ])
    
    # Create test dataset and loader
    test_dataset = SiameseDataset(data_dir=test_data_dir, transform=transform, train=False)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)
    
    # Lists to store predictions and ground truth
    all_labels = []
    all_scores = []
    
    # Evaluate model
    print("Starting evaluation...")
    with torch.no_grad():
        for i, (img1, img2, labels) in enumerate(test_loader):
            img1, img2 = img1.to(device), img2.to(device)
            
            # Get model outputs
            output1, output2 = model(img1, img2)
            
            # Calculate similarity scores
            distance = nn.functional.pairwise_distance(output1, output2)
            similarity_scores = 1 - (distance / distance.max())  # Normalize to [0,1]
            
            # Store predictions and labels
            all_scores.extend(similarity_scores.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
            
            if (i + 1) % 10 == 0:
                print(f"Processed {(i+1)*batch_size} pairs...")
    
    # Convert to numpy arrays
    all_scores = np.array(all_scores)
    all_labels = np.array(all_labels)
    
    # Calculate metrics at different thresholds
    thresholds = np.arange(0, 1.1, 0.1)
    best_f1 = 0
    best_threshold = 0
    
    print("\nCalculating metrics at different thresholds...")
    for threshold in thresholds:
        predictions = (all_scores >= threshold).astype(int)
        f1 = f1_score(all_labels, predictions)
        print(f"Threshold {threshold:.1f}: F1 Score = {f1:.4f}")
        
        if f1 > best_f1:
            best_f1 = f1
            best_threshold = threshold
    
    # Use best threshold for final predictions
    final_predictions = (all_scores >= best_threshold).astype(int)
    
    # Calculate final metrics
    final_f1 = f1_score(all_labels, final_predictions)
    cm = confusion_matrix(all_labels, final_predictions)
    fpr, tpr, _ = roc_curve(all_labels, all_scores)
    roc_auc = auc(fpr, tpr)
    
    # Calculate precision-recall curve
    precision, recall, _ = precision_recall_curve(all_labels, all_scores)
    avg_precision = average_precision_score(all_labels, all_scores)
    
    # Print results
    print("\nFinal Evaluation Metrics:")
    print(f"Best Threshold: {best_threshold:.2f}")
    print(f"F1 Score: {final_f1:.4f}")
    print(f"AUC-ROC: {roc_auc:.4f}")
    print(f"Average Precision: {avg_precision:.4f}")
    print("\nConfusion Matrix:")
    print(cm)
    
    # Plot ROC Curve
    plt.figure(figsize=(10, 8))
    plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (AUC = {roc_auc:.2f})')
    plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('Receiver Operating Characteristic (ROC) Curve')
    plt.legend(loc="lower right")
    plt.savefig('evaluation_roc_curve.png')
    plt.close()
    
    # Plot Precision-Recall Curve
    plt.figure(figsize=(10, 8))
    plt.plot(recall, precision, color='blue', lw=2, label=f'PR curve (AP = {avg_precision:.2f})')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('Recall')
    plt.ylabel('Precision')
    plt.title('Precision-Recall Curve')
    plt.legend(loc="lower left")
    plt.savefig('evaluation_pr_curve.png')
    plt.close()
    
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
    plt.savefig('evaluation_confusion_matrix.png')
    plt.close()
    
    return {
        'best_threshold': best_threshold,
        'f1_score': final_f1,
        'auc_roc': roc_auc,
        'average_precision': avg_precision,
        'confusion_matrix': cm
    }

if __name__ == "__main__":
    # Example usage
    model_path = "models/new.pth"  # Path to your trained model
    test_data_dir = "data/test"    # Path to your test dataset
    
    results = evaluate_model(model_path, test_data_dir) 