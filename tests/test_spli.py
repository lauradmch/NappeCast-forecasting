import pytest

from src.helper.constants import DROUGHT_EVENT_THRESHOLD, DROUGHT_THRESHOLDS
from src.helper.spli import category_label

# pytest.mark.parametrize runs the same test once per (value, expected) pair
@pytest.mark.parametrize("value, expected", [
    (-2.5, "Extreme drought"),
    (-2.0, "Extreme drought"),
    (-1.5, "Severe drought"),
    (-1.2, "Moderate drought"),
    (-1.0, "Moderate drought"),
    ( 0.0, "Normal"),
    ( 1.0, "Moderately wet"),   # boundary: # original used < on the wet side
    ( 1.5, "Very wet"),
    ( 2.0, "Extremely wet"),
    ( 2.5, "Extremely wet"),
])
def test_category_label(value, expected):
    label, _ = category_label(value)
    assert label == expected


def test_nan_raises():
    with pytest.raises(ValueError):
        category_label(float("nan"))


def test_drought_thresholds():
    assert DROUGHT_THRESHOLDS == {"extreme": -2.0, "severe": -1.5, "moderate": -1.0}
    assert DROUGHT_EVENT_THRESHOLD == -1.5