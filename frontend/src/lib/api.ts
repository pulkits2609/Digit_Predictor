export interface Prediction {
  prediction: number; confidence: number;
  top_predictions: { digit: number; confidence: number }[];
  probabilities: number[]; processing_time_ms: number; model_version: string;
  is_uncertain: boolean; processed_image: string;
}

export class ApiError extends Error {}

function baseUrl() {
  const value = (import.meta.env.API || import.meta.env.VITE_API_BASE_URL)?.replace(/\/$/, '');
  if (!value) throw new ApiError('The recognition server is not configured. Set API in your Vercel environment variables and redeploy.');
  if (import.meta.env.PROD && !value.startsWith('https://')) throw new ApiError('The production recognition server must use HTTPS.');
  return value;
}

async function imageRequest<T>(path: string, file: Blob, signal: AbortSignal, timeoutMs: number): Promise<T> {
  const controller = new AbortController();
  let timedOut = false;
  const cancel = () => controller.abort();
  signal.addEventListener('abort', cancel, { once: true });
  if (signal.aborted) controller.abort();
  const timer = setTimeout(() => { timedOut = true; controller.abort(); }, timeoutMs);
  try {
    const body = new FormData(); body.append('file', file, file instanceof File ? file.name : 'drawing.png');
    const response = await fetch(`${baseUrl()}/api/v1/${path}`, { method: 'POST', body, signal: controller.signal });
    const data = await response.json().catch(() => null);
    if (!response.ok) {
      const message = data?.error?.message ?? data?.detail;
      throw new ApiError(typeof message === 'string' ? message : response.status === 503 ? 'The model is not ready. Try again in a moment.' : 'The server could not process this image. Try a clear, single digit.');
    }
    return data as T;
  } catch (error) {
    if (timedOut) throw new ApiError('The prediction timed out. Your input is safe; please try again.');
    if (signal.aborted) throw new DOMException('Cancelled', 'AbortError');
    if (error instanceof ApiError) throw error;
    throw new ApiError('Cannot reach the recognition server. Check your connection and try again.');
  } finally { clearTimeout(timer); signal.removeEventListener('abort', cancel); }
}

export async function predict(file: Blob, signal: AbortSignal, timeoutMs = 20000): Promise<Prediction> {
  const data = await imageRequest<Prediction>('predict', file, signal, timeoutMs);
  if (!Array.isArray(data?.probabilities) || data.probabilities.length !== 10 || data.probabilities.some(value => !Number.isFinite(value) || value < 0 || value > 1)
    || !Number.isInteger(data.prediction) || data.prediction < 0 || data.prediction > 9 || !Number.isFinite(data.confidence)
    || !Number.isFinite(data.processing_time_ms) || !Array.isArray(data.top_predictions) || data.top_predictions.length !== 3
    || typeof data.processed_image !== 'string' || !data.processed_image.startsWith('data:image/png;base64,')) throw new ApiError('The server returned an invalid prediction. Please try again.');
  return data;
}

export interface FeatureMaps { processed_image: string; feature_maps: {layer: string;images:string[]}[] }
export function visualize(file:Blob, signal:AbortSignal):Promise<FeatureMaps> {return imageRequest<FeatureMaps>('visualize',file,signal,20000);}

export async function checkReadiness(signal: AbortSignal): Promise<boolean> {
  try {
    const response = await fetch(`${baseUrl()}/readyz`, { signal: AbortSignal.any([signal, AbortSignal.timeout(5000)]) });
    return response.ok;
  } catch { return false; }
}

export const maxUploadMB = Number(import.meta.env.VITE_MAX_UPLOAD_MB || 5);
export function validateUpload(file: File): string | null {
  if (!['image/png', 'image/jpeg', 'image/webp'].includes(file.type)) return 'Choose a PNG, JPEG, or WebP image.';
  if (!file.size) return 'This file is empty. Choose another image.';
  if (file.size > maxUploadMB * 1024 * 1024) return `Choose an image smaller than ${maxUploadMB} MB.`;
  return null;
}
