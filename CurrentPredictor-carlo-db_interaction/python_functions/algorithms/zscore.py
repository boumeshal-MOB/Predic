from __future__ import annotations
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from ..logger import setup_logging

LOGGER = setup_logging()

@dataclass(slots=True)
class ZScoreConfig:
    degree: int
    threshold: float


class ZScoreDetector:
    """
    Polynomial Trend + Robust Z-Score (MAD).

    Workflow
    --------
    1. Fit a polynomial trend.
    2. Compute residuals.
    3. Compute robust z-score using MAD.
    4. Return anomalies.
    """

    @staticmethod
    def _polynomial_trend(values: np.ndarray,time_seconds: np.ndarray,degree: int) -> np.ndarray:
        
        #Compute the polynomial trend.
        coefficients = np.polyfit(time_seconds,values,degree)
        return np.polyval(coefficients,time_seconds)

    @staticmethod
    def _robust_zscore(residuals: np.ndarray,) -> np.ndarray:

        #Compute Robust Z-Score using MAD. If MAD is zero the standard deviation is used.
        valid = np.isfinite(residuals)

        if not valid.any():
            return np.full_like(residuals,np.nan)

        median = np.nanmedian(residuals)
        mad = np.nanmedian(np.abs(residuals - median))

        if not np.isfinite(mad) or mad <= 0:
            mad = np.std(residuals[valid])
            if mad == 0:
                mad = 1.0

        zscore = np.full_like(residuals,np.nan)
        zscore[valid] = (0.6745 * (residuals[valid] - median) / mad)
        return zscore

    def detect(self,raw_data: pd.DataFrame,params: dict[str, Any]) -> pd.DataFrame:

        #Detect anomalies
        config = ZScoreConfig(
            degree=int(params.get("degree", 5)),
            threshold=float(params.get("threshold", 2)),
        )

        if raw_data.empty:
            LOGGER.warning("Empty dataframe received.")
            return pd.DataFrame(
                columns=[
                    "timestamp",
                    "variable_id",
                ]
            )

        raw_data = raw_data.copy()
        raw_data["timestamp"] = pd.to_datetime(raw_data["timestamp"],utc=True)
        raw_data.sort_values("timestamp",inplace=True)

        values = raw_data["value"].astype(float).to_numpy()
        variable_ids = (raw_data["variable_id"].astype(int).to_numpy())
        timestamps = raw_data["timestamp"]
        time_seconds = (timestamps - timestamps.iloc[0]).dt.total_seconds().to_numpy()

        valid = (np.isfinite(values) & np.isfinite(time_seconds))
        values = values[valid]
        time_seconds = time_seconds[valid]
        raw_data = raw_data.loc[valid].reset_index(drop=True)
        variable_ids = variable_ids[valid]

        if len(values) <= config.degree:

            LOGGER.warning(
                "Not enough points (%d) for polynomial degree %d.",
                len(values),
                config.degree,
            )
            return pd.DataFrame(columns=["timestamp","variable_id"])

        try:
            trend = self._polynomial_trend(values,time_seconds,config.degree)

        except Exception:
            LOGGER.exception("Polynomial fit failed.")
            return pd.DataFrame(columns=["timestamp","variable_id"])
        
        residuals = values - trend
        zscore = self._robust_zscore(residuals)

        anomaly_mask = (np.abs(zscore)> config.threshold)

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
            "Detected %d anomalies for variable %s (degree=%d threshold=%s).",
            len(anomalies),
            variable_ids[0] if len(variable_ids) else "unknown",
            config.degree,
            config.threshold,
        )

        return anomalies