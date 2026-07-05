from __future__ import annotations

import sys

from python_functions.json_config import JsonConfig
from python_functions.anomaly_detection import RawDataAnomalyDetector

CONFIG_FILE = "config1.json"
ENV_FILE = "config.env"

def main() -> None:
    try:

        config_manager = JsonConfig(CONFIG_FILE)
        config = config_manager.load()

        algorithm = config["algorithm"]
        days_ago = config["days_ago"]
        variables = config["variables"]
        params = config["algorithm_params"]

        detector = RawDataAnomalyDetector(config_file=CONFIG_FILE,env_file=ENV_FILE)

        print("=" * 60)
        print("Anomaly Detection Started")
        print("=" * 60)
        print(f"Algorithm : {algorithm}")
        print(f"Days Ago  : {days_ago}")
        print(f"Variables : {len(variables)}")
        print(f"Parameters: {params}")

        for variable in variables:

            variable_id = variable["variable_id"]
            last_timestamp = variable.get("last_timestamp")

            print("\n" + "=" * 60)
            print(f"Processing variable_id = {variable_id}")
            print(f"Last timestamp         = {last_timestamp}")

            anomalies = detector.run(
                variable_id=variable_id,
                algorithm=algorithm,
                days_ago=days_ago,
                params=params,
                last_timestamp=last_timestamp,
            )

            if anomalies.empty:
                print("No anomalies found.")
            else:
                print(f"Found {len(anomalies)} anomalies.")
                print(anomalies)

        print("\n" + "=" * 60)
        print("Anomaly Detection Completed")
        print("=" * 60)

    except Exception as exc:
        print("\nAn error occurred during anomaly detection.")
        print(f"Error: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()