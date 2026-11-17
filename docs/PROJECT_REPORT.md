# NeuralInk: handwritten digit recognition using deep learning

**Course:** Deep Learning Foundations · **Experiment:** 11, Capstone Project · **Programme:** B.Tech Computer Science, AI specialization

## Aim

Build and evaluate a convolutional neural network for single handwritten digit recognition, and integrate it with an accessible web application whose frontend and inference API deploy independently.

## Abstract

NeuralInk accepts a drawn or uploaded digit, converts it into a normalized 28×28 grayscale representation and classifies it using a locally trained TensorFlow CNN. A React interface presents the predicted class, softmax confidence, top three predictions, all ten class scores, actual processing time and the image supplied to the model. The system separates offline learning from online inference and bundles training artifacts for an educational Model Insights view. It does not use an external AI inference service. Evaluation is restricted to the held-out MNIST test dataset; generalization to browser drawings and photographs requires separate study.

## Problem statement and objectives

Handwriting varies in size, placement, contrast and style. A practical digit recognizer must connect a trained model with predictable input handling and understandable feedback. This project therefore aims to train a genuine CNN, implement one canonical preprocessing path for both input methods, expose a validated FastAPI endpoint, create a usable drawing/upload interface, report measured evaluation results and prepare an independent HTTPS deployment.

## Technologies

React, Vite and TypeScript provide the interface. Tailwind CSS supplies styling, Lucide supplies icons and Motion supports restrained animation. FastAPI and Uvicorn provide the Python API; TensorFlow/Keras performs training and local inference; NumPy and Pillow support numerical and image operations. Docker Compose, Caddy, systemd and Vercel cover deployment preparation. Exact package versions are recorded in the dependency manifests and lockfile.

## Dataset

