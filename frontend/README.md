# Frontend deployment on Vercel

The frontend and backend are separate folders. Deploy this frontend independently.

Vercel settings:
- Root Directory: frontend
- Framework: Vite
- Install command: npm ci
- Build command: npm run build
- Output directory: dist
- Environment variable: API=https://your-backend-domain

API is the public backend base URL, without /api/v1/predict. Set it in Vercel Settings > Environment Variables and redeploy after changing it. It is a public URL, never a secret. Only API is explicitly exposed from unprefixed build variables. Existing VITE_API_BASE_URL remains a compatibility fallback.

For local development, create .env.local with API=http://127.0.0.1:8000 and run npm ci then npm run dev. Production requires an HTTPS API URL. Backend CORS_ORIGINS must allow the exact Vercel frontend origin.

The backend is deployed separately using the instructions in ../docs/DEPLOYMENT.md. Model weights are supplied in backend/models/neuralink.keras; no training occurs during startup.

Checks: npm test, npm run typecheck, npm run lint, npm run build.
