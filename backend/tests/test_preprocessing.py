import io
import numpy as np
import pytest
from PIL import Image, ImageDraw
from app.ml.preprocessing import InputError, preprocess

def image_bytes(format="PNG", inverted=False, offset=(0,0), rgba=False, white_ink=False):
    image=Image.new("RGBA" if rgba else "RGB", (300,300), (0,0,0,0) if rgba else ("white" if inverted else "black"))
    draw=ImageDraw.Draw(image)
    ink="white" if (white_ink or not inverted) else "black"
    if rgba and not white_ink:
        ink="black"
    ox,oy=offset
    draw.line([(80+ox,80+oy),(180+ox,80+oy),(110+ox,210+oy)],fill=ink,width=16)
    stream=io.BytesIO()
    image.save(stream,format=format)
    return stream.getvalue()

@pytest.mark.parametrize("format",["PNG","JPEG","WEBP"])
def test_supported_formats(format):
    result=preprocess(image_bytes(format))
    assert result.tensor.shape==(1,28,28,1)
    assert result.tensor.dtype==np.float32
    assert 0 <= result.tensor.min() <= result.tensor.max() <= 1
    assert result.preview.startswith("data:image/png;base64,")

@pytest.mark.parametrize("color",["black","white"])
def test_blank_images(color):
    stream=io.BytesIO()
    Image.new("RGB",(100,100),color).save(stream,format="PNG")
    with pytest.raises(InputError,match="No visible digit"):
        preprocess(stream.getvalue())

@pytest.mark.parametrize("data",[b"",b"not-an-image",b"\x89PNG\r\n\x1a\n"])
def test_invalid_image(data):
    with pytest.raises(InputError):
        preprocess(data)

@pytest.mark.parametrize("white_ink",[False,True])
def test_transparent_ink(white_ink):
    assert preprocess(image_bytes(rgba=True,white_ink=white_ink)).tensor.sum()>5

def test_fully_transparent_image():
    stream=io.BytesIO()
    Image.new("RGBA",(100,100),(0,0,0,0)).save(stream,format="PNG")
    with pytest.raises(InputError):
        preprocess(stream.getvalue())

def test_polarity_and_translation_invariance():
    regular=preprocess(image_bytes()).tensor
    assert np.allclose(regular,preprocess(image_bytes(inverted=True)).tensor,atol=0.01)
    assert np.array_equal(regular,preprocess(image_bytes(offset=(50,-30))).tensor)
    pixels=regular[0,:,:,0]
    y,x=np.indices((28,28))
    assert abs((pixels*x).sum()/pixels.sum()-13.5)<0.6
    assert abs((pixels*y).sum()/pixels.sum()-13.5)<0.6

def test_pixel_limit():
    with pytest.raises(InputError) as error:
        preprocess(image_bytes(),100)
    assert error.value.status==413

def test_extreme_ratio():
    stream=io.BytesIO()
    Image.new("RGB",(600,2),"black").save(stream,format="PNG")
    with pytest.raises(InputError):
        preprocess(stream.getvalue())

def test_excess_whitespace_and_faint_strokes():
    image=Image.new("L",(1500,1200),255)
    ImageDraw.Draw(image).line([(1000,800),(1040,800),(1010,860)],fill=225,width=5)
    stream=io.BytesIO()
    image.save(stream,format="PNG")
    assert preprocess(stream.getvalue()).tensor.sum()>5
