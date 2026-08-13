from pydantic import BaseModel, Field


class ModelPrediction(BaseModel):

    prediction: str

    confidence: float = Field(
        ge=0.0,
        le=1.0
    )

    probabilities: list[float]


class ApplePredictionResponse(BaseModel):

    success: bool

    fruit: str

    freshness: ModelPrediction

    shelf_life: ModelPrediction