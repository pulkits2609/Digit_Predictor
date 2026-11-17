import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { DrawingCanvas } from '../components/DrawingCanvas';
describe('drawing history',()=>{
  it('supports completed strokes, undo, redo, and clear',()=>{
    const onChange=vi.fn();render(<DrawingCanvas onChange={onChange}/>);
    const canvas=screen.getByLabelText('Draw a single digit from zero to nine');
    vi.spyOn(canvas,'getBoundingClientRect').mockReturnValue({left:0,top:0,width:320,height:320,right:320,bottom:320,x:0,y:0,toJSON(){}});
    fireEvent.pointerDown(canvas,{pointerId:1,button:0,clientX:100,clientY:100});
    fireEvent.pointerMove(canvas,{pointerId:1,clientX:150,clientY:180});
    fireEvent.pointerUp(canvas,{pointerId:1});
    expect(screen.getByRole('button',{name:'Undo'})).toBeEnabled();
    fireEvent.click(screen.getByRole('button',{name:'Undo'}));
    expect(screen.getByRole('button',{name:'Undo'})).toBeDisabled();expect(screen.getByRole('button',{name:'Redo'})).toBeEnabled();
    fireEvent.click(screen.getByRole('button',{name:'Redo'}));expect(screen.getByRole('button',{name:'Undo'})).toBeEnabled();
    fireEvent.click(screen.getByRole('button',{name:'Clear canvas'}));expect(screen.getByRole('button',{name:'Undo'})).toBeDisabled();expect(screen.getByRole('button',{name:'Redo'})).toBeDisabled();expect(onChange).toHaveBeenLastCalledWith(false);
  });
  it('finishes cancelled pointers and exposes pen and eraser states',()=>{
    render(<DrawingCanvas onChange={vi.fn()}/>);fireEvent.click(screen.getByRole('button',{name:'Eraser'}));expect(screen.getByRole('button',{name:'Eraser'})).toHaveAttribute('aria-pressed','true');
    fireEvent.click(screen.getByRole('button',{name:'Pen'}));expect(screen.getByRole('button',{name:'Pen'})).toHaveAttribute('aria-pressed','true');
    const canvas=screen.getByLabelText('Draw a single digit from zero to nine');fireEvent.pointerDown(canvas,{pointerId:2,button:0,clientX:10,clientY:10});fireEvent.pointerCancel(canvas,{pointerId:2});expect(screen.getByRole('button',{name:'Undo'})).toBeEnabled();
  });
});
