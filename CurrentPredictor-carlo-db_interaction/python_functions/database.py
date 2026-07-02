from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pandas as pd
import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor, execute_values


class Database:

    def __init__(self, env_file: str) -> None:

        base_dir = Path(__file__).resolve().parent.parent
        env_path = base_dir / env_file

        if not env_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {env_path}")

        load_dotenv(env_path)

        self.connection = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            port=int(os.getenv("DB_PORT", "5432")),
        )

        self.connection.autocommit = False

    def _select(
        self,
        query: str,
        parameters: tuple[Any, ...] | None = None,
    ) -> pd.DataFrame:

        with self.connection.cursor(
            cursor_factory=RealDictCursor
        ) as cursor:

            cursor.execute(query, parameters)
            rows = cursor.fetchall()

        return pd.DataFrame(rows)

    # Read data from db
    def fetch_raw_data(
        self,
        variable_id: int,
        start_date: str,
        limit: int = 10000,
    ) -> pd.DataFrame:

        query = """
            SELECT
                timestamp,
                value,
                variable_id
            FROM raw_data
            WHERE variable_id = %s
              AND timestamp >= %s
              AND timestamp <= NOW()
            ORDER BY timestamp ASC
            LIMIT %s
        """

        return self._select(
            query,
            (
                variable_id,
                start_date,
                limit,
            ),
        )

    #Save anomalies inside the db
    def save_anomalies(self, anomalies: pd.DataFrame) -> None:

        if anomalies.empty:
            return

        values = list(
            anomalies[
                [
                    "timestamp",
                    "variable_id",
                ]
            ].itertuples(
                index=False,
                name=None,
            )
        )

        query = """
            INSERT INTO anomalies
                (timestamp, variable_id)
            VALUES %s
            ON CONFLICT (timestamp, variable_id)
            DO NOTHING
        """

        try:

            with self.connection.cursor() as cursor:

                execute_values(
                    cursor,
                    query,
                    values,
                    page_size=1000,
                )

            self.connection.commit()

        except Exception:

            self.connection.rollback()
            raise

    # Connection handling
    def close(self) -> None:

        if self.connection and not self.connection.closed:
            self.connection.close()

    def __enter__(self):
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ):

        if exc_type is not None:
            self.connection.rollback()

        self.close()