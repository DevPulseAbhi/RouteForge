"""Plotly views for honest algorithm comparisons."""

from __future__ import annotations

import pandas as pd
import plotly.express as px

from algorithms import SearchResult


def results_frame(results: list[SearchResult]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Algorithm": result.algorithm,
                "Found": "Yes" if result.found else "No",
                "Distance (m)": result.cost,
                "Hops": result.hops,
                "Nodes explored": result.explored_nodes,
                "Edges considered": result.edges_considered,
                "Time (ms)": result.execution_time_ms,
            }
            for result in results
        ]
    )


def comparison_chart(results: list[SearchResult], metric: str):
    frame = results_frame(results)
    return px.bar(frame, x="Algorithm", y=metric, color="Algorithm", title=f"{metric} comparison", text_auto=".3s")
