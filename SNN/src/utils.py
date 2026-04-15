# import torch
# import torch.nn.functional as F
# from torchvision import transforms
# import matplotlib.pyplot as plt
# from PIL import Image

# # Constants
# INPUT_SIZE = 128
# EMBEDDING_SIZE = 256
# MARGIN = 1.0
# BATCH_SIZE = 32
# EPOCHS = 100
# LEARNING_RATE = 0.0001
# WEIGHT_DECAY = 1e-4
# PATIENCE = 15

# # Data transforms
# transform_train = transforms.Compose([
#     transforms.Resize((INPUT_SIZE, INPUT_SIZE)),
#     transforms.RandomHorizontalFlip(),
#     transforms.RandomVerticalFlip(),
#     transforms.RandomRotation(15),
#     transforms.RandomAffine(degrees=10, translate=(0.1, 0.1), scale=(0.9, 1.1)),
#     transforms.ColorJitter(brightness=0.2, contrast=0.2),
#     transforms.ToTensor(),
#     transforms.Normalize(mean=[0.485], std=[0.229])
# ])

# transform_val = transforms.Compose([
#     transforms.Resize((INPUT_SIZE, INPUT_SIZE)),
#     transforms.ToTensor(),
#     transforms.Normalize(mean=[0.485], std=[0.229])
# ])

# def visualize_pairs(pairs, labels, num_examples=5):
#     fig, axes = plt.subplots(num_examples, 2, figsize=(10, num_examples*3))
#     for idx in range(num_examples):
#         img1 = Image.open(pairs[idx][0]).convert('L')
#         img2 = Image.open(pairs[idx][1]).convert('L')
#         axes[idx, 0].imshow(img1, cmap='gray')
#         axes[idx, 1].imshow(img2, cmap='gray')
#         axes[idx, 0].axis('off')
#         axes[idx, 1].axis('off')
#         axes[idx, 0].set_title(f'{"Same" if labels[idx] == 0 else "Different"} Class')
#     plt.tight_layout()
#     plt.show()

# def plot_metrics(train_losses, val_losses, train_accs, val_accs):
#     fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))
    
#     ax1.plot(train_losses, label='Train Loss')
#     ax1.plot(val_losses, label='Val Loss')
#     ax1.set_title('Loss over epochs')
#     ax1.set_xlabel('Epoch')
#     ax1.set_ylabel('Loss')
#     ax1.legend()
#     ax1.grid(True)
    
#     ax2.plot(train_accs, label='Train Accuracy')
#     ax2.plot(val_accs, label='Val Accuracy')
#     ax2.set_title('Accuracy over epochs')
#     ax2.set_xlabel('Epoch')
#     ax2.set_ylabel('Accuracy (%)')
#     ax2.legend()
#     ax2.grid(True)
    
#     plt.tight_layout()
#     plt.show()


# import torch
# import torch.nn.functional as F
# from torchvision import transforms
# import matplotlib.pyplot as plt
# from PIL import Image

# # Constants
# INPUT_SIZE = 128
# EMBEDDING_SIZE = 256
# MARGIN = 1.0
# BATCH_SIZE = 32
# EPOCHS = 100
# LEARNING_RATE = 0.0001
# WEIGHT_DECAY = 1e-4
# PATIENCE = 15

# # Data transforms
# transform_train = transforms.Compose([
#     transforms.Resize((INPUT_SIZE, INPUT_SIZE)),
#     transforms.RandomHorizontalFlip(),
#     transforms.RandomVerticalFlip(),
#     transforms.RandomRotation(15),
#     transforms.RandomAffine(degrees=10, translate=(0.1, 0.1), scale=(0.9, 1.1)),
#     transforms.ColorJitter(brightness=0.2, contrast=0.2),
#     transforms.ToTensor(),
#     transforms.Normalize(mean=[0.485], std=[0.229])
# ])

# transform_val = transforms.Compose([
#     transforms.Resize((INPUT_SIZE, INPUT_SIZE)),
#     transforms.ToTensor(),
#     transforms.Normalize(mean=[0.485], std=[0.229])
# ])

# def visualize_pairs(pairs, labels, num_examples=5):
#     """
#     Visualizes a set of image pairs with labels indicating whether they are of the same class.
    
#     Parameters:
#     - pairs (list of tuples): List of image path pairs (or PIL images/tensors if modified).
#     - labels (list or tensor): List of labels (0 for same, 1 for different).
#     - num_examples (int): Number of examples to visualize.

#     Displays:
#     - A figure with `num_examples` rows, each row showing a pair of images and its label.
#     """
#     fig, axes = plt.subplots(num_examples, 2, figsize=(10, num_examples*3))
#     for idx in range(num_examples):
#         try:
#             img1 = Image.open(pairs[idx][0]).convert('L')
#             img2 = Image.open(pairs[idx][1]).convert('L')
#             axes[idx, 0].imshow(img1, cmap='gray')
#             axes[idx, 1].imshow(img2, cmap='gray')
#             axes[idx, 0].axis('off')
#             axes[idx, 1].axis('off')
#             axes[idx, 0].set_title(f'{"Same" if labels[idx] == 0 else "Different"} Class')
#         except Exception as e:
#             print(f"Error displaying pair {idx}: {e}")
#     plt.tight_layout()
#     plt.show()

# def plot_metrics(train_losses, val_losses, train_accs=None, val_accs=None):
#     """
#     Plots training and validation loss and accuracy over epochs.

