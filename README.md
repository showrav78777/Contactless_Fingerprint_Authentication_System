# Contactless Fingerprint Authentication

A full-stack fingerprint registration and verification system built with Flutter (frontend) and Django REST Framework (backend).

## Features

- Contactless fingerprint capture flow
- Registration and login verification pipeline
- Local image preprocessing/storage
- Django API backend for upload, processing, and verification

## Project Structure

```text
fingerprint-main/
├── lib/                  # Flutter source code
├── assets/               # Flutter assets
├── SNN/                  # Siamese Neural Network training/inference pipeline
├── notes/                # Django backend project
│   ├── api/              # API, models, and processing logic
│   ├── media/            # Uploaded/processed fingerprint images
│   └── manage.py
├── android/ios/web/...   # Flutter platform folders
└── pubspec.yaml          # Flutter dependencies
```

## Requirements

- Flutter SDK (Dart >= 3.5.0)
- Python 3.9+
- pip / virtual environment tools

## Setup

### Backend

```bash
cd notes
python3 -m venv .venv
source .venv/bin/activate
pip install django djangorestframework django-cors-headers pillow matplotlib torch torchvision
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

### Frontend

```bash
flutter pub get
flutter run
```

## API Base

- Local backend: `http://<your-ip>:8000/api/`

## SNN Architecture

The `SNN/` module contains the fingerprint matching research/training pipeline.

### 1) Preprocessing Pipeline (`SNN/preprocess_dataset.py`)

Each fingerprint image is converted into three feature representations:
- **Gabor map** (ridge enhancement)
- **Skeleton map** (1-pixel-wide ridge structure)
- **Minutiae map** (ridge endings/bifurcations)

Main steps:
- normalization
- segmentation + ROI mask
- orientation estimation
- ridge frequency estimation
- Gabor filtering
- skeletonization
- minutiae extraction

Outputs are saved per-person under `data/processed_dataset/<person_id>/{gabor,skeleton,minutiae}/`.

### 2) Dataset/Pairs (`SNN/src/fingerprint_dataset.py`)

Training uses Siamese-style pairs:
- **Positive pairs**: two samples from the same person
- **Negative pairs**: samples from different persons

Each sample in enhanced training includes 6 tensors:
- `gabor1, skeleton1, minutiae1, gabor2, skeleton2, minutiae2`

### 3) Model Variants

- **Base Siamese pipeline** (`SNN/src/model.py`, `SNN/train.py`)
  - twin encoder network with contrastive loss
  - outputs embeddings and compares with Euclidean distance

- **Enhanced multi-branch network** (`SNN/src/enhanced_model.py`, `SNN/train_enhanced.py`)
  - three branch encoders (Gabor/Skeleton/Minutiae)
  - attention module (`RidgeAttention`) in each branch
  - feature fusion MLP
  - L2-normalized embedding output
  - combined contrastive + cosine-based loss (`EnhancedContrastiveLoss`)

### 4) Inference/Matching (`SNN/fingerprint_matcher.py`)

- loads trained Siamese weights (`models/new.pth`)
- preprocesses and embeds probe + gallery images
- computes similarity from pairwise distance
- performs person-level matching against stored database fingerprints

## Notes

- Update backend host in `lib/config.dart` as needed.
- Virtual environment folders are intentionally git-ignored.
