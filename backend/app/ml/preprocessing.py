"""The sole image-to-tensor pipeline for uploaded and canvas images."""
import base64
import io
import warnings
from dataclasses import dataclass
import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError

class InputError(ValueError):
    def __init__(self, message: str, status: int = 422):
        super().__init__(message)
        self.status = status

@dataclass
class ProcessedImage:
    tensor: np.ndarray
    preview: str


def preprocess(data: bytes, max_pixels: int = 12000000) -> ProcessedImage:
    if not data:
        raise InputError("The image file is empty.", 400)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            image = Image.open(io.BytesIO(data))
            if image.format not in {"PNG", "JPEG", "WEBP"}:
                raise InputError("Use a PNG, JPEG, or WebP image.", 415)
            if image.width * image.height > max_pixels or max(image.size) > 16000:
                raise InputError("Image dimensions are too large.", 413)
            if min(image.size) < 2 or max(image.size) / min(image.size) > 60:
                raise InputError("Crop the image around a single handwritten digit.")
            image.load()
            image = ImageOps.exif_transpose(image).convert("RGBA")
            # Transparent images are composited opposite their visible ink, preserving
            # both black transparent ink and white transparent canvas exports.
            rgba = np.asarray(image)
            visible = rgba[..., 3] > 127
            ink_level = float(np.median(rgba[..., :3][visible])) if visible.any() else 0
            background = (255, 255, 255, 255) if ink_level < 128 else (0, 0, 0, 255)
            base = Image.new("RGBA", image.size, background)
            base.alpha_composite(image)
            gray = np.asarray(base.convert("L"), dtype=np.float32)
    except InputError:
        raise
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise InputError("The image could not be decoded safely. Choose another image.", 400) from exc
    # Median perimeter is robust to a digit touching one border.
    edge = np.concatenate((gray[0], gray[-1], gray[:, 0], gray[:, -1]))
    background_level = float(np.median(edge))
    foreground = np.maximum(background_level - gray, 0) if background_level > 127 else np.maximum(gray - background_level, 0)
    peak = float(foreground.max())
    if peak < 8:
        raise InputError("No visible digit found. Draw one digit with contrasting strokes.")
    foreground = foreground / peak
    mask = foreground > max(0.08, 8 / peak)
    ys, xs = np.where(mask)
    if len(xs) < 5:
        raise InputError("The mark is too small. Write a complete digit.")
    crop = foreground[ys.min():ys.max()+1, xs.min():xs.max()+1]
    if min(crop.shape) < 2:
        raise InputError("Write a complete digit, rather than a single thin mark.")
    scale = 20 / max(crop.shape)
    size = (max(1, round(crop.shape[1] * scale)), max(1, round(crop.shape[0] * scale)))
    resized = Image.fromarray(np.uint8(np.clip(crop, 0, 1) * 255)).resize(size, Image.Resampling.LANCZOS)
    canvas = Image.new("L", (28, 28), 0)
    canvas.paste(resized, ((28-size[0])//2, (28-size[1])//2))
    pixels = np.asarray(canvas, dtype=np.float32) / 255
    y_grid, x_grid = np.indices((28, 28))
    mass = float(pixels.sum())
    if mass < 1:
        raise InputError("The digit is too faint to process.")
    dx = round(13.5 - float((pixels * x_grid).sum() / mass))
    dy = round(13.5 - float((pixels * y_grid).sum() / mass))
    shifted = Image.new("L", (28, 28), 0)
    shifted.paste(canvas, (dx, dy))
    tensor = (np.asarray(shifted, dtype=np.float32) / 255).reshape(1, 28, 28, 1)
    buffer = io.BytesIO()
    shifted.save(buffer, format="PNG")
    return ProcessedImage(tensor, "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode())
