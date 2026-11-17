import { motion, useReducedMotion } from 'motion/react';
import type { Prediction } from '../lib/api';

export function PredictionResults({ result, loading }: { result: Prediction | null; loading: boolean }) {
  const reduceMotion = useReducedMotion();
  return <section className="panel result-panel" aria-labelledby="prediction-title" aria-busy={loading}>
    <div className="panel-heading"><h2 id="prediction-title">Prediction</h2></div>
    <div className={`result-body ${!result ? 'empty' : ''}`} aria-live="polite" aria-atomic="true">
      {!result ? <><h3>{loading ? 'Recognizing digit…' : 'No prediction yet'}</h3><p>{loading ? 'The neural network is processing your image.' : 'Draw or upload a digit to get started.'}</p></> :
        <motion.div initial={reduceMotion ? false : { opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: .15 }} className="prediction-content">
          <div className="prediction-main">
            <div><span className="result-label">Recognized digit</span><div className="predicted-digit">{result.prediction}</div></div>
            <div className="confidence-block"><span className="result-label">Confidence</span><span className="confidence"><span>{(result.confidence * 100).toFixed(1)}</span><small>%</small></span></div>
          </div>
          {result.is_uncertain && <p className="uncertainty" role="status">The model is uncertain. Try writing the digit more clearly.</p>}
          <div className="result-section-heading"><h3>Confidence by digit</h3></div>
          <div className="probability-chart" aria-label="Probability distribution across digits zero to nine">
            {result.probabilities.map((value, digit) => <div key={digit} className={digit === result.prediction ? 'winner' : ''} title={`Digit ${digit}: ${(value * 100).toFixed(2)}%`}>
              <span className="bar-value">{value > .02 ? `${(value * 100).toFixed(0)}%` : ''}</span>
              <div className="bar-track"><i style={{ height: `${value * 100}%` }} /></div>
              <span className="chart-digit">{digit}</span><span className="sr-only">{(value * 100).toFixed(2)} percent</span>
            </div>)}
          </div>
          <p className="top-predictions">Top matches: {result.top_predictions.map(item => `${item.digit} (${(item.confidence * 100).toFixed(1)}%)`).join(' · ')}</p>
          <div className="processed-row">
            <img src={result.processed_image} alt="Actual preprocessed 28 by 28 grayscale CNN input" />
            <div><strong>Model input</strong><span>28 × 28 grayscale</span></div>
            <span className="time">Inference: <span>{result.processing_time_ms.toFixed(1)} ms</span></span>
          </div>
          <div className="prediction-explanation" id="how-it-works">
            <h3>How it reached this result</h3>
            <p>Your image was cropped, centered, and resized to 28 × 28 pixels. The CNN compared learned stroke patterns across digits 0–9 and gave <strong>{result.prediction}</strong> the highest score.</p>
          </div>
          <p className="confidence-note">Confidence is the model’s score, not a guarantee of correctness.</p>
        </motion.div>}
    </div>
  </section>;
}
