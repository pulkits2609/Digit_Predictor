import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import App from '../App';
import { predict, checkReadiness } from '../lib/api';
import type { Prediction } from '../lib/api';
vi.mock('../lib/api',async importOriginal=>({...await importOriginal<typeof import('../lib/api')>(),predict:vi.fn(),checkReadiness:vi.fn()}));
const result:Prediction={prediction:7,confidence:.97,top_predictions:[{digit:7,confidence:.97},{digit:1,confidence:.02},{digit:9,confidence:.01}],probabilities:[0,.02,0,0,0,0,0,.97,0,.01],processing_time_ms:12.3,model_version:'test',is_uncertain:false,processed_image:'data:image/png;base64,test'};
beforeEach(()=>{window.history.replaceState(null,'','#workspace');vi.mocked(checkReadiness).mockResolvedValue(true);vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:false}));vi.mocked(predict).mockReset();});
async function upload() { await userEvent.click(screen.getByRole('tab',{name:'Upload an image'}));const input=screen.getByLabelText('Upload digit image');await userEvent.upload(input,new File(['image'],'seven.png',{type:'image/png'})); }
describe('workspace',()=>{
  it('keeps the workspace minimal and leaves the educational sections off the page',()=>{
    render(<App/>);
    expect(screen.getByRole('heading',{name:'Handwritten Digit Recognition'})).toBeVisible();
    expect(screen.getByRole('heading',{name:'No prediction yet'})).toBeVisible();
    expect(screen.queryByRole('link',{name:/how it works|model insights/i})).not.toBeInTheDocument();
    expect(screen.queryByText('LAB')).not.toBeInTheDocument();
    expect(screen.queryByText('Inside the learning process')).not.toBeInTheDocument();
    expect(screen.queryByLabelText('Probability distribution across digits zero to nine')).not.toBeInTheDocument();
  });
  it('preserves direct insights navigation and returning to the workspace',async()=>{
    render(<App/>);
    window.location.hash='#model-insights';fireEvent(window,new HashChangeEvent('hashchange'));
    expect(await screen.findByRole('heading',{name:'Inside the learning process'})).toBeVisible();
    await userEvent.click(screen.getByRole('link',{name:'Workspace'}));
    await waitFor(()=>expect(screen.getByRole('heading',{name:'Handwritten Digit Recognition'})).toBeVisible());
    expect(screen.queryByRole('heading',{name:'Inside the learning process'})).not.toBeInTheDocument();
  });
  it('explains the actual winning class without inventing feature attributions',async()=>{
    vi.mocked(predict).mockResolvedValue({...result,prediction:4,confidence:.8,top_predictions:[{digit:4,confidence:.8},{digit:7,confidence:.2}],probabilities:[0,0,0,0,.8,0,0,.2,0,0]});
    render(<App/>);await upload();await userEvent.click(screen.getByRole('button',{name:'Recognize digit'}));
    const explanation=await screen.findByRole('heading',{name:'How it reached this result'});
    expect(explanation.parentElement).toHaveTextContent('gave 4 the highest score');
    expect(explanation.parentElement).toHaveTextContent('cropped, centered, and resized to 28 × 28 pixels');
    expect(screen.getByText('Confidence is the model’s score, not a guarantee of correctness.')).toBeVisible();
  });
  it('starts with empty canvas controls disabled and switches modes',async()=>{render(<App/>);expect(screen.getByRole('button',{name:'Recognize digit'})).toBeDisabled();expect(screen.getByRole('button',{name:'Undo'})).toBeDisabled();expect(screen.getByRole('button',{name:'Redo'})).toBeDisabled();expect(screen.getByRole('button',{name:'Clear canvas'})).toBeDisabled();await upload();expect(screen.getByRole('button',{name:'Recognize digit'})).toBeEnabled();expect(screen.getByText('seven.png')).toBeVisible();});
  it('shows invalid upload feedback',async()=>{render(<App/>);await userEvent.click(screen.getByRole('tab',{name:'Upload an image'}));fireEvent.change(screen.getByLabelText('Upload digit image'),{target:{files:[new File(['bad'],'bad.gif',{type:'image/gif'})]}});expect(screen.getByRole('alert')).toHaveTextContent('Choose a PNG');expect(screen.getByRole('button',{name:'Recognize digit'})).toBeDisabled();});
  it('renders genuine response fields and all ten classes',async()=>{vi.mocked(predict).mockResolvedValue(result);render(<App/>);await upload();await userEvent.click(screen.getByRole('button',{name:'Recognize digit'}));await waitFor(()=>expect(screen.getByText('97.0')).toBeVisible());expect(screen.getByAltText('Actual preprocessed 28 by 28 grayscale CNN input')).toHaveAttribute('src',result.processed_image);expect(screen.getByText('12.3 ms')).toBeVisible();expect(screen.getByLabelText('Probability distribution across digits zero to nine').children).toHaveLength(10);});
  it('protects against stale responses after changing the image',async()=>{let resolve!:(result:Prediction)=>void;vi.mocked(predict).mockImplementation(()=>new Promise(r=>{resolve=r;}));render(<App/>);await upload();await userEvent.click(screen.getByRole('button',{name:'Recognize digit'}));expect(screen.getByRole('button',{name:'Recognizing your digit…'})).toBeDisabled();await userEvent.click(screen.getByRole('button',{name:'Remove image'}));resolve(result);await waitFor(()=>expect(screen.queryByText('97.0')).not.toBeInTheDocument());expect(screen.getByRole('button',{name:'Recognize digit'})).toBeDisabled();});
  it('recovers from errors without a refresh',async()=>{vi.mocked(predict).mockRejectedValueOnce(new Error('The server is unavailable.')).mockResolvedValueOnce(result);render(<App/>);await upload();await userEvent.click(screen.getByRole('button',{name:'Recognize digit'}));expect(await screen.findByRole('alert')).toHaveTextContent('unavailable');await userEvent.click(screen.getByRole('button',{name:'Try again'}));await waitFor(()=>expect(screen.getByText('97.0')).toBeVisible());});
});

