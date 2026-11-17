import '@testing-library/jest-dom/vitest';
import { afterEach, vi } from 'vitest';
import { cleanup } from '@testing-library/react';
afterEach(()=>{cleanup();vi.restoreAllMocks();});
vi.stubEnv('VITE_API_BASE_URL','https://api.test.invalid');
class TestResizeObserver { observe() {} unobserve() {} disconnect() {} }
vi.stubGlobal('ResizeObserver', TestResizeObserver);
Object.defineProperty(window,'matchMedia',{writable:true,value:vi.fn().mockImplementation(()=>({matches:false,addListener:vi.fn(),removeListener:vi.fn(),addEventListener:vi.fn(),removeEventListener:vi.fn()}))});
Object.defineProperty(HTMLCanvasElement.prototype,'getContext',{value:vi.fn(()=>({setTransform:vi.fn(),fillRect:vi.fn(),beginPath:vi.fn(),arc:vi.fn(),fill:vi.fn(),moveTo:vi.fn(),lineTo:vi.fn(),stroke:vi.fn(),getImageData:vi.fn(()=>({data:new Uint8ClampedArray(4)}))}))});
URL.createObjectURL=vi.fn(()=> 'blob:test-image');URL.revokeObjectURL=vi.fn();
class TestPointerEvent extends MouseEvent { pointerId:number; constructor(type:string,props:PointerEventInit={}){super(type,props);this.pointerId=props.pointerId??1;} }
vi.stubGlobal('PointerEvent',TestPointerEvent);
HTMLCanvasElement.prototype.setPointerCapture=vi.fn();HTMLCanvasElement.prototype.hasPointerCapture=vi.fn(()=>false);HTMLCanvasElement.prototype.releasePointerCapture=vi.fn();
