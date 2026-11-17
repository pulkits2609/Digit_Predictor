import logging
from contextlib import asynccontextmanager
from time import perf_counter
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.core.config import Settings
from app.core.security import SecurityMiddleware
from app.ml.inference import ModelService
from app.ml.preprocessing import InputError, preprocess
from app.ml.visualization import feature_maps
from app.schemas.prediction import Prediction


def create_app(settings: Settings | None = None, service: ModelService | None = None) -> FastAPI:
    settings = settings or Settings()
    origins = settings.origins  # Validate even when no requests have arrived.
    logging.basicConfig(level=settings.log_level)
    model_service = service or ModelService(settings)

    @asynccontextmanager
    async def lifespan(app):
        await run_in_threadpool(model_service.load)
        app.state.model_service = model_service
        yield

    api = FastAPI(title="NeuralInk API", version="1.0.0", lifespan=lifespan, docs_url="/docs" if settings.app_env != "production" else None, redoc_url=None)
    api.add_middleware(SecurityMiddleware, settings=settings)
    # Outermost CORS also decorates middleware validation failures.
    api.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=False, allow_methods=["GET", "POST"], allow_headers=["Content-Type"])

    @api.exception_handler(StarletteHTTPException)
    async def http_error(request, exc):
        return JSONResponse({"error": {"code": f"http_{exc.status_code}", "message": str(exc.detail)}}, exc.status_code)

    @api.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        return JSONResponse({"error": {"code": "invalid_request", "message": "Provide one image using the file field."}}, 422)

    @api.exception_handler(Exception)
    async def unexpected_error(request, exc):
        logging.getLogger(__name__).exception("Request failed")
        return JSONResponse({"error": {"code": "internal_error", "message": "Prediction failed. Please try again."}}, 500)

    @api.get("/healthz")
    def health():
        return {"status": "ok"}

    @api.get("/readyz")
    def ready():
        if model_service.model is None:
            raise HTTPException(503, "The trained model is unavailable.")
        return {"status": "ready", "model_version": model_service.metadata["version"]}

    @api.get("/api/v1/model/info")
    def model_info():
        if model_service.model is None:
            raise HTTPException(503, "The trained model is unavailable.")
        return model_service.metadata

    async def process_upload(file: UploadFile):
        try:
            if model_service.model is None:
                raise HTTPException(503, "The trained model is unavailable. Please try again later.")
            if file.content_type not in {"image/png", "image/jpeg", "image/webp"}:
                raise HTTPException(415, "Use a PNG, JPEG, or WebP image.")
            data = await file.read(settings.upload_bytes + 1)
            if len(data) > settings.upload_bytes:
                raise HTTPException(413, f"Images must be {settings.max_upload_mb} MB or smaller.")
            try:
                return await run_in_threadpool(preprocess, data, settings.max_image_pixels)
            except InputError as exc:
                raise HTTPException(exc.status, str(exc)) from exc
        finally:
            await file.close()

    @api.post("/api/v1/predict", response_model=Prediction)
    async def predict(file: UploadFile = File(...)):
        started = perf_counter()
        image = await process_upload(file)
        return await run_in_threadpool(model_service.predict, image, started)

    @api.post("/api/v1/visualize")
    async def visualize(file: UploadFile = File(...)):
        image = await process_upload(file)
        return await run_in_threadpool(feature_maps, model_service, image)

    return api

app = create_app()
