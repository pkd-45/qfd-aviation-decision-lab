import json
from pathlib import Path

import pandas as pd

from qfd_aviation_lab.geojson import save_points_geojson


def test_point_geojson_is_valid_feature_collection(tmp_path: Path) -> None:
    frame = pd.DataFrame([{"site": "Example", "lat": -27.0, "lon": 153.0, "value": 1.0}])
    path = tmp_path / "points.geojson"
    save_points_geojson(frame, path, ["site", "value"])
    payload = json.loads(path.read_text())
    assert payload["type"] == "FeatureCollection"
    assert len(payload["features"]) == 1
    assert payload["features"][0]["geometry"]["type"] == "Point"
    assert payload["features"][0]["geometry"]["coordinates"] == [153.0, -27.0]
