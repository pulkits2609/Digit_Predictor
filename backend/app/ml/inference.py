import json
import logging
import os
from threading import Lock
from time import perf_counter
from typing import Any
import numpy as np
from app.core.config import Settings
from app.ml.preprocessing import ProcessedImage

logger = logging.getLogger(__name__)

class ModelService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.model: Any = None
        self.metadata: dict = {}
        self.lock = Lock()

    def load(self) -> None:
        if not self.settings.model_path.is_file():
            logger.error("Model unavailable; train or mount the saved model before inference")
            return
        try:
            os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
            os.environ.setdefault("TF_NUM_INTRAOP_THREADS", "2")
            os.environ.setdefault("TF_NUM_INTEROP_THREADS", "2")
            import tensorflow as tf
            model = tf.keras.models.load_model(self.settings.model_path, compile=False)
            if model.input_shape != (None, 28, 28, 1) or model.output_shape != (None, 10):
                raise ValueError("Incompatible model shape")
            model(np.zeros((1, 28, 28, 1), dtype=np.float32), training=False)
            metadata = json.loads(self.settings.model_metadata_path.read_text(encoding="utf-8"))
            self.metadata = metadata
            self.model = model
        except Exception:
            logger.exception("Unable to load the configured model")
            self.model = None

    def predict(self, image: ProcessedImage, started: float) -> dict:
        with self.lock:
            probabilities = np.asarray(self.model(image.tensor, training=False))[0].astype(float)
        if probabilities.shape != (10,) or not np.isfinite(probabilities).all() or (probabilities < 0).any() or not np.isclose(probabilities.sum(), 1, atol=1e-4):
            raise RuntimeError("Invalid model output")
        ranks = np.argsort(-probabilities, kind="stable")[:3]
        digit = int(ranks[0])
        return {
            "prediction": digit,
            "confidence": float(probabilities[digit]),
            "top_predictions": [{"digit": int(i), "confidence": float(probabilities[i])} for i in ranks],
            "probabilities": probabilities.tolist(),
            "processing_time_ms": round((perf_counter()-started)*1000, 3),
            "model_version": self.metadata["version"],
            "is_uncertain": bool(probabilities[digit] < self.settings.uncertainty_threshold),
            "processed_image": image.preview,
        }
