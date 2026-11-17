# NeuralInk viva guide

## 1. What is deep learning?

Deep learning trains neural networks with multiple layers to learn representations from examples. NeuralInk learns image features and digit classes from labeled MNIST images instead of using handwritten rules for the shape of each number.

## 2. What is an artificial neural network?

A network is a collection of parameterized layers. A neuron computes a weighted sum plus bias, often followed by a nonlinear activation. Training changes those weights to reduce prediction error.

## 3. How does a CNN differ from an MLP?

An MLP usually flattens the image immediately and connects every input to each hidden neuron. A CNN uses local filters shared across positions, preserving spatial relationships while using fewer parameters than a similarly sized fully connected image model. NeuralInk still uses dense layers after convolutional feature extraction.

## 4. What is convolution? What is a kernel?

A small learned kernel slides over an image and computes a weighted response at each position. For a 3×3 grayscale kernel, nine pixel values contribute to a response plus a bias. Multiple filters produce multiple feature maps. Deep-learning libraries commonly implement cross-correlation while calling the operation convolution.

## 5. What is feature extraction?

Earlier layers can respond to simple patterns such as edges; later layers combine these responses into more useful shapes. These features are learned from the training objective. We cannot claim a particular filter detects a particular shape without inspecting its activations.

## 6. What is max pooling?

Max pooling keeps the maximum response from each local region. A 2×2 pool with stride two reduces width and height by roughly half, lowers computation and gives limited tolerance to small position changes. It has no learned weights.

## 7. Why ReLU?

ReLU computes `max(0, x)`. It provides nonlinearity and is inexpensive. Without nonlinearities, stacked linear layers could collapse into a single linear transformation and would not learn complex decision boundaries.

## 8. What is softmax?

Softmax converts ten output logits into ten nonnegative scores summing to one: `exp(z_i) / sum(exp(z_j))`. The highest score selects the class. A 0.98 score is a model confidence value; it does not prove a 98% chance of correctness on a new photograph.

## 9. What is backpropagation?

Backpropagation uses the chain rule to calculate the gradient of loss with respect to each trainable parameter. The optimizer then updates parameters. The network performs a forward pass for scores and a backward pass for gradients during training; inference uses only a forward pass.

## 10. What is the loss function?

Sparse categorical cross-entropy is appropriate for one integer label per image. For the correct class `y`, loss is `-log(p_y)`. It strongly penalizes assigning low confidence to the true class. Accuracy counts correct argmax predictions, which is a different quantity.

## 11. Why Adam instead of plain gradient descent?

Adam tracks moving averages of gradients and squared gradients to adapt update sizes. It is a practical default for this CNN. It does not remove the need to choose a learning rate, validate training or guard against overfitting.

## 12. What is overfitting? How does dropout help?

Overfitting occurs when performance improves on training data but fails to generalize to held-out data. Dropout randomly removes a fraction of hidden activations during training, discouraging dependence on a few neurons. At inference it is disabled. Early stopping, augmentation and validation monitoring provide additional controls.

## 13. What is MNIST and why 28×28?

MNIST contains 60,000 training and 10,000 test grayscale digit images labeled 0–9. Each image is 28×28 pixels, which is compact enough for fast educational experiments. Browser drawings are larger and must be converted to the model's input format.

## 14. Why separate training, validation and testing?

Training fits weights. Validation chooses checkpoints and stopping time. Testing estimates final performance on data not used for those decisions. NeuralInk creates validation data from the original training set and leaves the provided test set untouched until final evaluation. Repeatedly choosing architectures from test scores would leak test information into development.

## 15. What does the model actually learn?

The trained artifact contains learned convolution and dense weights. The proposed network has 225,034 trainable parameters with valid convolutions. The actual artifact's metadata and `model.summary()` provide the authoritative count. Preprocessing heuristics are deterministic code, not learned CNN parameters.

## 16. How is a prediction generated?

Canvas pixels or an uploaded image are posted as one multipart file. FastAPI validates it, detects image polarity, crops the foreground, preserves aspect ratio, resizes and centers it on 28×28. The normalized `(1,28,28,1)` tensor enters the loaded CNN. The API returns the argmax digit, top three scores, all ten scores, processed preview and measured processing time.

## 17. Why is real handwriting harder than MNIST?

MNIST is a curated grayscale dataset with normalized size and placement. Photographs add lighting, paper texture, perspective, compression and background objects. Writers also differ in stroke style and thickness. A high MNIST score cannot be reported as browser or photograph accuracy. The processed preview helps explain failures.

## 18. What is a confusion matrix?

Rows represent true classes and columns predicted classes. The diagonal counts correct predictions; off-diagonal cells show confusions such as a true 4 predicted as 9. Always state the row/column convention. Precision measures how often predictions of a class are correct; recall measures how many examples of that class are found. F1 is their harmonic mean. Support is the number of true examples.

## 19. How are frontend and backend connected?

The React frontend uses a typed fetch client and a configured `VITE_API_BASE_URL`. FastAPI accepts `/api/v1/predict`. The browser requires the backend to allow the frontend's exact origin through CORS. Both public origins use HTTPS. The frontend contains no TensorFlow model or server secrets.

## 20. How is the backend deployed independently?

A Linux host runs one Uvicorn worker with one model loaded at startup. Caddy terminates HTTPS and proxies to the internal API. Docker Compose supplies restart behavior, read-only model mounting and health checks; systemd is the alternative. A secure outbound tunnel supports CGNAT without inbound port forwarding.

## 21. What is the difference between liveness and readiness?

Liveness says the process can respond. Readiness says the model is loaded and initialized for inference. `/healthz` may return success while `/readyz` returns 503 for a missing model. The UI must not invent a result during that failure.

## 22. What security and privacy controls matter here?

Validate MIME and decoded format, bound compressed bytes and decoded pixels, reject invalid/blank images, avoid permanent storage and return safe errors. Enforce CORS and reasonable rate limits, but explain that CORS is not authentication. Trust proxy headers only under an explicit deployment policy. Process-local limits do not coordinate multiple instances.

## 23. How does the project map to the syllabus?

Feedforward computation produces scores; backpropagation differentiates the loss; Adam applies gradient updates; dropout and augmentation provide regularization; convolution and pooling extract spatial features; the final layer performs multiclass image classification. The web application integrates these topics in Experiment 11's capstone, complementing the CNN practical.

## Demonstration checklist

1. Show `/readyz`, training artifacts and the saved model so the evaluator can distinguish real inference from a UI mock.
2. Draw one digit, predict and inspect all ten scores and the processed input.
3. Upload a single dark-on-white digit to demonstrate polarity handling through the same endpoint.
4. Clear or upload an invalid image and show the useful validation feedback.
5. Open Model Insights and explain validation curves, confusion matrix and per-class metrics using actual saved results.
6. Explain one failure case and the domain gap; avoid presenting a small live demo as a measured accuracy study.
