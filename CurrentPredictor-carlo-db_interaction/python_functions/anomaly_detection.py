from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import pandas as pd

from .algorithms.zscore import ZScoreDetector
from .algorithms.isolation_forest import IsolationForestDetector
from .algorithms.plotter import plot_anomalies        #delete to delate the plot

from .database import Database
from .json_config import JsonConfig
from .logger import setup_logging

LOGGER = setup_logging()


class RawDataAnomalyDetector:
    """
        1. Read raw data from the database.
        2. Execute the selected algorithm.
        3. Save anomalies to the database.
        4. Update last_timestamp inside config.json.
    """

    def __init__(self,config_file: str,env_file: str) -> None:

        self.db = Database(env_file)
        self.config = JsonConfig(config_file)
        
        self.algorithms = {
            "zscore": ZScoreDetector,
            "isolation_forest": IsolationForestDetector,
            # "dbscan": DBSCANDetector,
        }

    @staticmethod
    #Compute the start date from the selected time window.
    def _compute_start_date(days_ago: int) -> str:
        start_date = datetime.now() - timedelta(days=days_ago)
        return start_date.isoformat()


    #execute anomaly detection
    def run(
        self,
        variable_id: int,
        algorithm: str,
        days_ago: int,
        params: dict[str, Any],
        last_timestamp: str | None,
    ) -> pd.DataFrame:

        if algorithm not in self.algorithms:
            raise ValueError(f"Unsupported algorithm: {algorithm}")

        LOGGER.info(
            "Starting anomaly detection for variable %s",
            variable_id,
        )

        start_date = self._compute_start_date(days_ago)

        raw_data = self.db.fetch_raw_data(
            variable_id=variable_id,
            start_date=start_date,
        )

        if raw_data.empty:

            LOGGER.warning(
                "No raw data found for variable %s",
                variable_id,
            )

            return pd.DataFrame(
                columns=[
                    "timestamp",
                    "variable_id",
                ]
            )

        detector = self.algorithms[algorithm]()

        anomalies = detector.detect(
            raw_data=raw_data,
            params=params,
        )

        if last_timestamp is not None:

            last_timestamp = pd.to_datetime(
                last_timestamp,
                utc=True,
            )

            anomalies = anomalies.copy()

            anomalies["timestamp"] = pd.to_datetime(
                anomalies["timestamp"],
                utc=True,
            )

            anomalies = anomalies[anomalies["timestamp"] > last_timestamp]

        plot_anomalies(raw_data=raw_data,anomalies=anomalies)
        saved = self.db.save_anomalies(anomalies=anomalies)

        LOGGER.info(
            "Saved %d anomalies for variable %s",
            len(anomalies),
            variable_id,
        )

        if not anomalies.empty:

            latest_timestamp = (
                anomalies["timestamp"]
                .max()
                .isoformat()
            )

            self.config.update_last_timestamp(
                variable_id=variable_id,
                last_timestamp=latest_timestamp,
            )

        return anomalies