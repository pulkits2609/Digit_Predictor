"""Explicit re-evaluation tool; training already writes held-out metrics once."""
import json
import os
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL","2")
import numpy as np
import tensorflow as tf
from training.train import ROOT

if __name__ == "__main__":
    (_, _), (x, y) = tf.keras.datasets.mnist.load_data()
    model = tf.keras.models.load_model(ROOT / "models/neuralink.keras")
    values=model.evaluate(x.astype(np.float32)[...,None]/255,y,batch_size=128,verbose=0,return_dict=True)
    print(json.dumps(values,indent=2))
