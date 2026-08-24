from __future__ import annotations

import numpy as np

EARTH_RADIUS_KM = 6371.0088


def haversine_matrix(
    lat_a: np.ndarray,
    lon_a: np.ndarray,
    lat_b: np.ndarray,
    lon_b: np.ndarray,
) -> np.ndarray:
    """Pairwise great-circle distance matrix in kilometres."""
    lat1 = np.radians(np.asarray(lat_a, dtype=float))[:, None]
    lon1 = np.radians(np.asarray(lon_a, dtype=float))[:, None]
    lat2 = np.radians(np.asarray(lat_b, dtype=float))[None, :]
    lon2 = np.radians(np.asarray(lon_b, dtype=float))[None, :]

    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2.0) ** 2
    return 2.0 * EARTH_RADIUS_KM * np.arcsin(np.sqrt(a))
