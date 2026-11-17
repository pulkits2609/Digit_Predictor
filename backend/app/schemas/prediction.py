from pydantic import BaseModel, Field

class RankedPrediction(BaseModel):
    digit: int = Field(ge=0, le=9)
    confidence: float = Field(ge=0, le=1)

class Prediction(BaseModel):
    prediction: int = Field(ge=0, le=9)
    confidence: float = Field(ge=0, le=1)
    top_predictions: list[RankedPrediction] = Field(min_length=3, max_length=3)
    probabilities: list[float] = Field(min_length=10, max_length=10)
    processing_time_ms: float = Field(ge=0)
    model_version: str
    is_uncertain: bool
    processed_image: str
