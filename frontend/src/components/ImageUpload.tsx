import { useEffect, useRef, useState } from 'react';
import { ImagePlus, Upload, X } from 'lucide-react';
import { maxUploadMB, validateUpload } from '../lib/api';

export function ImageUpload({ file, onChange }: { file: File | null; onChange: (file: File | null) => void }) {
  const input = useRef<HTMLInputElement>(null); const [error, setError] = useState(''); const [preview, setPreview] = useState(''); const [dragging, setDragging] = useState(false);
  useEffect(() => { if (!file) { setPreview(''); return; } const url = URL.createObjectURL(file); setPreview(url); return () => URL.revokeObjectURL(url); }, [file]);
  const choose = (candidate?: File) => {
    if (!candidate) return;
    const message = validateUpload(candidate); setError(message || '');
    if (!message) onChange(candidate);
    if (input.current) input.current.value = '';
  };
  return <div className="upload-container">
    <input ref={input} aria-label="Upload digit image" className="sr-only" type="file" accept="image/png,image/jpeg,image/webp" onChange={event => choose(event.target.files?.[0])}/>
    <div className={`upload-zone ${dragging ? 'dragging' : ''}`} onDragOver={event => { event.preventDefault(); setDragging(true); }} onDragLeave={() => setDragging(false)} onDrop={event => { event.preventDefault(); setDragging(false); choose(event.dataTransfer.files[0]); }}>
      {preview ? <><img className="upload-preview" src={preview} alt="Selected handwritten digit"/><button className="remove-image icon-button" aria-label="Remove image" title="Remove image" onClick={() => { onChange(null); setError(''); }}><X size={18}/></button></> : <><ImagePlus size={24} aria-hidden="true"/><h3>Upload a digit</h3><p>Drop an image here or choose a file.</p><button type="button" className="secondary-button" onClick={() => input.current?.click()}><Upload size={16}/> Browse images</button><small>PNG, JPG, WebP · up to {maxUploadMB} MB</small></>}
    </div>
    {file && <div className="file-line"><span title={file.name}>{file.name}</span><button className="text-button" onClick={() => input.current?.click()}>Replace image</button></div>}
    {error && <p className="error-message" role="alert">{error}</p>}
    <p className="input-help">Use one digit on a plain background, cropped close.</p>
  </div>;
}
