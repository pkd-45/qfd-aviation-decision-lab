from __future__ import annotations

import numpy as np
import pandas as pd

MISSION_THRESHOLDS = {
    "suppression": (30.0, 45.0, 60.0, 90.0),
    "isr": (15.0, 30.0, 45.0, 60.0),
}


def _mission_metrics(assignments: pd.DataFrame, mission: str) -> dict[str, float]:
    subset = assignments.loc[assignments["mission"] == mission]
    risk = subset["scenario_risk"].to_numpy(dtype=float)
    times = subset["response_min"].to_numpy(dtype=float)
    risk_total = float(risk.sum())
    weighted_mean = float(np.sum(risk * times) / risk_total)
    order = np.argsort(times)
    cumulative = np.cumsum(risk[order]) / risk_total
    p90_time = float(times[order][np.searchsorted(cumulative, 0.90)])

    prefix = f"{mission}_risk_weighted"
    metrics = {
        f"{prefix}_mean_response_min": weighted_mean,
        f"{prefix}_p90_response_min": p90_time,
    }
    for threshold in MISSION_THRESHOLDS[mission]:
        covered = float(risk[times <= threshold].sum() / risk_total)
        metrics[f"{mission}_risk_coverage_within_{int(threshold)}min"] = covered
    return metrics


def network_metrics(assignments: pd.DataFrame) -> dict[str, float]:
    metrics: dict[str, float] = {}
    for mission in MISSION_THRESHOLDS:
        metrics.update(_mission_metrics(assignments, mission))
    return metrics
