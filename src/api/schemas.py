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


class TrainingResponse(BaseModel):
    horizon: int
    new_version: Optional[str] = None
    previous_version: Optional[str] = None
    run_id: str


class HealthResponse(BaseModel):
    status: str


class StationRecord(BaseModel):
    code_bss: str
    urn_bss: str
    date_debut_mesure: Optional[date] = None
    date_fin_mesure: Optional[date] = None
    code_commune_insee: str
    nom_commune: str
    longitude: float
    latitude: float
    codes_bdlisa: str
    urns_bdlisa: str
    geometry: Optional[str] = None
    bss_id: str
    altitude_station: Optional[float] = None
    nb_mesures_piezo: Optional[int] = None
    code_departement: str
    nom_departement: str
    libelle_pe: str
    profondeur_investigation: Optional[float] = None
    codes_masse_eau_edl: str
    noms_masse_eau_edl: str
    urns_masse_eau_edl: str
    date_maj: Optional[datetime] = None


class InterimRecord(BaseModel):
    # Clés (toujours présentes)
    code_bss: str
    date_index: date
    latitude: float
    longitude: float
    temperature_2m_max: Optional[float] = None
    sunrise: Optional[datetime] = None
    sunset: Optional[datetime] = None
    daylight_duration: Optional[float] = None
    precipitation_sum: Optional[float] = None
    shortwave_radiation_sum: Optional[float] = None
    et0_fao_evapotranspiration: Optional[float] = None
    cloud_cover_mean: Optional[float] = None
    pressure_msl_mean: Optional[float] = None
    wind_speed_10m_mean: Optional[float] = None
    soil_moisture_0_to_100cm_mean: Optional[float] = None
    soil_temperature_0_to_100cm_mean: Optional[float] = None
    bss_id: Optional[str] = None
    niveau_nappe_eau: Optional[float] = None
    mode_obtention: Optional[str] = None
    nom_producteur: Optional[str] = None


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
    peff_cum_30d: Optional[float] = None
    peff_cum_90d: Optional[float] = None
    temperature_mean_30d: Optional[float] = None
    temperature_mean_90d: Optional[float] = None
    spli: Optional[float] = None
    spi: Optional[float] = None
    seti: Optional[float] = None
    ssti: Optional[float] = None
    ssri: Optional[float] = None
    swsi: Optional[float] = None
    scci: Optional[float] = None
    spmi: Optional[float] = None
    spei: Optional[float] = None
    ssmi: Optional[float] = None


class ForecastRecord(BaseModel):
    horizon: int
    last_train: date
    ds: date
    code_bss: str
    bss_id: str
    yhat: float
    yhat_lower: float
    yhat_upper: float
    id: Optional[int] = None
    inserted_at: Optional[datetime] = None

class StationResponse(BaseModel):
    status: str
    n_rows: int
    data: List[StationRecord]


class InterimResponse(BaseModel):
    status: str
    n_rows: int
    data: List[InterimRecord]


class ProcessedResponse(BaseModel):
    status: str
    n_rows: int
    data: List[ProcessedRecord]


class ForecastResponse(BaseModel):
    status: str
    n_rows: int
    horizon : int
    last_train: date
    data: List[ForecastRecord]


class TuningResponse(BaseModel):
    horizon: int
    status: str


class LoadResponse(BaseModel):
    status: str
    nb_station: int
    nb_processed: int
    nb_forecast: int

class TransfertLogResponse(BaseModel):
    status: str
    file: str