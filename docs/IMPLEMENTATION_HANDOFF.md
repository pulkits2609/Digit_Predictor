# NeuralInk implementation handoff

Project location: `C:\Users\Pulkit Sharma\IMP STUFF\Notes 4th Year\deeplearning\exp11`

Built on 16 November 2026. The project is initialized as a local Git repository on branch `main`; it has not been pushed or publicly deployed.

## Implemented

React/Vite/TypeScript/Tailwind frontend with a responsive dark interface, Motion animations respecting reduced motion, Lucide icons, pointer drawing, adjustable brush, eraser, undo/redo/clear, upload validation, typed API requests, cancellation, timeouts, stale-result protection, retry controls, processed-image preview, ten-class distribution, top-three rankings, and offline Model Insights.

FastAPI backend loads a genuine trained TensorFlow CNN once. Both image modes share decoding, EXIF orientation, transparency handling, polarity estimation, foreground cropping, aspect-preserving scaling and center-of-mass alignment into a normalized `(1,28,28,1)` tensor. Includes bounded requests, decoded-image limits, configurable CORS, process-local rate limiting, safe errors, health/readiness checks, model metadata, and an optional API for real convolution feature maps. Uploaded images remain in memory and are discarded.

Training, evaluation, saved model, plots, confusion matrix, per-class metrics, academic report, viva guide, Mermaid architecture diagrams, Docker/Caddy/systemd/tunnel deployment guides, Vercel configuration, and CI are included.

## Structure

```text
exp11/
  frontend/         UI, tests, static training artifacts, Vercel config
  backend/app/      API, validation, preprocessing, inference
  backend/training/ Reproducible CNN training and evaluation
  backend/models/   Trained weights, metrics, plots, sample images
  backend/tests/    Backend unit/integration tests
  deploy/           Compose, Caddy, systemd, tunnel, readiness helper
  docs/             Report, viva, architecture, deployment
  qa/               Repeatable live API and browser smoke checks
  .github/          CI
```

## Actual model results

Architecture: Input28×28×1 → Conv32(3×3, ReLU) → MaxPool2 → Conv64(3×3, ReLU) → MaxPool2 → Flatten → Dense128(ReLU) → Dropout0.3 → Dense10(softmax). Mild rotation, translation and zoom run only during training.

| Measurement | Actual result |
|---|---:|
| Parameters | 225,034 |
| Training / validation images | 54,000 / 6,000 |
| Held-out test images | 10,000 |
| Epochs | 8 |
| Test accuracy | 99.24% |
| Test cross-entropy loss | 0.02274431 |
| Training duration on this machine | 63.818 seconds |

Seed42, batch128, Adam, early stopping and validation-loss checkpoint selection. The test set was excluded from training and model selection. Metrics are in `backend/models/{metadata,history,metrics}.json`, with matching JSON bundled under `frontend/public/model/`.

MNIST accuracy does not establish photographic or browser-input accuracy. A small live preprocessing smoke test recognized 9 of 10 selected examples; one3 became8. Confidence is an uncalibrated softmax score. Actual latency varies; one verified live sample took16.669ms, another9.434ms. These are individual observations, not a throughput benchmark.

## Verification

35 backend tests and13 frontend tests passed, including genuine saved-model inference, feature maps, timeout handling, stale-response protection and canvas operations. Ruff, ESLint, TypeScript and Python dependency consistency checks passed. The final production build passed (112.52KB gzipped JavaScript). Live Edge/Chromium tests passed mouse drawing, upload, undo/redo/clear, ten-class chart, processed preview, genuine convolution feature-map display, simulated network failure/recovery, offline insights, no browser exceptions, no horizontal overflow at390/768/1440px, and emulated touchscreen drawing. The browser-drawn7 and uploaded MNIST7 both returned genuine7 predictions. The recognition button is fully visible at1366×768. The frontend dependency audit reported zero known vulnerabilities.

Docker Compose configuration and official Caddy configuration validation passed. Docker image build and container boot remain unverified because the local Docker Desktop Linux engine was unavailable. Physical touch devices, Safari, Firefox, public TLS/DNS, Vercel hosting and remote Linux deployment have not been tested. The collapsible feature-map viewer computes and fetches intermediate activations only when opened.

## Local startup

The trained weights and installed environments already exist. Open two PowerShell terminals:

```powershell
cd 'C:\Users\Pulkit Sharma\IMP STUFF\Notes 4th Year\deeplearning\exp11\backend'
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1 --no-proxy-headers
```

```powershell
cd 'C:\Users\Pulkit Sharma\IMP STUFF\Notes 4th Year\deeplearning\exp11\frontend'
npm.cmd run dev -- --port 5173
```

Frontend: `http://127.0.0.1:5173/`. API readiness: `http://127.0.0.1:8000/readyz`. These local servers were left running at handoff. Development Vite configuration uses the loopback API; production requires an HTTPS endpoint.

Retrain from `backend`:

```powershell
.\.venv\Scripts\python.exe -m training.train --epochs 8 --batch-size 128 --seed 42
```

Build from `frontend`:

```powershell
npm.cmd ci
npm.cmd run build
```

Training regenerates weights and frontend artifact JSON. Restart the API and rebuild/redeploy the frontend together to keep model versions consistent. Do not run training during serving or container startup.

## Independent production deployment

Vercel: repository root directory `frontend`; install `npm ci`; build `npm run build`; output `dist`; set `VITE_API_BASE_URL=https://your-real-api-domain`. Redeploy after environment changes. No prediction backend is needed to build. An optional `VITE_GITHUB_URL` enables the repository link.

On the Linux server, copy the project and matching model artifacts, then:

```bash
cp deploy/.env.example deploy/.env
# Set your actual API_DOMAIN, TLS_EMAIL and exact CORS_ORIGINS.
docker compose --env-file deploy/.env -f deploy/docker-compose.yml config
docker compose --env-file deploy/.env -f deploy/docker-compose.yml up -d --build
docker compose --env-file deploy/.env -f deploy/docker-compose.yml ps
docker compose --env-file deploy/.env -f deploy/docker-compose.yml logs -f backend caddy
python3 deploy/scripts/check-readiness.py https://your-real-api-domain
```

Caddy publishes80/443; the raw API port is internal. `docs/DEPLOYMENT.md` contains stop/restart/update commands, a non-root systemd alternative, TLS/CORS troubleshooting, and an outbound Cloudflare Tunnel option for CGNAT.

Backend configuration: `APP_ENV`, `CORS_ORIGINS`, `MODEL_PATH`, `MODEL_METADATA_PATH`, `MAX_UPLOAD_MB`, `MAX_IMAGE_PIXELS`, `RATE_LIMIT_ENABLED`, `RATE_LIMIT_PER_MINUTE`, `UNCERTAINTY_THRESHOLD`, `LOG_LEVEL`. Compose additionally needs `API_DOMAIN`, `TLS_EMAIL`, and optionally `MAX_REQUEST_BODY`. Examples are provided; no production credentials are included. Single-worker memory limiting is intentional; the in-memory rate limiter does not coordinate multiple instances.

Remaining manual deployment work: choose the remote machine/domain, upload the trained model (weights are Git-ignored), configure real environment values and DNS or tunnel credentials, deploy the backend and Vercel frontend, and verify from the public frontend origin. No deployment has been claimed as successful.

Request flow: canvas PNG or uploaded image → multipart HTTPS request → validation → shared preprocessing → loaded CNN → real softmax scores and preview → frontend prediction and charts.
