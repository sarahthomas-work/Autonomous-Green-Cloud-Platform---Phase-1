from pathlib import Path

import joblib
import numpy as np
import tensorflow as tf


class PredictionService:
    """
    Loads the trained LSTM model and scaler and performs
    one-step time-series prediction.
    """

    def __init__(self):
        backend_dir = Path(__file__).resolve().parents[2]

        model_path = backend_dir / "ml_models" / "agcp_lstm_model.h5"
        scaler_path = backend_dir / "ml_models" / "scaler.pkl"

        self.model = tf.keras.models.load_model(model_path)
        self.scaler = joblib.load(scaler_path)

    def predict(self, values: list[float]) -> float:
        """
        Generate a prediction from the latest 60 values.
        """

        if len(values) < 60:
            raise ValueError(
                "At least 60 values are required for prediction."
            )

        last_60 = np.array(values[-60:], dtype=float).reshape(-1, 1)

        scaled_values = self.scaler.transform(last_60)

        model_input = scaled_values.reshape(1, 60, 1)

        prediction_scaled = self.model.predict(
            model_input,
            verbose=0,
        )

        prediction = self.scaler.inverse_transform(
            prediction_scaled
        )

        return float(prediction[0][0])


prediction_service = PredictionService()