# Trained artifacts

`neuralink.keras` contains genuinely trained TensorFlow/Keras weights and the best-validation checkpoint. Startup loads this file without training. `metadata.json` identifies the architecture and experiment; `history.json` contains per-epoch values; `metrics.json` contains the untouched test-set evaluation and per-class report. These JSON files are also exported into `frontend/public/model/` for offline insights.

The checked-in experiment used seed 42, 54,000 training images, 6,000 validation images, 8 epochs, batch size 128, Adam, mild geometric augmentation, and the best validation loss checkpoint. It achieved **99.24% test accuracy** and test loss **0.0227443** on 10,000 held-out MNIST images. This does not establish real-world canvas or photograph accuracy.

Run from `backend/`: `python -m training.train --epochs 8 --batch-size 128 --seed 42`. This downloads MNIST to the standard Keras cache. Run training before building frontend assets so generated JSON is included. Only run training offline from production API traffic; replace the model and matching metadata together, then restart the single API worker.

`training-curves.png`, `confusion-matrix.png`, and `samples.png` are generated plots. `samples/digit-N.png` contains an actual MNIST test example for each digit, enlarged for manual/API/browser smoke tests; they were never training data. Additional smoke predictions do not alter the held-out experiment results.
