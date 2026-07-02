from __future__ import annotations

import plotly.graph_objects as go
import pandas as pd


def plot_anomalies(
    raw_data: pd.DataFrame,
    anomalies: pd.DataFrame,
) -> None:
    """
    Plot raw data and highlight detected anomalies.
    """

    fig = go.Figure()

    # Normal data
    fig.add_trace(
        go.Scatter(
            x=raw_data["timestamp"],
            y=raw_data["value"],
            mode="lines+markers",
            name="Data",
            marker=dict(size=5),
        )
    )

    # Anomalies
    if not anomalies.empty:

        anomaly_points = raw_data.merge(
            anomalies,
            on=["timestamp", "variable_id"],
            how="inner",
        )

        fig.add_trace(
            go.Scatter(
                x=anomaly_points["timestamp"],
                y=anomaly_points["value"],
                mode="markers",
                name="Anomalies",
                marker=dict(
                    size=10,
                    symbol="x",
                    color="red",
                ),
            )
        )

    fig.update_layout(
        title="Anomaly Detection",
        xaxis_title="Timestamp",
        yaxis_title="Value",
        template="plotly_white",
    )

    fig.show()