"""
Schémas Pydantic — contrats d'entrée/sortie de l'API.


"""

from typing import List, Optional
from datetime import date, datetime
from pydantic import BaseModel, ConfigDict

class ModelInfoResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    loaded: bool
    source: Optional[str] = None
    model_type: Optional[str] = None
    loaded_at: Optional[str] = None
    detail: Optional[str] = None

class PredictRecord(BaseModel):
    ds: str
    yhat: float
    yhat_lower: float
    yhat_upper: float

class TrainingResponse(BaseModel):
    horizon: int
    new_version: Optional[str] = None
    previous_version: Optional[str] = None
    run_id: str

class HealthResponse(BaseModel):
    status: str

class ProcessedRecord(BaseModel):
    latitude: float
    longitude: float
    temperature_2m_max: float
    sunrise: datetime
    sunset: datetime
    daylight_duration: float
    precipitation_sum: float
    shortwave_radiation_sum: float
    et0_fao_evapotranspiration: float
    cloud_cover_mean: float
    pressure_msl_mean: float
    wind_speed_10m_mean: float
    soil_moisture_0_to_100cm_mean: float
    soil_temperature_0_to_100cm_mean: float
    code_bss: str
    date_index: date
    bss_id: str
    niveau_nappe_eau: float
    mode_obtention: str
    nom_producteur: str
    P_cum_30d: Optional[float] = None
    P_cum_90d: Optional[float] = None
    Peff_cum_30d: Optional[float] = None
    Peff_cum_90d: Optional[float] = None
    Temperature_mean_30d: Optional[float] = None
    Temperature_mean_90d: Optional[float] = None
    SPLI: Optional[float] = None
    SPI: Optional[float] = None
    SETI: Optional[float] = None
    SSTI: Optional[float] = None
    SSRI: Optional[float] = None
    SWSI: Optional[float] = None
    SCCI: Optional[float] = None
    SPMI: Optional[float] = None
    SPEI: Optional[float] = None
    SSMI: Optional[float] = None

class InterimRecord(BaseModel):
    latitude: float
    longitude: float
    temperature_2m_max: float
    sunrise: datetime
    sunset: datetime
    daylight_duration: float
    precipitation_sum: float
    shortwave_radiation_sum: float
    et0_fao_evapotranspiration: float
    cloud_cover_mean: float
    pressure_msl_mean: float
    wind_speed_10m_mean: float
    soil_moisture_0_to_100cm_mean: float
    soil_temperature_0_to_100cm_mean: float
    code_bss: str
    date_index: date
    bss_id: str
    niveau_nappe_eau: float
    mode_obtention: str
    nom_producteur: str

class ProcessedResponse(BaseModel):
    status: str
    n_rows: int
    data: List[ProcessedRecord]
    
class InterimResponse(BaseModel):
    status: str
    n_rows: int
    data: List[InterimRecord]

class PredictResponse(BaseModel):
    status: str
    n_rows: int
    horizon : str
    last_train: str
    data: List[PredictRecord]

class ForecastResponse(BaseModel):
    status: str
    n_rows: int
    horizon : str
    last_train: str
    data: List[PredictRecord]

class HistoricResponse(BaseModel):
    status: str
    n_rows: int
    horizon : str
    last_train: str
    data: List[ProcessedRecord]
    
class LoadResponse(BaseModel):
    status: str
    n_rows: int