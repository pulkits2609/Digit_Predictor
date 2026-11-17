import { useCallback, useEffect, useRef, useState } from 'react';
import { Github, ImagePlus, LoaderCircle, PenLine, RefreshCw } from 'lucide-react';
import { DrawingCanvas } from './components/DrawingCanvas';
import type { DrawingHandle } from './components/DrawingCanvas';
import { ImageUpload } from './components/ImageUpload';
import { PredictionResults } from './components/PredictionResults';
import { ModelInsights } from './components/ModelInsights';
import { FeatureMaps } from './components/FeatureMaps';
import { checkReadiness, predict } from './lib/api';
import type { Prediction } from './lib/api';
import './insights.css';

export default function App() {
  const [mode, setMode] = useState<'draw' | 'upload'>('draw');
  const [hasInk, setHasInk] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<Prediction | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [submittedImage, setSubmittedImage] = useState<Blob | null>(null);
  const [online, setOnline] = useState<boolean | null>(null);
  const [checking, setChecking] = useState(false);
  // Keep the existing insights location available without adding it to the workspace.
  const [showInsights, setShowInsights] = useState(window.location.hash === '#model-insights');
  const drawing = useRef<DrawingHandle>(null);
  const request = useRef<AbortController | null>(null);
  const revision = useRef(0);
  const inFlight = useRef(false);

  const refresh = useCallback(async (signal: AbortSignal) => {
    setChecking(true);
    const ready = await checkReadiness(signal);
    if (!signal.aborted) {
      setOnline(ready);
      setChecking(false);
    }
  }, []);
  useEffect(() => {
    const controller = new AbortController();
    void refresh(controller.signal);
    return () => controller.abort();
  }, [refresh]);
  useEffect(() => () => request.current?.abort(), []);
  useEffect(() => {
    const navigate = () => setShowInsights(window.location.hash === '#model-insights');
    window.addEventListener('hashchange', navigate);
    return () => window.removeEventListener('hashchange', navigate);
  }, []);

  const invalidate = useCallback(() => {
    revision.current++;
    request.current?.abort();
    inFlight.current = false;
    setLoading(false);
    setResult(null);
    setSubmittedImage(null);
    setError('');
  }, []);
  const canvasChanged = useCallback((ink: boolean) => {
    invalidate();
    setHasInk(ink);
  }, [invalidate]);

  const submit = async () => {
    if (inFlight.current || (mode === 'draw' ? !hasInk : !file)) return;
    inFlight.current = true;
    setLoading(true);
    setError('');
    const version = revision.current;
    const controller = new AbortController();
    request.current = controller;
    try {
      const image = mode === 'draw' ? await drawing.current!.toBlob() : file!;
      if (controller.signal.aborted) return;
      const response = await predict(image, controller.signal);
      if (version === revision.current) {
        setResult(response);
        setSubmittedImage(image);
        setOnline(true);
      }
    } catch (error) {
      if (version === revision.current && !controller.signal.aborted) {
        setError(error instanceof Error ? error.message : 'Prediction failed. Please try again.');
        setResult(null);
      }
    } finally {
      if (version === revision.current) {
        setLoading(false);
        inFlight.current = false;
      }
    }
  };
  const changeMode = (next: 'draw' | 'upload') => {
    if (mode === next) return;
    invalidate();
    setMode(next);
  };
  const github = import.meta.env.VITE_GITHUB_URL;

  return <div className="app-shell">
    <header className="site-header">
      <span aria-hidden="true" />
      <nav aria-label="Main navigation">
        <a className={!showInsights ? 'nav-active' : undefined} href="#workspace" aria-current={!showInsights ? 'page' : undefined}>Workspace</a>
        {github && <a className="icon-button" href={github} target="_blank" rel="noreferrer" aria-label="Project on GitHub" title="Project on GitHub"><Github size={18} /></a>}
      </nav>
    </header>
    <main>
      <div hidden={showInsights}>
        <section className="page-intro" id="workspace" aria-labelledby="workspace-title">
          <div className="intro-copy"><h1 id="workspace-title">Handwritten Digit Recognition</h1><p>Draw a digit or upload an image to see what the neural network predicts.</p></div>
          <button className="connection-status" onClick={() => void refresh(new AbortController().signal)} aria-label="Check recognition server connection" title="Check backend readiness" disabled={checking}>
            <RefreshCw size={14} className={checking ? 'spin' : undefined} aria-hidden="true" />
            {checking ? 'Checking server' : online ? 'Model ready' : online === false ? 'Server unavailable' : 'Connecting'}
          </button>
        </section>
        <div className="workspace-grid">
          <section className="panel input-panel" aria-labelledby="input-title">
            <div className="panel-heading"><h2 id="input-title">Input</h2></div>
            <div className="mode-tabs" role="tablist" aria-label="Input method">
              <button role="tab" id="draw-tab" aria-label="Draw a digit" aria-selected={mode === 'draw'} aria-controls="draw-panel" onClick={() => changeMode('draw')}><PenLine size={16} aria-hidden="true" />Draw</button>
              <button role="tab" id="upload-tab" aria-label="Upload an image" aria-selected={mode === 'upload'} aria-controls="upload-panel" onClick={() => changeMode('upload')}><ImagePlus size={16} aria-hidden="true" />Upload</button>
            </div>
            <div className="input-content">
              <div id="draw-panel" role="tabpanel" aria-labelledby="draw-tab" hidden={mode !== 'draw'}><DrawingCanvas ref={drawing} onChange={canvasChanged} /></div>
              <div id="upload-panel" role="tabpanel" aria-labelledby="upload-tab" hidden={mode !== 'upload'}><ImageUpload file={file} onChange={next => { invalidate(); setFile(next); }} /></div>
              <button className="predict-button" disabled={loading || (mode === 'draw' ? !hasInk : !file)} onClick={() => void submit()}>
                {loading && <LoaderCircle size={18} className="spin" aria-hidden="true" />}{loading ? 'Recognizing your digit…' : 'Recognize digit'}
              </button>
              {error && <div className="error-message" role="alert">{error} <button className="text-button" onClick={() => void submit()}>Try again</button></div>}
              <p className="privacy-note">Images are processed on the server and discarded.</p>
            </div>
          </section>
          <PredictionResults result={result} loading={loading} />
        </div>
        {submittedImage && result && <FeatureMaps key={revision.current} image={submittedImage} />}
      </div>
      {showInsights && <ModelInsights />}
    </main>
  </div>;
}
