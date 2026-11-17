# Deployment and operations

The frontend is static and deploys to Vercel. The Python API runs on a separate Linux x86-64 machine. No training occurs during API startup. The backend requires an existing `backend/models/neuralink.keras` and matching metadata. Run all commands from the repository root unless a `cd` is shown. Placeholder domains must be replaced before production use.

## Supported runtime

Use Python 3.11, TensorFlow 2.18.1 CPU and the pinned backend requirements. Linux x86-64 is the deployment target; Windows x86-64 Python 3.11 supports local CPU development. Modern CPUs with TensorFlow's required instruction support are necessary. ARM, Raspberry Pi, GPU and macOS configurations are not validated by this project. Use Node.js 22 LTS for the frontend. Docker Compose v2 is the preferred Linux deployment path. Ubuntu 22.04/24.04 is suitable for Docker; for native installation supply Python 3.11 explicitly because the distribution's default Python may differ.

## Local development on Windows PowerShell

```powershell
cd 'C:\Users\Pulkit Sharma\IMP STUFF\Notes 4th Year\deeplearning\exp11\backend'
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -m training.train --epochs 8 --batch-size 128 --seed 42
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1 --no-proxy-headers
```

In a second terminal:

```powershell
cd 'C:\Users\Pulkit Sharma\IMP STUFF\Notes 4th Year\deeplearning\exp11\frontend'
npm ci
Copy-Item .env.example .env
# Set API=http://127.0.0.1:8000 in this local .env.
npm run dev -- --host 127.0.0.1
```

The default Vite origin is `http://127.0.0.1:5173`. Add this exact origin to backend `CORS_ORIGINS`; `localhost` and `127.0.0.1` are different origins. Restart the backend after environment changes and restart Vite after changing `.env`. Existing trained artifacts can be used instead of retraining. Linux equivalents use `python3.11` and `.venv/bin/python`.

## Training and artifacts

From `backend`, run `.venv/bin/python -m training.train --epochs 8 --batch-size 128 --seed 42` (Windows: `.venv\Scripts\python.exe`). The training script downloads MNIST, splits only the 60,000 training images into training/validation, checkpoints the best validation model and evaluates the untouched 10,000-image test set. It exports the model, history, metadata, metrics and educational plots. Preserve matching artifacts together. JSON artifacts copied to `frontend/public/model/` let Model Insights work without the API.

Model weights are excluded from Git by default. Copy the trained model to the backend server through a trusted channel; do not publicly expose the model folder. Keep a backup of the prior matching model and metadata before updating. Do not overwrite files while inference is running: stop the backend, replace the full artifact set, restart, check readiness and make a real prediction. Redeploy the frontend if bundled metrics change.

The completed seed-42 run used 8 epochs and achieved 99.24% accuracy and 0.02274431 cross-entropy on 10,000 held-out MNIST test samples. See PROJECT_REPORT.md and the generated artifacts for full measurements. These results do not measure browser or photograph accuracy.

## Vercel frontend

1. Push source and the generated JSON insight artifacts to a GitHub repository.
2. Import it into Vercel and set **Root Directory** to `frontend` and framework to **Vite**.
3. Set install command to `npm ci`, build command to `npm run build`, output directory to `dist`, Node.js to 22.x.
4. Set `API=https://api.your-domain.example` for Production; configure Preview separately if needed. Set optional frontend environment settings according to `frontend/.env.example`.
5. Deploy. No backend access is required for the frontend build.
6. Set the backend CORS allowlist to the exact deployed frontend origin, without a trailing slash or path. Redeploy/restart the API.
7. Check `https://api.your-domain.example/readyz`, draw/upload one digit from the deployed frontend, and inspect that its network request uses the HTTPS backend origin.

