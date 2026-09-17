"""
Constants from NappeCast : fixed values that are used in multiple places in the codebase.
- Secrets, URLs          -> .env / os.getenv
- Parameters            -> configs/config.yaml
- Domain definitions    -> here (constants.py)
"""
from types import MappingProxyType
from typing import Final

# ---------------------------- COLONNES ----------------------------
TARGET_COL: Final = "niveau_nappe_eau"
DATE_COL: Final = "date_index"
STATION_COL: Final = "code_bss"

# ---------------------------- INDICES STANDARDISÉS ----------------------------
SPLI_COL: Final = "SPLI"
DRIVER_LABELS: Final[dict[str, str]] = {  # driver index columns -> human labels
    "SPI":  "Precipitation (SPI)",
    "SETI": "Evapotranspiration (SETI)",
    "SSTI": "Soil temperature (SSTI)",
    "SSRI": "Shortwave radiation (SSRI)",
    "SWSI": "Wind speed (SWSI)",
    "SCCI": "Cloud cover (SCCI)",
    "SPMI": "Sea-level pressure (SPMI)",
    "SPEI": "Water balance (SPEI)",
    "SSMI": "Soil moisture (SSMI)",
}
DEFAULT_DRIVERS: Final = ("SPI", "SPEI", "SSMI")

# ---------------------------- SPLI : SEUILS ----------------------------
MIN_FORECAST_DAYS: Final = 14 # forecast-only months need MORE than this many days in forecast_spli


# Ordered from driest to wettest: (upper bound, inclusive, label, color).
# inclusive=True -> v <= bound ; False -> v < bound
SPLI_CLASSES: Final = (
    (-2.0,         True,  "Extreme drought",  "#67001f"),
    (-1.5,         True,  "Severe drought",   "#b2182b"),
    (-1.0,         True,  "Moderate drought", "#ef8a62"),
    ( 1.0,         False, "Normal",           "#4d4d4d"),
    ( 1.5,         False, "Moderately wet",   "#67a9cf"),
    ( 2.0,         False, "Very wet",         "#2166ac"),
    (float("inf"), True,  "Extremely wet",    "#053061"),
)

# {"extreme": -2.0, "severe": -1.5, "moderate": -1.0}
DROUGHT_THRESHOLDS: Final = MappingProxyType({
    label.split()[0].lower(): bound
    for bound, _, label, _ in SPLI_CLASSES
    if "drought" in label
})
DROUGHT_EVENT_THRESHOLD: Final = DROUGHT_THRESHOLDS["severe"]
