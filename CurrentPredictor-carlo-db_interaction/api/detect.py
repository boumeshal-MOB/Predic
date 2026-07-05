from __future__ import annotations

import json
import os
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from python_functions.json_config import JsonConfig
from python_functions.anomaly_detection import RawDataAnomalyDetector

CONFIG_FILE = "config1.json"
ENV_FILE = "config.env"


def run_detection() -> dict:
    config_manager = JsonConfig(CONFIG_FILE)
    config = config_manager.load()

    algorithm = config["algorithm"]
    days_ago = config["days_ago"]
    variables = config["variables"]
    params = config["algorithm_params"]

    detector = RawDataAnomalyDetector(config_file=CONFIG_FILE, env_file=ENV_FILE)

    results = []

    for variable in variables:
        variable_id = variable["variable_id"]
        last_timestamp = variable.get("last_timestamp")

        anomalies = detector.run(
            variable_id=variable_id,
            algorithm=algorithm,
            days_ago=days_ago,
            params=params,
            last_timestamp=last_timestamp,
        )

        results.append(
            {
                "variable_id": variable_id,
                "anomalies_found": len(anomalies),
            }
        )

    return {"algorithm": algorithm, "results": results}


class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        cron_secret = os.getenv("CRON_SECRET")
        auth_header = self.headers.get("Authorization")

        if cron_secret and auth_header != f"Bearer {cron_secret}":
            self.send_response(401)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "unauthorized"}).encode("utf-8"))
            return

        try:
            payload = run_detection()
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(payload).encode("utf-8"))
        except Exception as exc:
            self.send_response(500)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(exc)}).encode("utf-8"))
