"""
Schémas Pydantic — contrats d'entrée/sortie de l'API.


"""

from typing import List, Optional

from pydantic import BaseModel, ConfigDict

class ModelInfoResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    loaded: bool
    source: Optional[str] = None
    model_type: Optional[str] = None
    loaded_at: Optional[str] = None
    detail: Optional[str] = None


class PredictPoint(BaseModel):
    ds: str
    yhat: float
    yhat_lower: float
    yhat_upper: float

class PredictResponse(BaseModel):
    last_train: str
    points: List[PredictPoint]


class TrainingResponse(BaseModel):
    horizon: int
    new_version: Optional[str] = None
    previous_version: Optional[str] = None
    run_id: str


class HealthResponse(BaseModel):
    status: str
