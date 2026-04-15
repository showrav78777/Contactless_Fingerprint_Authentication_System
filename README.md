# Contactless Fingerprint Authentication System

A full-stack biometric authentication system combining **Flutter (frontend)**, **Django REST Framework (backend)**, and a **Siamese Neural Network (SNN)** for fingerprint matching.

---

## 🚀 Key Features

* 📷 Contactless fingerprint capture using camera
* 🔐 Registration and login verification pipeline
* 🧠 Deep learning-based fingerprint matching (SNN)
* ⚙️ Django REST API for processing and storage
* 📱 Cross-platform mobile app (Flutter)

---

## 🏗️ Project Architecture

```text
fingerprint-main/
├── lib/                  # Flutter frontend
├── assets/               # App assets
├── SNN/                  # ML training + inference
├── notes/                # Django backend
│   ├── api/              # API logic
│   ├── media/            # Stored images
│   └── manage.py
├── android/ios/web/...   # Platform-specific builds
└── pubspec.yaml
```

---

## ⚙️ Tech Stack

* **Frontend:** Flutter (Dart)
* **Backend:** Django REST Framework
* **ML:** PyTorch, OpenCV
* **Computer Vision:** Gabor filters, Skeletonization, Minutiae extraction

---

## 🛠️ Setup Instructions

### 🔹 Backend (Django)

```bash
cd notes
python3 -m venv .venv
source .venv/bin/activate
pip install django djangorestframework django-cors-headers pillow matplotlib torch torchvision
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

---

### 🔹 Frontend (Flutter)

```bash
flutter pub get
flutter run
```

---

## 🌐 API Endpoint

```
http://<your-ip>:8000/api/
```

---

## 🧠 Machine Learning Pipeline (SNN)

### 🔸 Preprocessing

Each fingerprint is transformed into:

* Gabor Map (ridge enhancement)
* Skeleton Map (ridge structure)
* Minutiae Map (key points)

---

### 🔸 Dataset Strategy

* Positive pairs → same person
* Negative pairs → different persons

Each training sample includes:

```
gabor1, skeleton1, minutiae1, gabor2, skeleton2, minutiae2
```

---

### 🔸 Model Architecture

#### Base Model

* Siamese Network
* Contrastive Loss
* Euclidean distance matching

#### Enhanced Model

* Multi-branch (Gabor + Skeleton + Minutiae)
* Attention mechanism (RidgeAttention)
* Feature fusion + normalized embeddings
* Combined loss (contrastive + cosine)

---

### 🔸 Inference

* Loads trained weights (`models/new.pth`)
* Generates embeddings
* Matches fingerprints using similarity scoring

---

## 📦 Model Download

Due to GitHub size limits, the trained model is not included.

👉 Download: **[Add Google Drive Link]**
Place inside:

```
SNN/models/
```

---

## 📷 Screenshots

(Add your app screenshots here)

---

## ⚠️ Notes

* Update backend IP in `lib/config.dart`
* Virtual environments are excluded via `.gitignore`
* Large model files are not stored in the repository

---

## 👨‍💻 Author

**Niloy Showrav**
