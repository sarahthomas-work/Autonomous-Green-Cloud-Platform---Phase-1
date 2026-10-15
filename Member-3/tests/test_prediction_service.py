import numpy as np
import pytest

from app.services.prediction_service import prediction_service


def test_prediction_with_60_values():
    values = np.linspace(10, 90, 60).tolist()

    prediction = prediction_service.predict(values)

    assert isinstance(prediction, float)


def test_prediction_with_less_than_60_values():
    values = np.linspace(10, 50, 59).tolist()

    with pytest.raises(ValueError, match="At least 60 values are required"):
        prediction_service.predict(values)