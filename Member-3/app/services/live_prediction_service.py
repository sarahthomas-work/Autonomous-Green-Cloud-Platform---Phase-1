from pathlib import Path

import pandas as pd

from app.services.prediction_service import prediction_service


class LivePredictionService:

    def __init__(self):
        backend_dir = Path(__file__).resolve().parents[2]
        self.raw_csv = backend_dir / "data" / "raw_telemetry.csv"

    def get_cpu_history(self, node_id: str) -> list[float]:
        if not self.raw_csv.exists():
            raise ValueError(
                "Live telemetry history is not available yet."
            )

        df = pd.read_csv(self.raw_csv)

        if df.empty:
            raise ValueError(
                "Live telemetry history is empty."
            )

        required_columns = {"instance", "cpu_util"}

        if not required_columns.issubset(df.columns):
            raise ValueError(
                "Live telemetry data does not contain the required "
                "instance and cpu_util fields."
            )

        node_data = df[df["instance"] == node_id]

        if len(node_data) < 60:
            raise ValueError(
                f"Only {len(node_data)} CPU telemetry values are available "
                f"for node {node_id}. At least 60 values are required."
            )

        return (
            node_data["cpu_util"]
            .astype(float)
            .tail(60)
            .tolist()
        )

    def predict(self, node_id: str) -> float:
        values = self.get_cpu_history(node_id)
        return prediction_service.predict(values)


live_prediction_service = LivePredictionService()