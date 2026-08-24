from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


def _native(value: Any) -> Any:
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value


def _write_feature_collection(path: Path, features: list[dict[str, Any]]) -> None:
    payload = {"type": "FeatureCollection", "features": features}
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def save_points_geojson(
    frame: pd.DataFrame,
    path: Path,
    property_columns: list[str],
) -> None:
    features = []
    for _, row in frame.iterrows():
        properties = {column: _native(row[column]) for column in property_columns}
        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [float(row["lon"]), float(row["lat"])],
                },
                "properties": properties,
            }
        )
    _write_feature_collection(path, features)


def save_assignment_lines_geojson(
    assignments: pd.DataFrame,
    selected: pd.DataFrame,
    path: Path,
) -> None:
    lookup = selected.set_index(["site", "type_code"])
    features = []
    for _, row in assignments.iterrows():
        base = lookup.loc[(row["site"], row["type_code"])]
        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [float(row["lon"]), float(row["lat"])],
                        [float(base["lon"]), float(base["lat"])],
                    ],
                },
                "properties": {
                    "cell_id": int(row["cell_id"]),
                    "mission": str(row["mission"]),
                    "site": str(row["site"]),
                    "type_code": str(row["type_code"]),
                    "response_min": float(row["response_min"]),
                    "distance_km": float(row["distance_km"]),
                    "risk_weight": float(row["scenario_risk"]),
                },
            }
        )
    _write_feature_collection(path, features)
