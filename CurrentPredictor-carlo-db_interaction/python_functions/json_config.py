from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_LAST_TIMESTAMP = "2000-01-01T00:00:00+00:00"

class JsonConfig:

    def __init__(self, config_file: str) -> None:

        self.config_path = (
            Path(__file__).resolve().parent.parent
            / config_file
        )

        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {self.config_path}"
            )

    def load(self) -> dict[str, Any]:

        with open(self.config_path,"r",encoding="utf-8",) as file:
            config = json.load(file)

        for variable in config["variables"]:
            if not variable.get("last_timestamp"):
                variable["last_timestamp"] = DEFAULT_LAST_TIMESTAMP

        return config

    def save(
        self,
        config: dict[str, Any],
    ) -> None:

        with open(
            self.config_path,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                config,
                file,
                indent=2,
            )

    def update_last_timestamp(
        self,
        variable_id: int,
        last_timestamp: str,
    ) -> None:

        config = self.load()

        for variable in config["variables"]:

            if variable["variable_id"] == variable_id:

                variable["last_timestamp"] = last_timestamp
                break

        self.save(config)