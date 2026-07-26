"""
Schémas Pydantic — contrats d'entrée/sortie de l'API.

"""

from typing import List, Optional
from pydantic import BaseModel, Field

# a adapter
class Observation(BaseModel):
    date: Optional[str] = Field(
        None,
        description="Format AAAA-MM-JJ",
        examples=["2016-01-01"],
    )

class PredictionResponse(BaseModel):
    prediction: int
    probabilite: float


class BatchObservations(BaseModel):
    observations: List[Observation]


class BatchPredictionResponse(BaseModel):
    predictions: List[PredictionResponse]


class ModelInfoResponse(BaseModel):
    loaded: bool
    source: Optional[str] = None
    loaded_at: Optional[str] = None
    detail: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
