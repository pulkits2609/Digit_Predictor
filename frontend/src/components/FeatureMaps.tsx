import { useEffect, useRef, useState } from 'react';
import { LoaderCircle, ScanLine } from 'lucide-react';
import { visualize } from '../lib/api';
import type { FeatureMaps as FeatureMapData } from '../lib/api';

export function FeatureMaps({ image }: { image: Blob }) {
  const [data,setData]=useState<FeatureMapData|null>(null);const [loading,setLoading]=useState(false);const [error,setError]=useState('');const [original,setOriginal]=useState('');
  const controller=useRef<AbortController|null>(null);
  useEffect(()=>{const url=URL.createObjectURL(image);setOriginal(url);return()=>{URL.revokeObjectURL(url);controller.current?.abort();};},[image]);
  const load=async()=>{if(data||loading)return;const request=new AbortController();controller.current=request;setLoading(true);setError('');try{const response=await visualize(image,request.signal);if(!request.signal.aborted)setData(response);}catch(error){if(!request.signal.aborted)setError(error instanceof Error?error.message:'Feature maps are unavailable.');}finally{if(!request.signal.aborted)setLoading(false);}};
  return <details className="feature-details" onToggle={event=>{if(event.currentTarget.open)void load();}}><summary><ScanLine size={15}/>How the model sees your digit</summary><p>Actual intermediate activations, computed only when you open this view. Each channel is normalized for display.</p>{loading&&<p role="status"><LoaderCircle size={13} className="spin"/> Loading CNN feature maps…</p>}{error&&<p className="error-message" role="alert">{error} <button className="text-button" onClick={()=>void load()}>Try again</button></p>}{data&&<><div className="feature-original"><figure><img src={original} alt="Original submitted digit"/><figcaption>Original input</figcaption></figure><figure><img src={data.processed_image} alt="Normalized CNN input"/><figcaption>28 × 28 input</figcaption></figure></div>{data.feature_maps.map(layer=><div className="feature-layer" key={layer.layer}><h3>{layer.layer} / selected activation channels</h3><div>{layer.images.map((src,index)=><figure key={index}><img src={src} alt={`${layer.layer} activation channel ${index+1}`}/><figcaption>{String(index+1).padStart(2,'0')}</figcaption></figure>)}</div></div>)}</>}</details>;
}