`VITE_*` values are public build configuration. Never put secrets there. Changing the API URL requires changing the Vercel environment value and redeploying; source edits are unnecessary. The Vercel routing configuration preserves static assets and supports the application's navigation. A successful build alone does not prove live API connectivity. See [Vercel's Vite guide](https://vercel.com/docs/frameworks/frontend/vite).

## Method A: Docker Compose and Caddy

Install Docker Engine and Compose v2 following the [official Ubuntu instructions](https://docs.docker.com/engine/install/ubuntu/). Copy this repository to the machine and place the trained artifacts in `backend/models/`. Point the API domain's DNS A record to the machine's public address; use AAAA only when IPv6 actually reaches it. Allow inbound TCP 80/443 (and optionally UDP 443 for HTTP/3) through host/cloud firewalls. Keep SSH restricted appropriately.

```bash
cp deploy/.env.example deploy/.env
# Edit deploy/.env: API_DOMAIN, TLS_EMAIL, CORS_ORIGINS.
docker compose --env-file deploy/.env -f deploy/docker-compose.yml config --quiet
docker compose --env-file deploy/.env -f deploy/docker-compose.yml build
docker compose --env-file deploy/.env -f deploy/docker-compose.yml up -d
docker compose --env-file deploy/.env -f deploy/docker-compose.yml ps
docker compose --env-file deploy/.env -f deploy/docker-compose.yml logs --tail=100 backend caddy
python3 deploy/scripts/check-readiness.py https://api.your-domain.example
```

Only Caddy publishes host ports. Backend models are mounted read-only. One Uvicorn worker holds one model. The backend has a 2 GiB memory limit and 2 CPU allocation; adjust after measuring your host. Readiness must pass before Compose starts Caddy. Caddy manages certificates automatically and persists its certificate data in named volumes. Do not delete those volumes during ordinary updates. The Compose health check detects readiness loss; Docker restart policies restart exited containers, but do not automatically restart a running unhealthy process. Investigate failed readiness rather than masking missing artifacts with a restart loop.

```bash
# Restart; use up -d --build for changes to images or environment.
docker compose --env-file deploy/.env -f deploy/docker-compose.yml restart backend
# Stop while retaining containers/volumes, then resume.
docker compose --env-file deploy/.env -f deploy/docker-compose.yml stop
docker compose --env-file deploy/.env -f deploy/docker-compose.yml start
# Update source after reviewing it, then rebuild/recreate.
git pull --ff-only
docker compose --env-file deploy/.env -f deploy/docker-compose.yml up -d --build
# Shut down containers/network and retain certificate volumes.
docker compose --env-file deploy/.env -f deploy/docker-compose.yml down
```

If startup fails, inspect backend logs, ensure both model and metadata are readable by the container's non-root user, verify environment validation, then recreate with `up -d --build`. Check certificates in Caddy logs when DNS/TLS fails. Do not disable TLS verification. See [Compose readiness ordering](https://docs.docker.com/compose/how-tos/startup-order/) and [Caddy request limits](https://caddyserver.com/docs/caddyfile/directives/request_body).

## Method B: Python virtual environment and systemd

Supply Python 3.11 through an approved package source or build compatible with your host. Copy the repository to `/opt/neuralink`, then run:

```bash
sudo useradd --system --home-dir /opt/neuralink --shell /usr/sbin/nologin neuralink
sudo python3.11 -m venv /opt/neuralink/backend/.venv
sudo /opt/neuralink/backend/.venv/bin/python -m pip install -r /opt/neuralink/backend/requirements.txt
sudo chown -R root:neuralink /opt/neuralink
sudo chmod -R g+rX /opt/neuralink
sudo install -d -m 750 -o root -g neuralink /etc/neuralink
sudo install -m 640 -o root -g neuralink /opt/neuralink/deploy/systemd/backend.env.example /etc/neuralink/backend.env
# Edit /etc/neuralink/backend.env with real origins and matching model paths.
sudo install -m 644 /opt/neuralink/deploy/systemd/neuralink.service /etc/systemd/system/neuralink.service
sudo systemctl daemon-reload
sudo systemctl enable --now neuralink
sudo systemctl status neuralink --no-pager
sudo journalctl -u neuralink -n 100 --no-pager
curl --fail http://127.0.0.1:8000/readyz
```

Install Caddy using its [official Linux package instructions](https://caddyserver.com/docs/install). Copy `deploy/Caddyfile` to `/etc/caddy/Caddyfile`; either replace its environment placeholders with the real domain/email/upstream or configure them with `sudo systemctl edit caddy`:

```ini
[Service]
Environment=API_DOMAIN=api.your-domain.example
Environment=TLS_EMAIL=admin@your-domain.example
Environment=API_UPSTREAM=127.0.0.1:8000
Environment=MAX_REQUEST_BODY=6MB
```

Then run `sudo systemctl daemon-reload` and `sudo systemctl restart caddy`. Check `sudo journalctl -u caddy -n 100 --no-pager` and verify public readiness. Caddy's admin API is disabled in this configuration, so use service restart after configuration changes. Uvicorn binds only loopback and runs as a dedicated unprivileged account. Use `sudo systemctl restart neuralink` after artifact updates and `sudo systemctl stop neuralink` before replacement.

## Behind NAT or CGNAT: outbound tunnel

A named Cloudflare Tunnel is an alternative to inbound Caddy. It requires a Cloudflare account and a domain managed there; provider availability and terms apply. Keep systemd Uvicorn bound to `127.0.0.1`. Install `cloudflared` from its [official documentation](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/local-management/create-local-tunnel/), then:

```bash
cloudflared tunnel login
cloudflared tunnel create neuralink
cloudflared tunnel route dns neuralink api.your-domain.example
# Install deploy/tunnel.example.yml as /etc/cloudflared/config.yml.
# Replace UUID/domain and copy the generated UUID.json to the referenced path.
# Restrict credential ownership and file modes to the cloudflared service account.
cloudflared --config /etc/cloudflared/config.yml tunnel ingress validate
sudo cloudflared --config /etc/cloudflared/config.yml service install
sudo systemctl enable --now cloudflared
```

Cloudflare provides the public HTTPS hostname and the agent initiates outbound connections; router port forwarding is unnecessary. The ingress file exposes only the selected hostname and ends with a 404 catch-all. Keep tunnel credentials outside Git. Do not run the public Caddy listener for this method. Set Vercel's API URL and backend CORS origins as above. If access policies are applied, ensure they permit this public demo's browser requests and CORS preflights; interactive login gates are not automatically compatible with cross-origin fetches.

## Configuration and operational boundaries

| Variable | Purpose |
| --- | --- |
| `API` | Public API origin compiled into frontend |
| `VITE_MAX_UPLOAD_MB` | Frontend upload-size guidance/validation; align with backend |
| `VITE_GITHUB_URL` | Optional repository navigation link |
| `APP_ENV` | Runtime environment, `production` on server |
| `CORS_ORIGINS` | Comma-separated exact allowed frontend origins |
| `MODEL_PATH`, `MODEL_METADATA_PATH` | Matching saved model/metadata paths |
| `MAX_UPLOAD_MB` | Image byte limit, default 5 MiB |
| `MAX_IMAGE_PIXELS` | Decoded image safety limit, default 12,000,000 |
| `RATE_LIMIT_ENABLED`, `RATE_LIMIT_PER_MINUTE` | Process-local prediction limiter |
| `UNCERTAINTY_THRESHOLD` | Softmax threshold heuristic, default 0.7 |
| `LOG_LEVEL` | Server logging verbosity |
| `API_DOMAIN`, `TLS_EMAIL` | Caddy hostname and ACME account contact |
| `MAX_REQUEST_BODY` | Proxy body bound including multipart overhead |

CORS is a browser-origin policy, not authentication. Do not combine wildcard origins with credentials. In-memory rate limits reset at restart and do not coordinate multiple instances. With proxy headers disabled, the limit is shared by requests arriving through the proxy, which is conservative for a small public demo. Do not trust arbitrary `X-Forwarded-For` or `X-Real-IP` headers. Scaling needs an explicitly trusted proxy chain and a shared limiter or provider edge rate limits; stock Caddy does not include a rate-limit directive. Images are decoded in memory, inferred and discarded; raw image data is not intentionally persisted or logged by the app. Your proxy/provider may maintain connection logs under its own policy.

## Troubleshooting

- **503 readiness:** model missing, incompatible TensorFlow serialization, invalid metadata, or startup load failure. Inspect private logs and restore a matching artifact set; liveness does not prove inference readiness.
- **Browser fetch error:** confirm public HTTPS readiness, exact CORS origin, API environment value and Vercel redeployment. Never work around mixed content by disabling browser security.
- **413:** image exceeds application limit or multipart body exceeds the proxy limit. Keep proxy limit slightly larger than file limit and update frontend guidance when changing it.
- **429:** wait for the process-local window or review edge limits; multiple clients may share one proxy bucket.
- **Uncertain/wrong digit:** inspect the 28×28 input; use one centered, high-contrast digit. MNIST accuracy does not establish photo accuracy.
- **Tunnel 502:** confirm local origin `/readyz`, service binding and tunnel ingress configuration.

Public deployment requires a real server, DNS, TLS validation and the user's Vercel/provider account. These files prepare deployment; they do not constitute proof that a public deployment has occurred.