#     Parameters:
#     - train_losses (list): Training loss values per epoch.
#     - val_losses (list): Validation loss values per epoch.
#     - train_accs (list, optional): Training accuracy values per epoch.
#     - val_accs (list, optional): Validation accuracy values per epoch.

#     Displays:
#     - Two plots: one for loss and one for accuracy (if provided) over epochs.
#     """
#     fig, axes = plt.subplots(1, 2 if train_accs and val_accs else 1, figsize=(15, 5))
    
#     # Plotting Loss
#     axes[0].plot(train_losses, label='Train Loss')
#     axes[0].plot(val_losses, label='Val Loss')
#     axes[0].set_title('Loss over epochs')
#     axes[0].set_xlabel('Epoch')
#     axes[0].set_ylabel('Loss')
#     axes[0].legend()
#     axes[0].grid(True)
    
#     # Plotting Accuracy if available
#     if train_accs and val_accs:
#         axes[1].plot(train_accs, label='Train Accuracy')
#         axes[1].plot(val_accs, label='Val Accuracy')
#         axes[1].set_title('Accuracy over epochs')
#         axes[1].set_xlabel('Epoch')
#         axes[1].set_ylabel('Accuracy (%)')
#         axes[1].legend()
#         axes[1].grid(True)
    
#     plt.tight_layout()
#     plt.show()

# # Example usage in training or evaluation functions, with `train_losses`, `val_losses`, `train_accs`, `val_accs` lists.


import torch
import torch.nn.functional as F
from torchvision import transforms
import matplotlib.pyplot as plt
from PIL import Image

# Constants
INPUT_SIZE = 128
EMBEDDING_SIZE = 256
MARGIN = 1.0
BATCH_SIZE = 32
EPOCHS = 100
LEARNING_RATE = 0.0001
WEIGHT_DECAY = 1e-4
PATIENCE = 15

# Data Transforms
transform_train = transforms.Compose([
    transforms.Resize((INPUT_SIZE, INPUT_SIZE)),
    transforms.RandomHorizontalFlip(),
    transforms.RandomVerticalFlip(),
    transforms.RandomRotation(15),
    transforms.RandomAffine(degrees=10, translate=(0.1, 0.1), scale=(0.9, 1.1)),
    transforms.ColorJitter(brightness=0.2, contrast=0.2),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485], std=[0.229])
])

transform_val = transforms.Compose([
    transforms.Resize((INPUT_SIZE, INPUT_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485], std=[0.229])
])

# Utility to Visualize Image Pairs
def visualize_pairs(pairs, labels, num_examples=5):
    """
    Visualizes a set of image pairs with labels indicating whether they are of the same class.

    Parameters:
    - pairs (list of tuples): List of image path pairs (or PIL images/tensors if modified).
    - labels (list or tensor): List of labels (0 for same, 1 for different).
    - num_examples (int): Number of examples to visualize.

    Displays:
    - A figure with `num_examples` rows, each row showing a pair of images and its label.
    """
    num_examples = min(num_examples, len(pairs), len(labels))
    fig, axes = plt.subplots(num_examples, 2, figsize=(10, num_examples * 3))

    for idx in range(num_examples):
        try:
            img1 = Image.open(pairs[idx][0]).convert('L')
            img2 = Image.open(pairs[idx][1]).convert('L')
            axes[idx, 0].imshow(img1, cmap='gray')
            axes[idx, 1].imshow(img2, cmap='gray')
            axes[idx, 0].axis('off')
            axes[idx, 1].axis('off')
            label_text = "Same Class" if labels[idx] == 0 else "Different Class"
            axes[idx, 0].set_title(label_text)
        except Exception as e:
            print(f"Error displaying pair {idx}: {e}")

    plt.tight_layout()
    plt.show()

# Plot Training Metrics
def plot_metrics(train_losses, val_losses, train_accs=None, val_accs=None):
    """
    Plots training and validation loss and accuracy over epochs.

    Parameters:
    - train_losses (list): Training loss values per epoch.
    - val_losses (list): Validation loss values per epoch.
    - train_accs (list, optional): Training accuracy values per epoch.
    - val_accs (list, optional): Validation accuracy values per epoch.

    Displays:
    - Two plots: one for loss and one for accuracy (if provided) over epochs.
    """
    if not train_losses or not val_losses:
        print("Error: train_losses and val_losses are required.")
        return

    num_plots = 2 if train_accs and val_accs else 1
    fig, axes = plt.subplots(1, num_plots, figsize=(15, 5))

    # Plotting Loss
    if num_plots == 1:
        axes = [axes]
    axes[0].plot(train_losses, label='Train Loss', color='blue')
    axes[0].plot(val_losses, label='Validation Loss', color='orange')
    axes[0].set_title('Loss Over Epochs')
    axes[0].set_xlabel('Epoch')
    axes[0].set_ylabel('Loss')
    axes[0].legend()
    axes[0].grid(True)

    # Plotting Accuracy if available
    if train_accs and val_accs:
        axes[1].plot(train_accs, label='Train Accuracy', color='green')
        axes[1].plot(val_accs, label='Validation Accuracy', color='red')
        axes[1].set_title('Accuracy Over Epochs')
        axes[1].set_xlabel('Epoch')
        axes[1].set_ylabel('Accuracy (%)')
        axes[1].legend()
        axes[1].grid(True)

    plt.tight_layout()
    plt.show()