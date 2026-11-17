# NeuralInk architecture

## System and deployment

```mermaid
flowchart LR
  U[Browser: draw or upload] --> F[Vercel: React static frontend]
  F -->|HTTPS multipart image| P[Caddy or outbound tunnel]
  P --> A[FastAPI: one Uvicorn worker]
  A --> V[Validation and canonical preprocessing]
  V --> M[Loaded TensorFlow CNN]
  M -->|JSON probabilities and preview| F
  T[Offline MNIST training] --> K[Saved .keras model and metadata]
  K -->|Load once on startup| M
  T --> J[History and evaluation JSON]
  J -->|Bundled with frontend| I[Offline-capable Model Insights]
```

The frontend and API can use different domains and machines. The API URL is build configuration. Browser CORS checks compare the frontend origin against the API allowlist. HTTPS terminates at the public reverse proxy or tunnel provider. Uploaded images remain in request memory; no upload directory or database is required. Training is a separate command, never an API request or startup task.

## CNN

```mermaid
flowchart TD
  X[28 × 28 × 1 normalized input] --> C1[Conv2D: 32 filters, 3 × 3, ReLU]
  C1 --> P1[MaxPool 2 × 2]
  P1 --> C2[Conv2D: 64 filters, 3 × 3, ReLU]
  C2 --> P2[MaxPool 2 × 2]
  P2 --> F[Flatten]
  F --> D[Dense 128, ReLU]
  D --> R[Dropout 0.3 during training]
  R --> O[Dense 10, softmax]
```

With valid convolutions, dimensions are 28→26→13→11→5. Flatten produces 1,600 values. Parameter counts: first convolution 320; second convolution 18,496; dense hidden layer 204,928; output 1,290; total **225,034**. Pooling, flatten, dropout and training augmentation have no learned parameters. The saved metadata is authoritative for the actual trained model.

## Request flow

```mermaid
sequenceDiagram
  participant B as Browser
  participant A as FastAPI
  participant P as Preprocessor
  participant M as Loaded CNN
  B->>A: POST /api/v1/predict (file)
  A->>A: Enforce body, MIME and rate limits
  A->>P: Decode image bytes
  P->>P: EXIF, transparency, grayscale, polarity
  P->>P: Crop foreground, aspect-preserving resize, center
  P-->>A: (1,28,28,1) normalized tensor + PNG preview
  A->>M: Inference with training=False
  M-->>A: Ten softmax values
  A-->>B: Digit, top three, all probabilities, timing, preview
  B->>B: Render only if response matches current input
```

Blank/corrupt/unsupported/oversized images return structured errors. The client distinguishes validation, connection, timeout and unavailable-model failures and can submit a new request. Cancellation and input-version checks prevent an old prediction from replacing a newer drawing. Softmax output is model confidence, not calibrated correctness probability.

## Preprocessing boundary

```mermaid
flowchart LR
  I[PNG/JPEG/WebP] --> D[Safe decode and dimension checks]
  D --> E[EXIF orientation and alpha handling]
  E --> G[Grayscale and background estimation]
  G --> B[Foreground detection and bounds]
  B --> R[Aspect-preserving resize into 20 × 20]
  R --> C[Place on 28 × 28 and center mass]
  C --> N[Float normalization 0..1]
```

Both input modes call this exact backend implementation. Browser transport resizing or canvas serialization does not replace it. Foreground thresholds and contrast guards are deterministic heuristics and cannot guarantee reliable processing of textured photographs or multiple digits.

## Health and security

`/healthz` is process liveness. `/readyz` requires the real loaded model and successful initialization. `/api/v1/model/info` publishes actual metadata. One model instance is loaded per worker; use one worker unless memory and limiter design are deliberately revised. The body/pixel bounds protect memory, while the proxy caps total multipart traffic. Public error responses omit private stack traces. Trusted proxy behavior and process-local limiter constraints are described in DEPLOYMENT.md.
