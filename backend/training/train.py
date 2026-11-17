"""Train once, select using validation only, evaluate untouched test data once."""
import argparse
import json
import os
from pathlib import Path
from time import perf_counter
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
os.environ.setdefault("TF_NUM_INTRAOP_THREADS", "4")
os.environ.setdefault("TF_NUM_INTEROP_THREADS", "2")
import numpy as np
import tensorflow as tf
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from training.visualize import save_figures

ROOT = Path(__file__).resolve().parents[1]

def build_model(seed: int):
    inputs = tf.keras.Input(shape=(28, 28, 1))
    # Mild geometry augmentation is only active during training.
    x = tf.keras.layers.RandomRotation(0.035, fill_mode="constant", seed=seed)(inputs)
    x = tf.keras.layers.RandomTranslation(0.06, 0.06, fill_mode="constant", seed=seed+1)(x)
    x = tf.keras.layers.RandomZoom(0.06, fill_mode="constant", seed=seed+2)(x)
    x = tf.keras.layers.Conv2D(32, 3, activation="relu", name="conv1")(x)
    x = tf.keras.layers.MaxPooling2D(2)(x)
    x = tf.keras.layers.Conv2D(64, 3, activation="relu", name="conv2")(x)
    x = tf.keras.layers.MaxPooling2D(2)(x)
    x = tf.keras.layers.Flatten()(x)
    x = tf.keras.layers.Dense(128, activation="relu")(x)
    x = tf.keras.layers.Dropout(0.3, seed=seed)(x)
    outputs = tf.keras.layers.Dense(10, activation="softmax")(x)
    return tf.keras.Model(inputs, outputs, name="NeuralInk")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--epochs", type=int, default=8)
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    if args.epochs < 1 or args.batch_size < 1:
        parser.error("epochs and batch-size must be positive")
    tf.keras.utils.set_random_seed(args.seed)
    tf.config.experimental.enable_op_determinism()
    out = ROOT / "models"
    out.mkdir(exist_ok=True)
    (raw_train, labels), (raw_test, test_labels) = tf.keras.datasets.mnist.load_data()
    train_x, val_x, train_y, val_y = train_test_split(raw_train, labels, test_size=0.1, stratify=labels, random_state=args.seed)
    train_x = train_x.astype("float32")[..., None] / 255
    val_x = val_x.astype("float32")[..., None] / 255
    test_x = raw_test.astype("float32")[..., None] / 255
    options = tf.data.Options()
    options.threading.private_threadpool_size = 2
    def dataset(x,y,shuffle=False):
        ds=tf.data.Dataset.from_tensor_slices((x,y))
        if shuffle:
            ds=ds.shuffle(len(y),seed=args.seed)
        return ds.batch(args.batch_size).with_options(options).prefetch(1)
    model = build_model(args.seed)
    model.compile(optimizer=tf.keras.optimizers.Adam(0.001), loss="sparse_categorical_crossentropy", metrics=["accuracy"])
    model.summary()
    callbacks = [tf.keras.callbacks.EarlyStopping(monitor="val_loss", patience=3, restore_best_weights=True), tf.keras.callbacks.ModelCheckpoint(out / "neuralink.keras", monitor="val_loss", save_best_only=True), tf.keras.callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=2)]
    started = perf_counter()
    history = model.fit(dataset(train_x, train_y, True), validation_data=dataset(val_x, val_y), epochs=args.epochs, callbacks=callbacks, verbose=2, shuffle=False)
    duration = perf_counter()-started
    model = tf.keras.models.load_model(out / "neuralink.keras")
    test_loss, test_accuracy = model.evaluate(dataset(test_x, test_labels), verbose=0)
    probabilities = model.predict(dataset(test_x, test_labels), verbose=0)
    predictions = probabilities.argmax(axis=1)
    metrics = {"test_accuracy":float(test_accuracy), "test_loss":float(test_loss), "test_samples":len(test_labels), "confusion_matrix":confusion_matrix(test_labels, predictions).tolist(), "classification_report":classification_report(test_labels, predictions, output_dict=True), "evaluation":"untouched MNIST test split; best model selected using validation loss"}
    history_dict = {k:[float(v) for v in values] for k,values in history.history.items()}
    architecture = ["Input 28x28x1", "Training-only rotation/translation/zoom", "Conv2D 32, 3x3, ReLU", "MaxPooling2D 2x2", "Conv2D 64, 3x3, ReLU", "MaxPooling2D 2x2", "Flatten", "Dense 128, ReLU", "Dropout 0.3", "Dense 10, Softmax"]
    metadata = {"name":"NeuralInk", "version":"1.0.0", "dataset":"MNIST", "input_shape":[28,28,1], "classes":list(range(10)), "parameter_count":model.count_params(), "architecture":architecture, "tensorflow_version":tf.__version__, "seed":args.seed, "epochs_requested":args.epochs,"epochs_completed":len(history.history["loss"]), "best_epoch":int(np.argmin(history.history["val_loss"]))+1, "batch_size":args.batch_size,"training_samples":len(train_y),"validation_samples":len(val_y),"training_seconds":round(duration,3), "evaluation_metrics":{"test_accuracy":float(test_accuracy),"test_loss":float(test_loss)}, "limitations":"MNIST accuracy does not establish accuracy on photographs or browser handwriting. Softmax confidence is not calibrated correctness."}
    for name, content in [("metadata",metadata),("history",history_dict),("metrics",metrics)]:
        text=json.dumps(content,indent=2)
        (out/f"{name}.json").write_text(text,encoding="utf-8")
        public=ROOT.parent / "frontend/public/model"
        public.mkdir(parents=True,exist_ok=True)
        (public/f"{name}.json").write_text(text,encoding="utf-8")
    save_figures(out,raw_train,labels,history_dict,metrics["confusion_matrix"])
    # Genuine raw MNIST examples for repeatable API/browser smoke tests.
    from PIL import Image
    samples=out / "samples"
    samples.mkdir(exist_ok=True)
    for digit in range(10):
        i=int(np.where(test_labels==digit)[0][0])
        Image.fromarray(raw_test[i]).resize((280,280)).save(samples/f"digit-{digit}.png")
    print(json.dumps({"test_accuracy":test_accuracy,"test_loss":test_loss,"parameters":model.count_params(),"training_seconds":duration}))

if __name__ == "__main__":
    main()
