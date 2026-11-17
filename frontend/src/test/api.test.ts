import { describe, expect, it, vi } from 'vitest';
import { predict, validateUpload } from '../lib/api';
describe('upload validation',()=>{
  it('accepts supported images',()=>{for(const type of ['image/png','image/jpeg','image/webp'])expect(validateUpload(new File(['bytes'],'digit',{type}))).toBeNull();});
  it('rejects unsupported, empty and oversized uploads',()=>{
    expect(validateUpload(new File(['a'],'digit.svg',{type:'image/svg+xml'}))).toMatch(/PNG/);
    expect(validateUpload(new File([],'digit.png',{type:'image/png'}))).toMatch(/empty/);
    expect(validateUpload(new File([new Uint8Array(6*1024*1024)],'digit.png',{type:'image/png'}))).toMatch(/smaller/);
  });
});
describe('prediction transport',()=>{
  it('reports server unavailability',async()=>{vi.stubGlobal('fetch',vi.fn().mockRejectedValue(new TypeError('network')));await expect(predict(new Blob(['a']),new AbortController().signal)).rejects.toThrow(/Cannot reach/);});
  it('reports a timeout without retrying',async()=>{
    vi.stubGlobal('fetch',vi.fn((_url,options)=>new Promise((_resolve,reject)=>options.signal.addEventListener('abort',()=>reject(new DOMException('Aborted','AbortError'))))));
    await expect(predict(new Blob(['a']),new AbortController().signal,5)).rejects.toThrow(/timed out/);expect(fetch).toHaveBeenCalledTimes(1);
  });
  it('rejects incomplete responses',async()=>{vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:true,json:async()=>({prediction:3,probabilities:[1]})}));await expect(predict(new Blob(['a']),new AbortController().signal)).rejects.toThrow(/invalid prediction/);});
  it('preserves explicit cancellation',async()=>{const controller=new AbortController();controller.abort();vi.stubGlobal('fetch',vi.fn().mockRejectedValue(new DOMException('Aborted','AbortError')));await expect(predict(new Blob(['a']),controller.signal)).rejects.toHaveProperty('name','AbortError');});
});
