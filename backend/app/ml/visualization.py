"""Render real intermediate activations only on explicit request."""
import base64
import io
import numpy as np
from PIL import Image


def feature_maps(service, image):
    import tensorflow as tf
    layers = [service.model.get_layer(name) for name in ("conv1", "conv2")]
    with service.lock:
        intermediate = tf.keras.Model(service.model.input, [layer.output for layer in layers])
        activations = intermediate(image.tensor, training=False)
    result = []
    for layer, values in zip(layers, activations):
        array = np.asarray(values)[0]
        images = []
        for i in range(min(8, array.shape[-1])):
            channel = array[..., i]
            low, high = float(channel.min()), float(channel.max())
            normalized = (channel - low) / (high - low) if high > low else np.zeros_like(channel)
            buffer = io.BytesIO()
            Image.fromarray(np.uint8(normalized * 255)).save(buffer, format="PNG")
            images.append("data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode())
        result.append({"layer": layer.name, "images": images})
    return {"processed_image": image.preview, "feature_maps": result}