MNIST contains 60,000 labeled training images and 10,000 held-out test images, each a 28×28 grayscale digit from 0 through 9. A validation subset is selected from the original training portion. Test samples do not contribute to weight updates, validation checkpoint selection or preprocessing-statistic fitting. Pixel normalization uses the fixed 0–255 scale rather than statistics learned from test images. Dataset provenance: [Keras MNIST API](https://keras.io/api/datasets/mnist/).

## CNN architecture

The LeNet-inspired network uses Conv2D(32,3×3,ReLU), MaxPooling2D(2×2), Conv2D(64,3×3,ReLU), MaxPooling2D(2×2), Flatten, Dense(128,ReLU), Dropout(0.3), and Dense(10,Softmax). With valid convolutions its trainable parameter count is 225,034. The 1,600-value flattened feature vector feeds the dense hidden layer. See ARCHITECTURE.md for dimensional derivation and diagrams; generated metadata records the actual trained architecture and parameter count.

## Training methodology

The offline script sets a reproducible seed, loads MNIST, creates training and validation subsets, normalizes input and trains with Adam and sparse categorical cross-entropy. Small rotations, translations and scale changes are suitable augmentations; flips and extreme rotations can change meaning and are excluded. Validation monitoring drives early stopping and best-model checkpointing. Epoch count and batch size are configurable. The chosen checkpoint is evaluated on the untouched test set, and history, metadata, classification metrics and confusion matrix are saved alongside the model. Fixed seeds improve repeatability but do not guarantee bit-identical floating point outcomes on different runtimes or hardware.

## Image preprocessing

The backend validates bytes, decoded format and pixel count before inference. It applies EXIF orientation, handles transparency, converts to grayscale, estimates foreground polarity, finds the digit bounds, preserves aspect ratio while resizing, and places the result on a 28×28 background with centering. Intensities are normalized into a `(1,28,28,1)` float tensor. Blank or unusable inputs return clear validation messages. Both drawing and upload modes use this function; the frontend does not implement a second recognition pipeline.

## System architecture and API workflow

The browser submits a canvas PNG or uploaded PNG/JPEG/WebP to `POST /api/v1/predict` using multipart field `file`. FastAPI applies size/rate/format validation, preprocesses the image and calls the model already loaded in memory. The JSON response contains prediction, confidence, sorted top three, ten probabilities, preview, model version, uncertainty flag and measured server processing time. The client cancels outdated requests and avoids rendering stale results. `/healthz`, `/readyz` and `/api/v1/model/info` provide process status, inference readiness and real model metadata.

Vercel hosts static frontend assets; a separate Linux host runs the API behind Caddy HTTPS or an outbound tunnel. Configurable API URL and CORS origins decouple the deployments. No database, account registration or permanent image store is required.

## Results and evaluation

Actual numerical results are recorded in `backend/models/metrics.json`, architecture/runtime provenance in `metadata.json`, and epoch-by-epoch measurements in `history.json`. Their frontend copies are in `frontend/public/model/`. The saved files are the source of truth; no accuracy value is assumed in advance.

<!-- TRAINING_RESULTS_START -->
Training completed locally using TensorFlow 2.18.1, seed 42, batch size 128 and 8 epochs. The best validation-loss checkpoint was epoch 8. The split contained 54,000 training, 6,000 validation and 10,000 test images.

| Measurement | Observed value |
| --- | --- |
| Held-out test accuracy | 99.24% |
| Held-out test cross-entropy | 0.02274431 |
| Final epoch training accuracy (augmentation/dropout active) | 98.23% |
| Final epoch validation accuracy (inference mode) | 99.03% |
| Final epoch training loss | 0.05896027 |
| Final epoch validation loss | 0.03008274 |
| Trainable parameters | 225,034 |
| Measured training duration on this machine | 63.818 seconds |

The confusion matrix contains 9,924 correct test classifications and 76 errors. Validation accuracy can exceed training accuracy because augmentation and dropout are active only during training.

| Digit | Precision | Recall | F1 | Support |
| --- | --- | --- | --- | --- |
| 0 | 0.9939 | 0.9990 | 0.9964 | 980 |
| 1 | 0.9921 | 0.9982 | 0.9952 | 1135 |
| 2 | 0.9980 | 0.9913 | 0.9947 | 1032 |
| 3 | 0.9950 | 0.9861 | 0.9906 | 1010 |
| 4 | 0.9949 | 0.9949 | 0.9949 | 982 |
| 5 | 0.9856 | 0.9955 | 0.9905 | 892 |
| 6 | 0.9979 | 0.9833 | 0.9905 | 958 |
| 7 | 0.9846 | 0.9942 | 0.9894 | 1028 |
| 8 | 0.9878 | 0.9949 | 0.9913 | 974 |
| 9 | 0.9940 | 0.9861 | 0.9900 | 1009 |

<!-- TRAINING_RESULTS_END -->

Accuracy is the fraction of correct test predictions. Cross-entropy also reflects how much score is assigned to the correct label. The confusion matrix and class-wise precision, recall and F1 reveal errors hidden by aggregate accuracy. Training/validation curves help diagnose underfitting and overfitting. Softmax confidence is an uncalibrated model score; the uncertainty threshold is a user-interface heuristic, not a statistical guarantee. Timing returned by a request measures server-side processing and excludes browser/network round-trip latency.

## Limitations

- Only one handwritten digit is supported; multi-digit OCR, full-page recognition and arbitrary photographs are outside scope.
- MNIST test accuracy does not establish accuracy on canvas handwriting or real photographs.
- Polarity, crop and centering heuristics may fail under textured backgrounds, severe shadows or multiple foreground objects.
- A CNN can be confidently wrong on unfamiliar input; the uncertainty heuristic cannot detect every out-of-distribution image.
- Rate limiting is process-local and can be shared across users behind the reverse proxy. Larger deployments need a shared or edge limiter.
- Production DNS/TLS, account-based Vercel publishing and physical-device touch testing require the relevant external environment; configuration files alone do not prove those checks.

## Future scope

Collect a consented, labeled browser/photo benchmark; measure domain-specific accuracy; calibrate confidence using a separate validation dataset; study stronger background segmentation and out-of-distribution detection; and add robust feature-map inspection when useful. Multi-digit segmentation would require a separate task definition and evaluation dataset.

## Conclusion

NeuralInk connects neural network fundamentals to a complete inference workflow: learned convolutional features, gradient-based optimization, regularization, held-out evaluation, image preprocessing and an independently deployed web interface. Its claims are bounded by the saved experimental artifacts and verified runtime checks. The project is suitable for demonstrating Experiment 11 and explaining the practical gap between benchmark classification and real user input.
