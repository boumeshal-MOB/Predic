from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from ..logger import setup_logging

LOGGER = setup_logging()

@dataclass(slots=True)
class IsolationForestConfig:
    contamination: float
    n_estimators: int


class IsolationForestDetector:

    def detect(
        self,
        raw_data: pd.DataFrame,
        params: dict[str, Any],
    ) -> pd.DataFrame:

        config = IsolationForestConfig(
            contamination=float(params.get("contamination", 0.01)),
            n_estimators=int(params.get("n_estimators", 100)),
        )

        if raw_data.empty:
            LOGGER.warning("Empty dataframe received.")
            return pd.DataFrame(columns=["timestamp","variable_id",])

        raw_data = raw_data.copy()
        raw_data["timestamp"] = pd.to_datetime(raw_data["timestamp"],utc=True)
        raw_data.sort_values("timestamp",inplace=True)

        values = raw_data["value"].astype(float).to_numpy()
        valid = np.isfinite(values)
        raw_data = raw_data.loc[valid].reset_index(drop=True)
        values = values[valid]

        if len(values) < 2:
            LOGGER.warning("Not enough valid samples.")
            return pd.DataFrame(columns=["timestamp","variable_id",])

        model = IsolationForest(
            contamination=config.contamination,
            n_estimators=config.n_estimators,
            random_state=42,
        )

        prediction = model.fit_predict(values.reshape(-1, 1))
        anomaly_mask = prediction == -1
        anomalies = (
            raw_data.loc[
                anomaly_mask,
                [
                    "timestamp",
                    "variable_id",
                ],
            ]
            .copy().reset_index(drop=True)
        )

        LOGGER.info(
            "Detected %d anomalies for variable %s (contamination=%s).",
            len(anomalies),
            raw_data["variable_id"].iloc[0],
            config.contamination,
        )


        return anomalies