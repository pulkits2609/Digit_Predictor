# NeuralInk inference backend

Python 3.11, TensorFlow 2.18.1 CPU, FastAPI and Pillow. All dependency versions are pinned in `requirements.txt`. The primary deployment target is Linux x86-64. Windows x86-64 supports local CPU development. No GPU, database or externally hosted AI model is required.

From this directory (PowerShell):

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -m training.train --epochs 8 --batch-size 128 --seed 42
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1 --no-proxy-headers
```

Linux uses `python3.11` and `.venv/bin/python`. If saved matching artifacts exist, training can be skipped. Training splits the original MNIST training set into 54,000 training and 6,000 validation images. The 10,000-image test set is evaluated after validation-only checkpoint selection. The saved model, metadata, metrics and history are under `models/`; public JSON copies support frontend insights. Keep model and metadata versions together.

`/healthz` checks the process; `/readyz` checks initialized model readiness; `/api/v1/model/info` returns metadata; `/api/v1/predict` accepts multipart field `file`. Prediction JSON includes a PNG data URI in `processed_image`, ten softmax scores and actual server-side elapsed time. The configured uncertainty threshold is an uncalibrated UI heuristic. Images are processed in memory without permanent storage. Both canvas and uploaded images use `app/ml/preprocessing.py`.

Configuration is in `.env.example`. Relative model paths resolve from the backend root. Set exact CORS origins and restart after changes. Use one worker: each worker otherwise loads a separate model and has a separate in-memory rate limiter. Uvicorn's proxy headers are disabled to avoid trusting spoofed client addresses. Behind a proxy, clients therefore share its rate-limit bucket unless deployment is deliberately revised with a trusted chain and shared/edge limiter.

The Docker image contains code and dependencies only; production Compose mounts the trained artifacts read-only at `/app/models`. Startup never downloads a dataset or retrains. Missing models yield unavailable readiness. See `../docs/DEPLOYMENT.md` for Docker, Caddy HTTPS, systemd and tunnel instructions.
