import { forwardRef, useCallback, useEffect, useImperativeHandle, useRef, useState } from 'react';
import type { PointerEvent as ReactPointerEvent } from 'react';
import { Eraser, PenLine, Redo2, Trash2, Undo2 } from 'lucide-react';

type Point = { x: number; y: number };
type Stroke = { points: Point[]; width: number; erase: boolean };
export interface DrawingHandle { toBlob: () => Promise<Blob> }
interface Props { onChange: (hasInk: boolean) => void }

export const DrawingCanvas = forwardRef<DrawingHandle, Props>(function DrawingCanvas({ onChange }, ref) {
  const canvas = useRef<HTMLCanvasElement>(null);
  const strokes = useRef<Stroke[]>([]); const future = useRef<Stroke[]>([]);
  const active = useRef<Stroke | null>(null); const pointer = useRef<number | null>(null);
  const [width, setWidth] = useState(18); const [erase, setErase] = useState(false);
  const [counts, setCounts] = useState([0, 0]);
  const onChangeRef = useRef(onChange);
  useEffect(() => { onChangeRef.current = onChange; }, [onChange]);

  const repaint = useCallback(() => {
    const el = canvas.current; if (!el) return;
    const context = el.getContext('2d'); if (!context) return;
    context.setTransform(el.width / 320, 0, 0, el.height / 320, 0, 0);
    context.fillStyle = '#000'; context.fillRect(0, 0, 320, 320);
    for (const stroke of [...strokes.current, ...(active.current ? [active.current] : [])]) {
      context.strokeStyle = context.fillStyle = stroke.erase ? '#000' : '#fff';
      context.lineWidth = stroke.width; context.lineCap = context.lineJoin = 'round';
      const first = stroke.points[0];
      context.beginPath(); context.arc(first.x, first.y, stroke.width / 2, 0, Math.PI * 2); context.fill();
      context.beginPath(); context.moveTo(first.x, first.y);
      stroke.points.slice(1).forEach(p => context.lineTo(p.x, p.y)); context.stroke();
    }
  }, []);

  const notify = useCallback(() => {
    setCounts([strokes.current.length, future.current.length]);
    const el = canvas.current; const ctx = el?.getContext('2d');
    const pixels = el && ctx ? ctx.getImageData(0, 0, el.width, el.height).data : [];
    let hasInk = false;
    for (let i = 0; i < pixels.length; i += 4) if (pixels[i] > 20) { hasInk = true; break; }
    onChangeRef.current(hasInk);
  }, []);

  useEffect(() => {
    const el = canvas.current; if (!el) return;
    const resize = () => {
      const size = Math.round(el.getBoundingClientRect().width * Math.min(window.devicePixelRatio || 1, 3));
      if (size > 0) { el.width = el.height = size; repaint(); }
    };
    const observer = new ResizeObserver(resize); observer.observe(el); resize();
    return () => observer.disconnect();
  }, [repaint]);

  const undo = useCallback(() => { if (active.current) return; const last = strokes.current.pop(); if (last) future.current.push(last); repaint(); notify(); }, [notify, repaint]);
  const redo = useCallback(() => { if (active.current) return; const next = future.current.pop(); if (next) strokes.current.push(next); repaint(); notify(); }, [notify, repaint]);
  useEffect(() => {
    const shortcut = (event: KeyboardEvent) => {
      if (!canvas.current?.closest('.input-panel')?.contains(document.activeElement)) return;
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'z') { event.preventDefault(); if (event.shiftKey) redo(); else undo(); }
    };
    window.addEventListener('keydown', shortcut); return () => window.removeEventListener('keydown', shortcut);
  }, [redo, undo]);

  useImperativeHandle(ref, () => ({ toBlob: () => new Promise((resolve, reject) => {
    canvas.current?.toBlob(blob => blob ? resolve(blob) : reject(new Error('Could not export your drawing.')), 'image/png');
  }) }), []);

  const point = (event: ReactPointerEvent<HTMLCanvasElement>) => {
    const bounds = event.currentTarget.getBoundingClientRect();
    return { x: (event.clientX - bounds.left) / bounds.width * 320, y: (event.clientY - bounds.top) / bounds.height * 320 };
  };
  const finish = (event: ReactPointerEvent<HTMLCanvasElement>) => {
    if (pointer.current !== event.pointerId) return;
    if (active.current) strokes.current.push(active.current);
    active.current = null; pointer.current = null;
    if (event.currentTarget.hasPointerCapture(event.pointerId)) event.currentTarget.releasePointerCapture(event.pointerId);
    repaint(); notify();
  };

  return <>
    <div className="canvas-wrap"><canvas ref={canvas} aria-label="Draw a single digit from zero to nine" tabIndex={0}
      onPointerDown={event => {
        if (pointer.current !== null || event.button !== 0) return;
        event.preventDefault(); event.currentTarget.focus(); event.currentTarget.setPointerCapture(event.pointerId);
        pointer.current = event.pointerId; future.current = [];
        active.current = { points: [point(event)], width: erase ? width * 1.5 : width, erase };
        setCounts([Math.max(strokes.current.length, 1), 0]);
        onChangeRef.current(false); repaint();
      }}
      onPointerMove={event => { if (pointer.current === event.pointerId && active.current) { active.current.points.push(point(event)); repaint(); } }}
      onPointerUp={finish} onPointerCancel={finish} onLostPointerCapture={finish}/>
    </div>
    <div className="canvas-toolbar" aria-label="Drawing tools">
      <button type="button" className={!erase ? 'icon-button selected' : 'icon-button'} aria-label="Pen" title="Pen" aria-pressed={!erase} onClick={() => setErase(false)}><PenLine size={17}/></button>
      <button type="button" className={erase ? 'icon-button selected' : 'icon-button'} aria-label="Eraser" title="Eraser" aria-pressed={erase} onClick={() => setErase(true)}><Eraser size={17}/></button>
      <label className="brush-label"><span>Size</span><input aria-label="Brush thickness" type="range" min="6" max="34" value={width} onChange={event => setWidth(Number(event.target.value))}/><span className="mono">{width}</span></label>
      <div className="toolbar-separator"/>
      <button type="button" className="icon-button" aria-label="Undo" title="Undo (Ctrl/⌘ Z)" disabled={!counts[0]} onClick={undo}><Undo2 size={17}/></button>
      <button type="button" className="icon-button" aria-label="Redo" title="Redo (Ctrl/⌘ Shift Z)" disabled={!counts[1]} onClick={redo}><Redo2 size={17}/></button>
      <button type="button" className="icon-button" aria-label="Clear canvas" title="Clear canvas" disabled={!counts[0]} onClick={() => { if (active.current) return; strokes.current = []; future.current = []; repaint(); notify(); }}><Trash2 size={17}/></button>
    </div>
  </>;
});
