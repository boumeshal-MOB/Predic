from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from python_functions.algorithms.zscore import ZScoreDetector
from python_functions.algorithms.isolation_forest import IsolationForestDetector

rng = np.random.default_rng(42)

N_POINTS = 24 * 14  # 14 days, hourly
start = datetime(2026, 6, 1, tzinfo=timezone.utc)
timestamps = [start + timedelta(hours=i) for i in range(N_POINTS)]

t = np.arange(N_POINTS)
trend = 0.01 * t
daily_cycle = 3 * np.sin(2 * np.pi * t / 24)
noise = rng.normal(0, 0.6, N_POINTS)
values = 20 + trend + daily_cycle + noise

injected_indices = [40, 41, 120, 121, 200, 250, 251, 252, 300]
for idx in injected_indices:
    values[idx] += rng.choice([-1, 1]) * rng.uniform(8, 14)

raw_data = pd.DataFrame(
    {
        "timestamp": timestamps,
        "value": values,
        "variable_id": 1,
    }
)

config1 = json.loads((PROJECT_ROOT / "config1.json").read_text())
config = json.loads((PROJECT_ROOT / "config.json").read_text())

zscore_anomalies = ZScoreDetector().detect(
    raw_data=raw_data,
    params=config["algorithm_params"],
)
iforest_anomalies = IsolationForestDetector().detect(
    raw_data=raw_data,
    params=config1["algorithm_params"],
)

injected_timestamps = {timestamps[i].isoformat() for i in injected_indices}


def summarize(detected_isoformats: list[str]) -> dict:
    detected = set(detected_isoformats)
    return {
        "true_positive": len(detected & injected_timestamps),
        "false_positive": len(detected - injected_timestamps),
        "false_negative": len(injected_timestamps - detected),
    }


zscore_ts = [ts.isoformat() for ts in zscore_anomalies["timestamp"]]
iforest_ts = [ts.isoformat() for ts in iforest_anomalies["timestamp"]]

output = {
    "timestamps": [ts.isoformat() for ts in raw_data["timestamp"]],
    "values": [round(v, 3) for v in raw_data["value"].tolist()],
    "injected_indices": injected_indices,
    "zscore": {
        "params": config["algorithm_params"],
        "anomaly_timestamps": zscore_ts,
        "summary": summarize(zscore_ts),
    },
    "isolation_forest": {
        "params": config1["algorithm_params"],
        "anomaly_timestamps": iforest_ts,
        "summary": summarize(iforest_ts),
    },
}

out_path = Path(__file__).resolve().parent / "demo_data.json"
out_path.write_text(json.dumps(output))

print(f"Z-Score anomalies found: {len(zscore_anomalies)}")
print(f"Isolation Forest anomalies found: {len(iforest_anomalies)}")
print(f"Injected anomalies: {len(injected_indices)}")
