# NeuralInk

Your handwriting. A neural network's perspective.

A Deep Learning Foundations Experiment 11 capstone: draw or upload one handwritten digit, then inspect a genuine TensorFlow CNN prediction, all ten softmax scores and the processed 28×28 input. React/Vite deploys to Vercel; FastAPI runs independently on your Linux server. No external AI inference API, database or account registration is required.

## Repository

```text
frontend/           React + TypeScript workspace, canvas, uploader, Model Insights
backend/app/        FastAPI, canonical preprocessing, loaded CNN inference
backend/training/   Reproducible MNIST training and evaluation
backend/models/     Saved model and measured training artifacts
backend/tests/      Backend validation, preprocessing and API tests
deploy/             Docker Compose, Caddy, systemd and tunnel examples
docs/               Project report, viva guide, architecture and deployment
qa/                 Live integration verification
.github/workflows/  Automated checks
```

## Run locally

Use Python 3.11 and Node.js 22 LTS. From PowerShell:

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
# Skip training if matching trained artifacts are already present.
.\.venv\Scripts\python.exe -m training.train --epochs 8 --batch-size 128 --seed 42
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1 --no-proxy-headers
```

In another terminal:

```powershell
cd frontend
npm ci
Copy-Item .env.example .env
# Local .env: API=http://127.0.0.1:8000
npm run dev -- --host 127.0.0.1
```

Open the Vite URL. Ensure backend `CORS_ORIGINS` includes the exact frontend origin. Linux uses `.venv/bin/python` instead of `.venv\Scripts\python.exe`. The API loads saved weights once; it never trains on startup. Model absence produces failed readiness rather than fabricated predictions.

## Train, check and build

```powershell
# From backend:
.\.venv\Scripts\python.exe -m training.train --epochs 8 --batch-size 128 --seed 42
.\.venv\Scripts\python.exe -m pytest
# From frontend:
npm run test -- --run
npm run build
# From repository root, with the API running and a real single-digit image:
python qa/verify_live.py path/to/digit.png --base-url http://127.0.0.1:8000
```

The completed 8-epoch run achieved **99.24% held-out MNIST test accuracy** and **0.02274431 test loss**, with 225,034 parameters. Training used 54,000 images and validation used 6,000; testing used 10,000 untouched images. Actual results live in `backend/models/{metadata,history,metrics}.json`; Model Insights reads matching bundled JSON offline. The network is Conv32 → Pool → Conv64 → Pool → Dense128 → Dropout → Softmax10. The expected parameter count is 225,034; saved metadata is authoritative. Do not equate MNIST accuracy with accuracy on arbitrary handwriting photographs.

## Deploy

Vercel: root `frontend`, install `npm ci`, build `npm run build`, output `dist`, environment `API=https://your-api-domain`. API: copy matching model artifacts to your Linux server and configure exact CORS origins, domain and TLS email in `deploy/.env`.

```bash
cp deploy/.env.example deploy/.env
# Edit real deployment values before running.
docker compose --env-file deploy/.env -f deploy/docker-compose.yml up -d --build
python3 deploy/scripts/check-readiness.py https://your-api-domain
```

The backend port is internal to Compose. Only Caddy publishes ports 80/443. Public deployment requires your real host, domain and provider accounts. See [complete deployment instructions](docs/DEPLOYMENT.md), including native systemd, CGNAT tunnel, updates and recovery.

## API and privacy

- `GET /healthz`: process liveness.
- `GET /readyz`: loaded-model readiness.
- `GET /api/v1/model/info`: model provenance and real evaluation metadata.
- `POST /api/v1/predict`: multipart `file`; returns digit, confidence, top three, ten probabilities, uncertainty flag, actual processing time and base64 PNG input preview.
- `POST /api/v1/visualize`: optional genuine intermediate convolution activations, computed only on request and covered by the same POST rate budget.

PNG, JPEG and supported WebP are accepted up to the configured limit (default 5 MiB and 12 million decoded pixels). Images are processed in memory and discarded. Confidence comes from softmax and is not calibrated correctness probability. The default uncertainty threshold is 0.7. CORS is an origin policy; the process-local limiter is not a distributed abuse prevention system.

Read the [project report](docs/PROJECT_REPORT.md), [viva guide](docs/VIVA_GUIDE.md) and [architecture](docs/ARCHITECTURE.md). MIT licensed; dataset and dependency licenses apply separately.
